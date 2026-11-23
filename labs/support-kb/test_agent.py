import unittest

from agent import respond


class SupportTests(unittest.TestCase):
    def test_citations(self):
        for message, citation in [
            ("Where is my invoice?", "receipts"),
            ("desk ka waqt kya hai", "hours"),
            ("میرا ٹکٹ", "itinerary"),
        ]:
            with self.subTest(message=message):
                self.assertEqual(respond(message)["citation"], citation)

    def test_handoff_wins_over_article_match(self):
        self.assertEqual(respond("I need a refund and an invoice")["route"], "handoff")

    def test_urgent_wins_over_handoff(self):
        self.assertEqual(respond("This is unsafe and I need a human")["route"], "urgent")

    def test_unknown_and_ambiguous_messages(self):
        for message in ("Can I bring a pet?", "receipt or itinerary"):
            with self.subTest(message=message):
                decision = respond(message)
                self.assertEqual(decision["route"], "handoff")
                self.assertNotIn("citation", decision)
