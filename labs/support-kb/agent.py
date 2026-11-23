"""Offline, citation-backed support demo for a fictional booking service."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    slug: str
    terms: frozenset[str]
    answer: str


ARTICLES = (
    Article("receipts", frozenset(("receipt", "invoice", "rasid", "رسید")),
            "Open Trips, select your booking, then choose Receipts."),
    Article("hours", frozenset(("hours", "schedule", "waqt", "اوقات")),
            "The support desk is open from 09:00 to 17:00 UTC."),
    Article("itinerary", frozenset(("itinerary", "confirmation", "ticket", "ٹکٹ")),
            "Open Trips and choose your booking to view its itinerary."),
)
HANDOFF = re.compile(r"\b(refund|complaint|lawyer|human|agent|refund chahiye)\b|شکایت|رقم واپس")
URGENT = re.compile(r"\b(unsafe|immediate danger|emergency|khatarnak)\b|خطرناک|ہنگامی")


def keyword_lookup(message):
    words = set(re.findall(r"[^\W_]+", message))
    ranked = sorted(ARTICLES, key=lambda article: len(words & article.terms), reverse=True)
    best, runner_up = ranked[:2]
    if len(words & best.terms) > len(words & runner_up.terms):
        return best.slug, best.answer
    return None


def respond(message: str, lookup=keyword_lookup) -> dict:
    normalized = message.casefold()
    if URGENT.search(normalized):
        return {"route": "urgent", "reason": "safety signal"}
    if HANDOFF.search(normalized):
        return {"route": "handoff", "reason": "human review requested or required"}
    matches = lookup(normalized)
    if matches is None:
        return {"route": "handoff", "reason": "insufficient evidence for one answer"}
    citation, answer = matches
    return {"route": "reply", "reply": answer, "citation": citation}


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message")
    print(json.dumps(respond(parser.parse_args().message), ensure_ascii=False))
