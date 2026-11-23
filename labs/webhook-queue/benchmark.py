"""Measure queued processing and outbox delivery on a disposable database."""
import argparse
import json
import math
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import psycopg
from psycopg.types.json import Jsonb

from queue_core import deliver_once, work_once


def measure(dsn, workers, count):
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("TRUNCATE webhook_outbox, webhook_dead_letters, webhook_jobs, demo_provider_inbox")
        db.execute(
            "INSERT INTO webhook_jobs (event_id,payload) "
            "SELECT i::text,jsonb_build_object('id',i::text) FROM generate_series(1,%s) AS i",
            (count,),
        )
        db.execute("UPDATE webhook_jobs SET available_at=clock_timestamp()")

    def worker():
        with psycopg.connect(dsn, autocommit=True) as queue, psycopg.connect(dsn, autocommit=True) as inbox:
            def send(event_id, payload):
                inbox.execute("INSERT INTO demo_provider_inbox VALUES (%s,%s) ON CONFLICT DO NOTHING",
                              (event_id, Jsonb(payload)))
            while True:
                worked = work_once(queue, lambda event: event)
                delivered = deliver_once(queue, send)
                if not worked and not delivered:
                    return

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for task in [pool.submit(worker) for _ in range(workers)]:
            task.result()
    seconds = time.perf_counter() - start
    with psycopg.connect(dsn) as db:
        rows = db.execute(
            "SELECT extract(epoch FROM (o.sent_at-j.available_at))*1000 "
            "FROM webhook_outbox o JOIN webhook_jobs j USING (event_id) "
            "WHERE o.sent_at IS NOT NULL ORDER BY 1"
        ).fetchall()
        inbox_count = db.execute("SELECT count(*) FROM demo_provider_inbox").fetchone()[0]
    if len(rows) != count or inbox_count != count:
        raise RuntimeError("incomplete delivery")
    return {"workers": workers, "delivered": count, "seconds": round(seconds, 3),
            "events_per_second": round(count / seconds, 1),
            "p95_queued_to_delivered_ms": round(float(rows[math.ceil(count * 0.95) - 1][0]), 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-database", action="store_true", required=True)
    parser.parse_args()
    dsn = os.environ["WEBHOOK_DATABASE_URL"]
    with psycopg.connect(dsn) as db:
        version = db.execute("SHOW server_version").fetchone()[0]
    print(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
                      "postgres": version, "samples": [measure(dsn, n, 1000) for n in (1, 4, 8)]}, indent=2))


if __name__ == "__main__":
    main()
