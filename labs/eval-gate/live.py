"""Run the evaluation gate against live models and record pass rates, tokens and latency.

Each provider is used only when its API key and a model ID are supplied:

    ANTHROPIC_API_KEY + ANTHROPIC_MODEL
    OPENAI_API_KEY    + OPENAI_MODEL
    GOOGLE_API_KEY    + GOOGLE_MODEL

A model variable may hold several IDs separated by commas.

    python labs/eval-gate/live.py --runs 3 --out labs/eval-gate/live-results

The script stops a model early if it exceeds --max-tokens, so a run has a known
upper cost. Nothing here is called by `make check`.
"""
import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hard_cases  # noqa: E402
from run import fixtures, grade, report  # noqa: E402

GRADE = grade

POLICY = """You answer messages for a fictional travel support desk. Messages arrive in English,
Roman Urdu or Urdu script. Choose exactly one route and write a short reply.

Routes:
- "urgent": the customer describes an unsafe or dangerous situation. The reply must say the
  message has gone to the urgent queue, using the words "urgent queue".
- "handoff": the customer wants a refund or anything a person must approve. The reply must say
  the "support team" will take it from here. Never promise a guaranteed refund.
- "reply": the question is answered by the facts below.

Facts:
- Desk hours are 09:00–17:00 UTC. Quote them exactly as written here.
- Receipts are downloaded under Trips > Receipts. Quote that path exactly.

Never ask a customer to share a password.
Return only a JSON object: {"route": "...", "reply": "..."}"""


ACTIVE_POLICY = [POLICY]


def post(url, headers, body, timeout=60):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def call_anthropic(model, message):
    data = post("https://api.anthropic.com/v1/messages",
                {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": MAX_OUTPUT, "system": ACTIVE_POLICY[0], "messages": [{"role": "user", "content": message}]})
    text = "".join(part.get("text", "") for part in data["content"])
    return text, data["usage"]["input_tokens"], data["usage"]["output_tokens"], data.get("stop_reason")


def call_openai(model, message):
    data = post("https://api.openai.com/v1/chat/completions",
                {"authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                {"model": model, "max_completion_tokens": MAX_OUTPUT,
                 "messages": [{"role": "system", "content": ACTIVE_POLICY[0]}, {"role": "user", "content": message}]})
    choice = data["choices"][0]
    return choice["message"]["content"] or "", data["usage"]["prompt_tokens"], data["usage"]["completion_tokens"], choice.get("finish_reason")


def call_google(model, message):
    data = post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"x-goog-api-key": os.environ["GOOGLE_API_KEY"]},
                {"systemInstruction": {"parts": [{"text": ACTIVE_POLICY[0]}]}, "contents": [{"role": "user", "parts": [{"text": message}]}],
                 "generationConfig": {"maxOutputTokens": MAX_OUTPUT}})
    candidate = data.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    usage = data.get("usageMetadata", {})
    return "".join(p.get("text", "") for p in parts), usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0), candidate.get("finishReason")


# Urdu script costs several tokens per word. The first live run used 200 and cut replies off
# mid-sentence, which the scorer then counted as failures; see the README.
MAX_OUTPUT = 1000
TRUNCATED = {"max_tokens", "length", "MAX_TOKENS"}

PROVIDERS = {"anthropic": ("ANTHROPIC", call_anthropic), "openai": ("OPENAI", call_openai), "google": ("GOOGLE", call_google)}


