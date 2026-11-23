"""Evaluate both routing policies against labelled synthetic examples."""

from collections import Counter
from itertools import groupby
import json
from pathlib import Path

from routing import route

COUNTS = {
    ("review", "review"): "TP",
    ("routine", "review"): "FP",
    ("routine", "routine"): "TN",
    ("review", "routine"): "FN",
}


def load_fixtures():
    return json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


def evaluate(fixtures, *, revised):
    counts = Counter()
    errors = []
    for fixture in fixtures:
        predicted = route(fixture["message"], revised=revised).queue
        result = COUNTS[fixture["expected"], predicted]
        counts[result] += 1
        if result in {"FP", "FN"}:
            errors.append((fixture["id"], result))
    return counts, errors


def main():
    fixtures = load_fixtures()
    groups = {"All": fixtures}
    groups.update(
        (language, list(rows))
        for language, rows in groupby(sorted(fixtures, key=lambda row: row["language"]), key=lambda row: row["language"])
    )
    print(f"{'Group':<13} {'Policy':<9} {'TP':>3} {'FP':>3} {'TN':>3} {'FN':>3}")
    for language, rows in groups.items():
        for policy in ("baseline", "revised"):
            counts, _ = evaluate(rows, revised=policy == "revised")
            print(f"{language:<13} {policy:<9} " + " ".join(f"{counts[key]:>3}" for key in ("TP", "FP", "TN", "FN")))
    for policy in ("baseline", "revised"):
        _, errors = evaluate(fixtures, revised=policy == "revised")
        print(f"{policy} errors: " + ", ".join(f"{case} ({kind})" for case, kind in errors))


if __name__ == "__main__":
    main()
