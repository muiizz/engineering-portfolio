"""Run the support agent against a disposable PostgreSQL catalog."""
import argparse
import json
import os
import re
from pathlib import Path

from handoff import handle

# The catalog and this alias vector are synthetic. Supply only a vector obtained
# from a trusted embedding adapter when expanding the reference.
ALIASES = {"opening times": "[0,1,0,0]"}


def lookup(connection, message, embedding=None):
    words = re.findall(r"[^\W_]+", message)
    if words:
        query = " OR ".join(words)
        rows = connection.execute(
            """WITH q AS (SELECT websearch_to_tsquery('simple', %s) AS terms)
            SELECT slug, answer, ts_rank(s.terms,q.terms) AS rank
            FROM support_kb_lab s CROSS JOIN q WHERE s.terms @@ q.terms
            ORDER BY rank DESC, slug LIMIT 2""",
            (query,),
        ).fetchall()
        if rows:
            if len(rows) > 1 and rows[0][2] == rows[1][2]:
                return None
            return rows[0][:2]
    embedding = embedding or ALIASES.get(message)
    if embedding:
        rows = connection.execute(
            """SELECT slug, answer, embedding <=> %s::vector AS distance
            FROM support_kb_lab ORDER BY distance,slug LIMIT 2""", (embedding,)
        ).fetchall()
        if rows and rows[0][2] <= 0.20 and (len(rows) == 1 or rows[1][2] - rows[0][2] >= 0.10):
            return rows[0][:2]
    return None


def main():
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queue", type=Path)
    parser.add_argument("request_id")
    parser.add_argument("message")
    args = parser.parse_args()
    with psycopg.connect(os.environ["SUPPORT_DATABASE_URL"], autocommit=True) as connection:
        print(json.dumps(handle(args.queue, args.request_id, args.message,
                                lookup=lambda message: lookup(connection, message))))


if __name__ == "__main__":
    main()
