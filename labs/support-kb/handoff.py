"""Local durable queue for the synthetic support demo."""
import argparse
import json
import sqlite3
from pathlib import Path

from agent import keyword_lookup, respond


def handle(database: Path, request_id: str, message: str, lookup=keyword_lookup) -> dict:
    decision = respond(message, lookup=lookup)
    if decision["route"] == "reply":
        return decision

    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS handoffs ("
            "request_id TEXT PRIMARY KEY, route TEXT NOT NULL, reason TEXT NOT NULL, "
            "status TEXT NOT NULL DEFAULT 'pending')"
        )
        connection.execute(
            "INSERT INTO handoffs (request_id, route, reason) VALUES (?, ?, ?) "
            "ON CONFLICT (request_id) DO NOTHING",
            (request_id, decision["route"], decision["reason"]),
        )
        route, reason, status = connection.execute(
            "SELECT route, reason, status FROM handoffs WHERE request_id = ?", (request_id,)
        ).fetchone()
    return {"request_id": request_id, "route": route, "reason": reason, "status": status}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("request_id")
    parser.add_argument("message")
    args = parser.parse_args()
    print(json.dumps(handle(args.database, args.request_id, args.message)))
