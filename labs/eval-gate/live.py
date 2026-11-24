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
from run import fixtures, grade, report  # noqa: E402

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


def post(url, headers, body, timeout=60):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def call_anthropic(model, message):
    data = post("https://api.anthropic.com/v1/messages",
                {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": 200, "system": POLICY, "messages": [{"role": "user", "content": message}]})
    text = "".join(part.get("text", "") for part in data["content"])
    return text, data["usage"]["input_tokens"], data["usage"]["output_tokens"]


def call_openai(model, message):
    data = post("https://api.openai.com/v1/chat/completions",
                {"authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                {"model": model, "max_completion_tokens": 400,
                 "messages": [{"role": "system", "content": POLICY}, {"role": "user", "content": message}]})
    return data["choices"][0]["message"]["content"] or "", data["usage"]["prompt_tokens"], data["usage"]["completion_tokens"]


def call_google(model, message):
    data = post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"x-goog-api-key": os.environ["GOOGLE_API_KEY"]},
                {"systemInstruction": {"parts": [{"text": POLICY}]}, "contents": [{"role": "user", "parts": [{"text": message}]}],
                 "generationConfig": {"maxOutputTokens": 400}})
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    usage = data.get("usageMetadata", {})
    return "".join(p.get("text", "") for p in parts), usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


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
            text, tokens_in, tokens_out = call(model, case["message"])
            return {"answer": parse(text), "raw": text, "in": tokens_in, "out": tokens_out,
                    "ms": round((time.perf_counter() - started) * 1000, 1), "error": None}
        except urllib.error.HTTPError as error:
            detail = f"HTTP {error.code}"
            if error.code not in (408, 409, 429, 500, 502, 503, 529):
                return {"answer": None, "raw": "", "in": 0, "out": 0, "ms": 0, "error": detail}
        except Exception as error:  # network errors and malformed responses
            detail = type(error).__name__
        time.sleep(2 * (attempt + 1))
    return {"answer": None, "raw": "", "in": 0, "out": 0, "ms": 0, "error": detail}


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
        scored = report(cases, answers)
        scored["failed_ids"] = [case["id"] for case in cases if not grade(case, answers[case["id"]])]
        scored["errors"] = sum(1 for result in results if result["error"])
        scored["unparseable"] = sum(1 for result in results if not result["error"] and result["answer"] is None)
        summary["runs"].append(scored)
        summary["tokens_in"] += sum(result["in"] for result in results)
        summary["tokens_out"] += sum(result["out"] for result in results)
        latencies += [result["ms"] for result in results if not result["error"]]
        if run == 0:
            first_answers = {case["id"]: {"message": case["message"], "expected": case["route"], "raw": result["raw"], "error": result["error"]}
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
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "live-results")
    args = parser.parse_args()
    cases = list(fixtures())[: args.limit or None]
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
            (args.out / f"answers-{safe}.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            models.append(summary)
            print(json.dumps({k: summary[k] for k in ("tokens_in", "tokens_out", "stopped_early")}),
                  [run["passed"] for run in summary["runs"]], flush=True)
    result = {"utc": datetime.now(timezone.utc).isoformat(), "cases": len(cases), "runs_requested": args.runs, "models": models}
    (args.out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if models else 2


if __name__ == "__main__":
    raise SystemExit(main())