def parse(text):
    """Accept a bare JSON object or one wrapped in a code fence. Anything else is a failed answer."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        answer = json.loads(text[start:end + 1])
    except ValueError:
        return None
    return answer if isinstance(answer, dict) else None


def ask(call, model, case, retries=3):
    for attempt in range(retries):
        started = time.perf_counter()
        try:
            text, tokens_in, tokens_out, stop = call(model, case["message"])
            return {"answer": parse(text), "raw": text, "in": tokens_in, "out": tokens_out, "stop": stop,
                    "ms": round((time.perf_counter() - started) * 1000, 1), "error": None}
        except urllib.error.HTTPError as error:
            detail = f"HTTP {error.code}"
            if error.code not in (408, 409, 429, 500, 502, 503, 529):
                return {"answer": None, "raw": "", "in": 0, "out": 0, "stop": None, "ms": 0, "error": detail}
        except Exception as error:  # network errors and malformed responses
            detail = type(error).__name__
        time.sleep(2 * (attempt + 1))
    return {"answer": None, "raw": "", "in": 0, "out": 0, "stop": None, "ms": 0, "error": detail}


def evaluate(name, call, model, cases, runs, workers, max_tokens):
    summary = {"provider": name, "model": model, "runs": [], "tokens_in": 0, "tokens_out": 0, "stopped_early": False}
    latencies, first_answers = [], {}
    for run in range(runs):
        if summary["tokens_in"] + summary["tokens_out"] > max_tokens:
            summary["stopped_early"] = True
            break
        with ThreadPoolExecutor(workers) as pool:
            results = list(pool.map(lambda case: ask(call, model, case), cases))
        answers = {case["id"]: result["answer"] for case, result in zip(cases, results)}
        failed = [case for case in cases if not GRADE(case, answers[case["id"]])]
        if GRADE is grade:
            scored = report(cases, answers)
        else:
            passed = [case for case in cases if case not in failed]
            scored = {"passed": len(passed), "total": len(cases),
                      "passed_by_language": {lang: sum(c["language"] == lang for c in passed) for lang in ("en", "ur-Latn", "ur")},
                      "passed_by_kind": {kind: sum(c["difficulty"] == kind for c in passed) for kind in dict.fromkeys(c["difficulty"] for c in cases)},
                      "route_correct": sum(isinstance(answers[c["id"]], dict) and answers[c["id"]].get("route") == c["route"] for c in cases)}
        scored["failed_ids"] = [case["id"] for case in failed]
        scored["errors"] = sum(1 for result in results if result["error"])
        scored["unparseable"] = sum(1 for result in results if not result["error"] and result["answer"] is None)
        scored["truncated"] = sum(1 for result in results if result["stop"] in TRUNCATED)
        scored["empty"] = sum(1 for result in results if not result["error"] and not result["raw"].strip())
        summary["runs"].append(scored)
        summary["tokens_in"] += sum(result["in"] for result in results)
        summary["tokens_out"] += sum(result["out"] for result in results)
        latencies += [result["ms"] for result in results if not result["error"]]
        if run == 0:
            first_answers = {case["id"]: {"message": case["message"], "expected": case["route"], "raw": result["raw"], "stop": result["stop"], "error": result["error"]}
                             for case, result in zip(cases, results)}
    if latencies:
        ordered = sorted(latencies)
        summary["latency_ms"] = {"p50": statistics.median(ordered), "p95": ordered[int(len(ordered) * 0.95) - 1]}
    return summary, first_answers


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-tokens", type=int, default=400_000, help="stop a model after this many tokens in total")
    parser.add_argument("--limit", type=int, default=0, help="use only the first N cases (for a smoke run)")
    parser.add_argument("--set", choices=("base", "hard"), default="base", help="hard uses hard_cases.py and its scorer")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "live-results")
    args = parser.parse_args()
    global GRADE
    if args.set == "hard":
        GRADE = hard_cases.grade_v2
        ACTIVE_POLICY[0] = POLICY.replace("\nNever ask a customer", hard_cases.EXTRA_POLICY + "\n\nNever ask a customer")
    cases = list(hard_cases.fixtures() if args.set == "hard" else fixtures())[: args.limit or None]
    tag = "hard-" if args.set == "hard" else ""
    args.out.mkdir(parents=True, exist_ok=True)
    models = []
    for name, (prefix, call) in PROVIDERS.items():
        key = os.environ.get(prefix + "_API_KEY", "").strip()
        wanted = [m.strip() for m in os.environ.get(prefix + "_MODEL", "").split(",") if m.strip()]
        if not key or not wanted:
            print(f"skip {name}: set {prefix}_API_KEY and {prefix}_MODEL to include it")
            continue
        for model in wanted:
            print(f"run {name} {model}: {len(cases)} cases x {args.runs} runs", flush=True)
            summary, answers = evaluate(name, call, model, cases, args.runs, args.workers, args.max_tokens)
            safe = "".join(ch if ch.isalnum() or ch in "-." else "-" for ch in model)
            (args.out / f"{tag}answers-{safe}.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            models.append(summary)
            if any(run["errors"] for run in summary["runs"]):
                print("errors:", sorted({a["error"] for a in answers.values() if a["error"]}), flush=True)
            print(json.dumps({k: summary[k] for k in ("tokens_in", "tokens_out", "stopped_early")}),
                  [run["passed"] for run in summary["runs"]], flush=True)
    result = {"set": args.set, "utc": datetime.now(timezone.utc).isoformat(), "cases": len(cases), "runs_requested": args.runs, "models": models}
    (args.out / f"{tag}summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if models else 2


if __name__ == "__main__":
    raise SystemExit(main())
