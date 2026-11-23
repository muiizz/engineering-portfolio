import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text())


def grade_answer(case_id: str, route: str, reply: str) -> bool:
    case = CASES[case_id]
    return route == case["route"] and case["phrase"].casefold() in reply.casefold()


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "answers.json"
    answers = json.loads(path.read_text())
    failures = []
    for case_id in CASES:
        answer = answers.get(case_id, {})
        if not grade_answer(case_id, answer.get("route", ""), answer.get("reply", "")):
            failures.append(case_id)
    print(f"{len(CASES) - len(failures)}/{len(CASES)} passed", *failures)
    sys.exit(bool(failures))
