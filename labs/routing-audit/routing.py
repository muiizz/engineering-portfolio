"""Deterministic routing for a fictional customer-support queue."""

from dataclasses import dataclass
import re
import unicodedata

BASELINE_SIGNALS = ("account hacked", "unauthorized charge", "charged twice")
REVISED_SIGNALS = BASELINE_SIGNALS + (
    "account hack ho gaya",
    "do baar paisay kat gaye",
    "meri ijazat ke baghair payment",
    "اکاؤنٹ ہیک",
    "دو بار پیسے کٹ گئے",
    "بلا اجازت ادائیگی",
)
BASELINE_RULE = re.compile(r"\b(?:" + "|".join(map(re.escape, BASELINE_SIGNALS)) + r")\b")
REVISED_RULE = re.compile(r"\b(?:" + "|".join(map(re.escape, REVISED_SIGNALS)) + r")\b")
URDU_VARIANTS = str.maketrans({"ي": "ی", "ك": "ک", "ـ": "", "\u200c": "", "\u200d": ""})


def normalize(message: str) -> str:
    text = unicodedata.normalize("NFKC", message).casefold().translate(URDU_VARIANTS)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(re.findall(r"[^\W_]+", text))


@dataclass(frozen=True)
class Decision:
    queue: str
    share_transcript: bool


def route(message: str, *, consent: object = None, revised: bool = True) -> Decision:
    """Select an internal queue and decide whether a handoff may include text."""
    if revised:
        matched = REVISED_RULE.search(normalize(message))
    else:
        matched = BASELINE_RULE.search(message.casefold())
    queue = "review" if matched else "routine"
    return Decision(queue, queue == "review" and consent is True)
