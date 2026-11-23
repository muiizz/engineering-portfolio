"""Integration controls for the PostgreSQL support agent."""
import os
import tempfile
from pathlib import Path

import psycopg

from handoff import handle
from pg_agent import lookup

with tempfile.TemporaryDirectory() as directory, psycopg.connect(
    os.environ["SUPPORT_DATABASE_URL"], autocommit=True
) as connection:
    queue = Path(directory) / "handoffs.db"

    def decision(key, message):
        return handle(queue, key, message, lookup=lambda text: lookup(connection, text))

    assert decision("keyword", "Where is my invoice?")["citation"] == "receipts"
    assert decision("vector", "opening times")["citation"] == "hours"
    assert decision("unknown", "pets")["status"] == "pending"
    assert decision("unknown", "pets")["request_id"] == "unknown"
    assert decision("urgent", "unsafe situation and invoice")["route"] == "urgent"
    assert decision("ambiguous", "invoice ticket")["route"] == "handoff"
    assert lookup(connection, "unmatched", "[0.5,0.5,0.5,0.5]") is None
print("Verified keyword and vector citations, low confidence, ambiguity, urgent precedence and durable handoff.")
