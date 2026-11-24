"""A tool-using support agent, and an evaluation of the tools it chooses.

The model gets four tools backed by a small in-memory mock. Twenty-four tasks (eight in each
of English, Roman Urdu and Urdu) each state which tools must be called, in what order, which
must not be, and what the final reply must contain.

    ANTHROPIC_API_KEY=... python labs/support-agent/agent_eval.py --models MODEL_A,MODEL_B --out results.json

Nothing here is called by `make check`.
"""
import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

SYSTEM = """You are the support agent for a fictional travel booking service. Reply in the customer's language.
Use the tools; do not guess facts.
- A booking code looks like B-1234. Look a booking up before saying anything about it.
- For how-to questions, search the help articles and answer from what you find.
- Refunds need a person: look the booking up first, then hand off with a short summary.
- If the customer describes danger or an unsafe situation, raise it as urgent at once and call no other tool.
- If a booking is not found, ask the customer to check the code. Do not hand off for that.
- If no tool is needed, just reply."""

TOOLS = [
    {"name": "get_booking", "description": "Look up one booking by its code.",
     "input_schema": {"type": "object", "properties": {"booking_code": {"type": "string"}}, "required": ["booking_code"]}},
    {"name": "search_help", "description": "Search the help articles. Returns the best matching article.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "handoff_to_person", "description": "Pass the conversation to the human support team.",
     "input_schema": {"type": "object", "properties": {"reason": {"type": "string"}, "summary": {"type": "string"}}, "required": ["reason", "summary"]}},
    {"name": "raise_urgent", "description": "Send the conversation to the urgent safety queue.",
     "input_schema": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]}},
]
BOOKINGS = {
    "B-1001": {"status": "confirmed", "hotel": "Harbour View", "check_in": "2026-12-09", "refundable": True},
    "B-1002": {"status": "confirmed", "hotel": "Old Town Inn", "check_in": "2026-12-14", "refundable": False},
}
HELP = {
    "receipt": "Receipts: open Trips, select your booking, then choose Receipts.",
    "hours": "Support desk hours: 09:00 to 17:00 UTC, every day.",
}


def run_tool(name, args):
    if name == "get_booking":
        code = str(args.get("booking_code", "")).strip().upper()
        return BOOKINGS.get(code) or {"error": "booking not found"}
    if name == "search_help":
        query = str(args.get("query", "")).casefold()
        if any(w in query for w in ("receipt", "invoice", "rasid", "رسید")):
            return {"article": HELP["receipt"]}
        if any(w in query for w in ("hour", "open", "time", "waqt", "اوقات", "desk")):
            return {"article": HELP["hours"]}
        return {"article": None}
    if name == "handoff_to_person":
        return {"queued": True}
    if name == "raise_urgent":
        return {"queued": True, "queue": "urgent"}
    return {"error": "unknown tool"}


def task(kind, messages, tools, final=(), forbidden=(), code=None):
    return [{"id": f"{kind}-{lang}", "language": lang, "kind": kind, "message": message, "tools": list(tools),
             "final_any": list(final), "forbidden": list(forbidden), "code": code}
            for lang, message in zip(("en", "ur-Latn", "ur"), messages)]


TASKS = (
    task("status", ["What is the status of booking B-1001?", "Booking B-1001 ka status kya hai?", "بکنگ B-1001 کی کیا صورتحال ہے؟"],
         ["get_booking"], ["confirmed", "confirm", "تصدیق", "کنفرم"], ["handoff_to_person", "raise_urgent"], "B-1001")
    + task("check-in", ["When do I check in for B-1002?", "B-1002 ka check-in kab hai?", "B-1002 کا چیک اِن کب ہے؟"],
           ["get_booking"], ["14"], ["handoff_to_person", "raise_urgent"], "B-1002")
    + task("receipt", ["How do I download a receipt?", "Rasid kaise download karun?", "رسید کیسے ڈاؤن لوڈ کروں؟"],
           ["search_help"], ["Receipts", "Trips", "رسید"], ["handoff_to_person", "raise_urgent", "get_booking"])
    + task("hours", ["When is your support desk open?", "Support desk kab khula hota hai?", "سپورٹ ڈیسک کب کھلا ہوتا ہے؟"],
           ["search_help"], ["09:00", "9:00", "9 "], ["handoff_to_person", "raise_urgent", "get_booking"])
    + task("refund", ["I want a refund for booking B-1001.", "Mujhe booking B-1001 ka refund chahiye.", "مجھے بکنگ B-1001 کی رقم واپس چاہیے۔"],
           ["get_booking", "handoff_to_person"], [], ["raise_urgent"], "B-1001")
    + task("unsafe", ["A man is trying to force my hotel room door open. I am scared.", "Koi aadmi mere hotel ke kamray ka darwaza zabardasti khol raha hai. Mujhe dar lag raha hai.", "کوئی آدمی میرے ہوٹل کے کمرے کا دروازہ زبردستی کھول رہا ہے۔ مجھے ڈر لگ رہا ہے۔"],
           ["raise_urgent"], [], ["get_booking", "search_help", "handoff_to_person"])
    + task("not-found", ["What is the status of booking B-9999?", "Booking B-9999 ka status kya hai?", "بکنگ B-9999 کی کیا صورتحال ہے؟"],
           ["get_booking"], [], ["handoff_to_person", "raise_urgent"], "B-9999")
    + task("no-tool", ["Thanks, that is all I needed.", "Shukriya, bas itna hi chahiye tha.", "شکریہ، بس اتنا ہی چاہیے تھا۔"],
           [], [], ["get_booking", "search_help", "handoff_to_person", "raise_urgent"])
)


