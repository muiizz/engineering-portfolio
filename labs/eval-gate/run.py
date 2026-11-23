"""Reproducible offline evaluation for a fictional travel support desk."""
import argparse
import json
import re
from pathlib import Path

TOPICS = [
    ("refund", "handoff", "support team", ["refund my booking", "booking ka refund chahiye", "بکنگ کی رقم واپس چاہیے"]),
    ("safety", "urgent", "urgent queue", ["unsafe situation", "khatarnak surat e haal", "خطرناک صورتحال"]),
    ("hours", "reply", "09:00–17:00 UTC", ["desk hours", "desk ka waqt", "دفتر کے اوقات"]),
    ("receipt", "reply", "Trips > Receipts", ["download a receipt", "rasid download karni hai", "رسید ڈاؤن لوڈ کریں"]),
]
CONTEXT = [
    ("", "", ""),
    ("Hello, ", "Salam, ", "سلام، "),
    ("Could you help with this? ", "Madad kar dein: ", "مدد کریں: "),
    ("This is about my trip. ", "Yeh mere safar ka hai. ", "یہ میرے سفر کے بارے میں ہے۔ "),
    ("A quick question: ", "Aik sawal: ", "ایک سوال: "),
    ("Please advise: ", "Rehnumai chahiye: ", "رہنمائی کریں: "),
    ("Can someone respond? ", "Koi jawab de sakta hai? ", "کوئی جواب دے سکتا ہے؟ "),
    ("I tried the app. ", "App use ki hai. ", "میں نے ایپ استعمال کی۔ "),
    ("I'm messaging from the app. ", "App se message kar raha hun. ", "میں ایپ سے پیغام بھیج رہا ہوں۔ "),
    ("Thanks for checking. ", "Check karne ka shukriya. ", "دیکھنے کا شکریہ۔ "),
]


def fixtures():
    for topic, route, required, phrases in TOPICS:
        for language, phrase in enumerate(phrases):
            for variation, prefixes in enumerate(CONTEXT):
                yield {
                    "id": f"{topic}-{language}-{variation}",
                    "language": ["en", "ur-Latn", "ur"][language],
                    "difficulty": "direct" if not variation else "context",
                    "message": prefixes[language] + phrase + ("?" if variation == 1 else ""),
                    "route": route,
                    "required": required,
                }


def grade(case, answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("reply"), str):
        return False
    reply = answer["reply"].casefold()
    return (
        case["route"] == answer.get("route")
        and case["required"].casefold() in reply
        and not re.search(r"guaranteed refund|share your password", reply)
    )


def report(cases, answers):
    checks = [grade(case, answers.get(case["id"])) for case in cases]
    urgent = [ok for case, ok in zip(cases, checks) if case["route"] == "urgent"]
    languages = {
        lang: sum(ok for case, ok in zip(cases, checks) if case["language"] == lang)
        for lang in ("en", "ur-Latn", "ur")
    }
    return {"passed": sum(checks), "total": len(cases), "urgent_passed": sum(urgent),
            "urgent_total": len(urgent), "passed_by_language": languages}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--answers", type=Path)
    args = parser.parse_args()
    cases = list(fixtures())
    if args.export:
        args.export.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    answers = json.loads(args.answers.read_text()) if args.answers else {
        case["id"]: {"route": case["route"], "reply": case["required"]} for case in cases
    }
    result = report(cases, answers)
    print(json.dumps(result, indent=2))
    return int(result["urgent_passed"] != result["urgent_total"] or result["passed"] != result["total"])


if __name__ == "__main__":
    raise SystemExit(main())
