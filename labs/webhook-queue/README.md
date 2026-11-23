# PostgreSQL webhook queue

Apply schema.sql to a disposable PostgreSQL database. The Python module accepts
an autocommit psycopg 3 connection. Intake authenticates the timestamp and raw
body before inserting a job. A unique event ID makes replay a no-op.

The worker locks one available row and skips rows held by other workers.
Its callback must perform a pure transformation. The outbox insert and job
completion commit together. A database rollback releases an interrupted claim.
Invalid payloads back off and reach the dead-letter table after five failures.


## Run locally

Install requirements.txt and apply schema.sql to an empty PostgreSQL database.
Set WEBHOOK_DATABASE_URL and WEBHOOK_SIGNING_SECRET in your shell. Run
`python receiver.py` and `python worker.py` in separate terminals with the
same database URL.

POST a JSON object with a nonempty string id to http://127.0.0.1:8080/webhook.
Set X-Webhook-Timestamp to Unix seconds and X-Webhook-Signature to the hex
HMAC-SHA256 of the ASCII timestamp, a period, and the exact body bytes.
The receiver returns 202 after the transaction commits, including for duplicates.

The worker delivers to demo_provider_inbox. A separate database transaction
simulates a provider accepting delivery before the local outbox is marked sent.
The inbox uses event_id as its idempotency key, so retrying with that key after
an interruption does not insert a second inbox row.

## Verified on 24 November 2026

Against PostgreSQL 16.2 with UTF-8 encoding, `python verify.py` passed replay
deduplication, recovery from an interruption after the synthetic provider
accepted delivery, concurrent claims over 100 events with eight workers, and
dead lettering after five failed attempts. Run this script on a fresh disposable
database with schema.sql applied.

## Measured throughput

Run `python benchmark.py --disposable-database` on a disposable database.
It truncates the demo tables, seeds 1,000 events per worker configuration and
measures queued-to-delivered p95 against the local synthetic provider. See
[raw timings](benchmark-results.json). One worker achieved 1,233 events/s
with a p95 of 763.53 ms. Four and eight workers were slower in this single run.
These results exclude HTTP ingress and external network latency.
