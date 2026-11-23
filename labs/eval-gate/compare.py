"""Compare two saved candidate runs on the same evaluation cases."""
import argparse
import json
from pathlib import Path

from run import fixtures, grade, report


def load_answers(path):
    with path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected answers keyed by case ID")
    return data


def compare(baseline, candidate):
    cases = list(fixtures())
    before, after = report(cases, baseline), report(cases, candidate)
    gains, regressions, failures = [], [], []
    for case in cases:
        key = case["id"]
        old, new = grade(case, baseline.get(key)), grade(case, candidate.get(key))
        if new and not old:
            gains.append(key)
        if old and not new:
            regressions.append(key)
        if not new:
            failures.append(key)
    return {"baseline": before, "candidate": after, "gains": gains,
            "regressions": regressions, "candidate_failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        result = compare(load_answers(args.baseline), load_answers(args.candidate))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    candidate = result["candidate"]
    return int(candidate["urgent_passed"] < candidate["urgent_total"] or bool(result["regressions"]))


if __name__ == "__main__":
    raise SystemExit(main())