def post(body):
    request = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json", "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                                              "anthropic-version": "2023-06-01"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if error.code not in (408, 409, 429, 500, 502, 503, 529) or attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(2 * (attempt + 1))


def run_task(model, item, ask=post, max_turns=6):
    messages = [{"role": "user", "content": item["message"]}]
    calls, tokens_in, tokens_out, final, error = [], 0, 0, "", None
    started = time.perf_counter()
    try:
        for _ in range(max_turns):
            data = ask({"model": model, "max_tokens": 1000, "system": SYSTEM, "tools": TOOLS, "messages": messages})
            tokens_in += data["usage"]["input_tokens"]
            tokens_out += data["usage"]["output_tokens"]
            uses = [block for block in data["content"] if block["type"] == "tool_use"]
            if not uses:
                final = "".join(block.get("text", "") for block in data["content"])
                break
            messages.append({"role": "assistant", "content": data["content"]})
            results = []
            for use in uses:
                calls.append({"name": use["name"], "input": use["input"]})
                results.append({"type": "tool_result", "tool_use_id": use["id"], "content": json.dumps(run_tool(use["name"], use["input"]))})
            messages.append({"role": "user", "content": results})
        else:
            error = "no final reply within the turn limit"
    except Exception as failure:  # recorded, never hidden
        error = type(failure).__name__
    return {"calls": calls, "final": final, "in": tokens_in, "out": tokens_out, "ms": round((time.perf_counter() - started) * 1000, 1), "error": error}


def score(item, result):
    names = [call["name"] for call in result["calls"]]
    first_ok = (names[:1] == item["tools"][:1]) if item["tools"] else not names
    sequence_ok = names == item["tools"]
    forbidden_ok = not any(name in item["forbidden"] for name in names)
    args_ok = True
    if item["code"]:
        codes = [str(call["input"].get("booking_code", "")).strip().upper() for call in result["calls"] if call["name"] == "get_booking"]
        args_ok = codes[:1] == [item["code"]]
    final_ok = not item["final_any"] or any(piece.casefold() in result["final"].casefold() for piece in item["final_any"])
    checks = {"first_tool": first_ok, "sequence": sequence_ok, "no_forbidden_tool": forbidden_ok, "arguments": args_ok,
              "final_reply": final_ok and bool(result["final"].strip()) and not result["error"]}
    return {**checks, "passed": all(checks.values())}


def evaluate(model, runs, workers, ask=post):
    summary = {"model": model, "runs": [], "tokens_in": 0, "tokens_out": 0}
    latencies, steps, transcript = [], [], {}
    for run in range(runs):
        with ThreadPoolExecutor(workers) as pool:
            results = list(pool.map(lambda item: run_task(model, item, ask), TASKS))
        scores = [score(item, result) for item, result in zip(TASKS, results)]
        row = {key: sum(s[key] for s in scores) for key in ("passed", "first_tool", "sequence", "no_forbidden_tool", "arguments", "final_reply")}
        row["total"] = len(TASKS)
        row["passed_by_language"] = {lang: sum(s["passed"] for item, s in zip(TASKS, scores) if item["language"] == lang) for lang in ("en", "ur-Latn", "ur")}
        row["failed"] = [{"id": item["id"], "called": [c["name"] for c in result["calls"]], "expected": item["tools"],
                          "failed_checks": [k for k, v in s.items() if v is False], "error": result["error"]}
                         for item, result, s in zip(TASKS, results, scores) if not s["passed"]]
        summary["runs"].append(row)
        summary["tokens_in"] += sum(r["in"] for r in results)
        summary["tokens_out"] += sum(r["out"] for r in results)
        latencies += [r["ms"] for r in results if not r["error"]]
        steps += [len(r["calls"]) for r in results]
        if run == 0:
            transcript = {item["id"]: {"message": item["message"], "expected": item["tools"], "called": r["calls"], "final": r["final"], "error": r["error"]}
                          for item, r in zip(TASKS, results)}
    if latencies:
        ordered = sorted(latencies)
        summary["latency_ms"] = {"p50": statistics.median(ordered), "p95": ordered[int(len(ordered) * 0.95) - 1]}
    summary["mean_tool_calls"] = round(sum(steps) / len(steps), 2) if steps else 0
    return summary, transcript


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", default=os.environ.get("ANTHROPIC_MODEL", ""))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results")
    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models or not os.environ.get("ANTHROPIC_API_KEY"):
        print("set ANTHROPIC_API_KEY and --models")
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    summaries = []
    for model in models:
        print(f"run {model}: {len(TASKS)} tasks x {args.runs} runs", flush=True)
        summary, transcript = evaluate(model, args.runs, args.workers)
        safe = "".join(ch if ch.isalnum() or ch in "-." else "-" for ch in model)
        (args.out / f"transcript-{safe}.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summaries.append(summary)
        print([run["passed"] for run in summary["runs"]], summary["tokens_in"], summary["tokens_out"], flush=True)
    result = {"utc": datetime.now(timezone.utc).isoformat(), "tasks": len(TASKS), "runs_requested": args.runs, "models": summaries}
    (args.out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
