# Citation-backed support routing

A fictional booking service answers three documented questions and cites the matching article. Explicit safety signals take priority over requests for human review. Unmatched and tied queries go to handoff.

Run from the repository root:

    python labs/support-kb/agent.py "Where is my invoice?"
    python -m unittest discover -s labs/support-kb -v

The demo uses an in-memory keyword index and deterministic responses. The tests cover three languages, priority, and fallback. The PostgreSQL retrieval lab below tests retrieval independently of the Python agent.

## Durable handoff demo

Run `python labs/support-kb/handoff.py /tmp/support-demo.db example-1 "I need a refund"`.
The queue stores request ID, route, reason and pending status in SQLite.
Repeating the same handoff request ID returns the existing row. Routine
knowledge-base replies do not enter the queue. The queued record carries no
message transcript. Run `python -m unittest discover -s labs/support-kb -v`
to verify queue persistence and the routing rules.

## PostgreSQL retrieval fixture

Run `psql -X -v ON_ERROR_STOP=1 -f labs/support-kb/hybrid.sql` against a
disposable PostgreSQL database with pgvector available. The transaction
rolls back the fixtures and indexes. The SQL compares top-1 keyword matches,
cosine distance, and keyword-first hybrid fallback. Its expected scores are
5/6 keyword, 5/6 vector, and 6/6 hybrid.

The four-dimensional vectors are controlled fixtures. One case deliberately
has a poor semantic match and another has no keyword match. This tests the
retrieval and scoring mechanics. It does not measure a learned embedding
model or HNSW performance with a large corpus.

## Run the integrated agent

Apply catalog.sql to a fresh disposable pgvector database, install
`psycopg[binary]==3.2.13`, and set SUPPORT_DATABASE_URL. Then run:

    python labs/support-kb/pg_agent.py /tmp/support-demo.db case-1 "opening times"
    python labs/support-kb/verify_pg.py

The integrated agent uses PostgreSQL full-text ranking first and pgvector
for the controlled alias fallback. Ties, weak vectors and unknown queries
go to the durable handoff queue. The test verifies citation IDs and escalation
precedence end to end. The catalog is synthetic, and the alias vector is
hand-authored. A learned embedding model and production-scale recall were
not benchmarked.

## Learned embeddings

`python labs/support-kb/embed_eval.py` scores keyword, embedding and hybrid
retrieval on 36 queries (three per article in English, Roman Urdu and Urdu)
using an open multilingual sentence encoder. It needs `sentence-transformers`
and no API key. The queries were written for this lab, so the result describes
this small set only.
