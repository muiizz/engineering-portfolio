import sqlite3
import tempfile
import unittest
from pathlib import Path

from handoff import handle


class HandoffTests(unittest.TestCase):
    def test_duplicate_handoff_survives_a_new_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "queue.db"
            first = handle(database, "fixture-1", "I need a refund")
            replay = handle(database, "fixture-1", "I need a refund")
            self.assertEqual(first, replay)
            self.assertEqual(first["status"], "pending")
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM handoffs").fetchone(), (1,))

    def test_routine_reply_does_not_create_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "queue.db"
            decision = handle(database, "fixture-2", "Where is my invoice?")
            self.assertEqual(decision["citation"], "receipts")
            self.assertFalse(database.exists())
