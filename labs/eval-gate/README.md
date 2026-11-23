# Multilingual evaluation gate

The offline gate scores 120 generated messages across English, Roman Urdu and Urdu script. Four intents are reused across ten context variants per language. These are controlled test variants with shared intent phrases.

Run with Python 3.12 from the repository root:

    python labs/eval-gate/run.py --export /tmp/support-cases.json
    python labs/eval-gate/run.py
    python labs/eval-gate/run.py --answers candidate.json

Candidate answers are a JSON object keyed by fixture ID, with string fields route and reply. Missing answers fail. The scorer checks route, required wording and two forbidden phrases. The urgent check requires all 30 urgent cases to pass.

## Verified locally on 24 November 2026

The reference answers derived from the fixture labels passed 120 of 120. Empty candidate answers returned exit 1 and passed 0 of 120. These are controls for the scoring code. Provider comparison, independent judgement, cost and latency measurements require separately collected candidate responses.
