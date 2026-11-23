import unittest

from compare import compare
from run import fixtures, grade


class GateTests(unittest.TestCase):
    def setUp(self):
        self.cases = list(fixtures())
        self.answers = {c["id"]: {"route": c["route"], "reply": c["required"]} for c in self.cases}

    def test_fixture_ids_are_unique_and_balanced(self):
        self.assertEqual(len(self.answers), 120)
        for language in ("en", "ur-Latn", "ur"):
            self.assertEqual(sum(c["language"] == language for c in self.cases), 40)

    def test_forbidden_phrase_overrides_required_text(self):
        case = self.cases[0]
        self.assertFalse(grade(case, {"route": case["route"], "reply": "support team: guaranteed refund"}))

    def test_detects_and_locates_regression(self):
        changed = dict(self.answers)
        changed.pop("safety-2-0")
        result = compare(self.answers, changed)
        self.assertEqual(result["regressions"], ["safety-2-0"])
        self.assertEqual(result["candidate"]["urgent_passed"], 29)
        self.assertEqual(result["candidate"]["passed_by_language"]["ur"], 39)

    def test_finds_gains_without_counting_unchanged_answers(self):
        result = compare({}, self.answers)
        self.assertEqual(len(result["gains"]), 120)
        self.assertEqual(result["regressions"], [])
