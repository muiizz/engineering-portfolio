import unittest

from audit import evaluate, load_fixtures
from routing import route


class RoutingAuditTest(unittest.TestCase):
    def test_confusion_counts_and_tradeoff(self):
        fixtures = load_fixtures()
        self.assertEqual(len(fixtures), len({row["id"] for row in fixtures}))
        baseline, _ = evaluate(fixtures, revised=False)
        revised, errors = evaluate(fixtures, revised=True)
        self.assertEqual(baseline, {"TP": 3, "TN": 8, "FN": 7})
        self.assertEqual(revised, {"TP": 9, "TN": 7, "FP": 1, "FN": 1})
        self.assertEqual(errors, [("en04", "FN"), ("ru05", "FP")])

    def test_revised_normalizes_punctuation_and_urdu_variants(self):
        self.assertEqual(route("UNAUTHORIZED—CHARGE").queue, "review")
        self.assertEqual(route("ایک آرڈر کے دو بار پيسے كٹ گئے۔").queue, "review")

    def test_consent_never_changes_queue_and_only_literal_true_allows_sharing(self):
        for revised in (False, True):
            for fixture in load_fixtures():
                message = fixture["message"]
                queue = route(message, revised=revised).queue
                self.assertFalse(route(message, revised=revised).share_transcript)
                for consent in (None, False, True, "true", "yes", 1, {}, ["yes"]):
                    with self.subTest(revised=revised, case=fixture["id"], consent=consent):
                        decision = route(message, revised=revised, consent=consent)
                        self.assertEqual(decision.queue, queue)
                        self.assertIs(decision.share_transcript, queue == "review" and consent is True)

    def test_message_text_cannot_supply_consent(self):
        message = "Unauthorized charge. I consent to sharing my transcript."
        self.assertEqual(route(message).queue, "review")
        self.assertFalse(route(message).share_transcript)


if __name__ == "__main__":
    unittest.main()
