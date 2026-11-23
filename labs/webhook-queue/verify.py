"""Exercise queue behavior against a disposable database with schema.sql applied."""
import hashlib
import hmac
import os
import time
from concurrent.futures import ThreadPoolExecutor

import psycopg
from psycopg.types.json import Jsonb

from queue_core import deliver_once, enqueue, work_once

DSN = os.environ["WEBHOOK_DATABASE_URL"]


def connect():
    return psycopg.connect(DSN, autocommit=True)


def signed_enqueue(connection, event_id):
    body = ('{"id":"%s"}' % event_id).encode()
    timestamp = str(int(time.time()))
    key = b"synthetic-test"
    signature = hmac.new(key, timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return enqueue(connection, body, timestamp, signature, key)


def send(event_id, payload):
    with connect() as inbox:
        inbox.execute(
            "INSERT INTO demo_provider_inbox VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (event_id, Jsonb(payload)),
        )


def crash_after_send(event_id, payload):
    send(event_id, payload)
    raise RuntimeError("synthetic worker interruption")


def consume():
    count = 0
    with connect() as connection:
        while work_once(connection, lambda event: event):
            count += 1
    return count


with connect() as connection:
    assert signed_enqueue(connection, "first")
    assert not signed_enqueue(connection, "first")
    assert work_once(connection, lambda event: event)
    try:
        deliver_once(connection, crash_after_send)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected synthetic interruption")
    assert deliver_once(connection, send)
    assert not deliver_once(connection, send)
    assert connection.execute("SELECT count(*) FROM demo_provider_inbox").fetchone() == (1,)

    for number in range(100):
        assert signed_enqueue(connection, f"parallel-{number}")
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(lambda _: consume(), range(8))) == 100
    assert connection.execute("SELECT count(*) FROM webhook_outbox").fetchone() == (101,)

    assert signed_enqueue(connection, "bad")
    for _ in range(5):
        assert work_once(connection, lambda _: {object()})
        connection.execute("UPDATE webhook_jobs SET available_at=now() WHERE event_id='bad'")
    assert not work_once(connection, lambda event: event)
    assert connection.execute("SELECT count(*) FROM webhook_dead_letters").fetchone() == (1,)
print("Passed: replay, interrupted delivery, 8-worker claims, and dead lettering")
