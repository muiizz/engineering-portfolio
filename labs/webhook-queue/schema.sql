CREATE TABLE webhook_jobs (
    event_id text PRIMARY KEY,
    payload jsonb NOT NULL,
    available_at timestamptz NOT NULL DEFAULT now(),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 5),
    finished_at timestamptz
);

CREATE INDEX webhook_jobs_ready
ON webhook_jobs (available_at, event_id)
WHERE finished_at IS NULL AND attempts < 5;

CREATE TABLE webhook_outbox (
    event_id text PRIMARY KEY REFERENCES webhook_jobs(event_id),
    payload jsonb NOT NULL,
    sent_at timestamptz
);

CREATE TABLE webhook_dead_letters (
    event_id text PRIMARY KEY REFERENCES webhook_jobs(event_id),
    reason text NOT NULL
);

CREATE TABLE demo_provider_inbox (
    event_id text PRIMARY KEY,
    payload jsonb NOT NULL
);
