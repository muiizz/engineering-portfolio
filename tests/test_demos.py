import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))
from eval import CASES, grade_answer
from quality_gate import check_release


class QualityGateTests(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(check_release({"tests": "pass", "lint": "pass", "security": "pass"}), [])

    def test_failed_check(self):
        self.assertEqual(check_release({"tests": "fail", "lint": "pass", "security": "pass"}), ["tests: fail"])

    def test_missing_check(self):
        self.assertEqual(check_release({"tests": "pass", "lint": "pass"}), ["security: missing"])


class SupportEvaluationTests(unittest.TestCase):
    def test_correct_answers(self):
        for case_id, case in CASES.items():
            with self.subTest(case=case_id):
                self.assertTrue(grade_answer(case_id, case["route"], case["phrase"]))

    def test_route_and_phrase_are_both_required(self):
        self.assertFalse(grade_answer("refund", "reply", "support team"))
        self.assertFalse(grade_answer("refund", "handoff", "Someone will help."))

    def test_phrase_is_case_insensitive(self):
        self.assertTrue(grade_answer("refund", "handoff", "SUPPORT TEAM"))


if __name__ == "__main__":
    unittest.main()
