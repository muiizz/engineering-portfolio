"""Signed intake and transactional queue operations for a synthetic provider."""
import hashlib
import hmac
import json
import time


def enqueue(connection, body: bytes, timestamp: str, signature: str, secret: bytes):
    if not secret or not timestamp.isascii() or not timestamp.isdecimal() or len(timestamp) > 12:
        raise ValueError("invalid signing configuration or timestamp")
    if abs(time.time() - int(timestamp)) > 300:
        raise ValueError("timestamp outside tolerance")
    digest = hmac.new(secret, timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest.encode(), signature.encode()):
        raise ValueError("invalid signature")
    event = json.loads(body)
    if not isinstance(event, dict) or not isinstance(event.get("id"), str) or not event["id"]:
        raise ValueError("event ID required")
    with connection.transaction():
        row = connection.execute(
            "INSERT INTO webhook_jobs (event_id,payload) VALUES (%s,%s::jsonb) "
            "ON CONFLICT (event_id) DO NOTHING RETURNING event_id",
            (event["id"], body.decode()),
        ).fetchone()
    return row is not None


def work_once(connection, transform):
    """Run a pure payload transformation while holding the queue row lock."""
    with connection.transaction():
        job = connection.execute(
            "SELECT event_id,payload,attempts FROM webhook_jobs "
            "WHERE finished_at IS NULL AND attempts < 5 AND available_at <= now() "
            "ORDER BY available_at,event_id LIMIT 1 FOR UPDATE SKIP LOCKED"
        ).fetchone()
        if job is None:
            return False
        event_id, payload, attempts = job
        try:
            outgoing = json.dumps(transform(payload))
        except (ValueError, TypeError):
            attempt = attempts + 1
            connection.execute(
                "UPDATE webhook_jobs SET attempts=%s, "
                "available_at=now() + %s * interval '1 second' WHERE event_id=%s",
                (attempt, 2 ** attempt, event_id),
            )
            if attempt == 5:
                connection.execute(
                    "INSERT INTO webhook_dead_letters VALUES (%s,%s)",
                    (event_id, "payload transformation failed"),
                )
        else:
            connection.execute(
                "INSERT INTO webhook_outbox (event_id,payload) VALUES (%s,%s::jsonb)",
                (event_id, outgoing),
            )
            connection.execute(
                "UPDATE webhook_jobs SET finished_at=now() WHERE event_id=%s", (event_id,)
            )
    return True


def deliver_once(connection, send):
    """Send one outbox event using the event ID as a provider idempotency key."""
    with connection.transaction():
        row = connection.execute(
            "SELECT event_id,payload FROM webhook_outbox WHERE sent_at IS NULL "
            "ORDER BY event_id LIMIT 1 FOR UPDATE SKIP LOCKED"
        ).fetchone()
        if row is None:
            return False
        event_id, payload = row
        send(event_id, payload)
        connection.execute(
            "UPDATE webhook_outbox SET sent_at=now() WHERE event_id=%s", (event_id,)
        )
    return True
