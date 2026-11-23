"""Process jobs and deliver to a durable, idempotent synthetic inbox."""
import os
import time

from queue_core import deliver_once, work_once


def main():
    import psycopg
    from psycopg.types.json import Jsonb

    dsn = os.environ["WEBHOOK_DATABASE_URL"]

    def send(event_id, payload):
        with psycopg.connect(dsn, autocommit=True) as inbox:
            inbox.execute(
                "INSERT INTO demo_provider_inbox VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (event_id, Jsonb(payload)),
            )

    with psycopg.connect(dsn, autocommit=True) as connection:
        while True:
            worked = work_once(connection, lambda event: {"received": event["id"]})
            delivered = deliver_once(connection, send)
            if not worked and not delivered:
                time.sleep(0.25)


if __name__ == "__main__":
    main()
