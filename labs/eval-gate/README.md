# Multilingual evaluation gate

The offline gate scores 120 generated messages across English, Roman Urdu and Urdu script. Four intents are reused across ten context variants per language. These are controlled test variants with shared intent phrases.

Run with Python 3.12 from the repository root:

    python labs/eval-gate/run.py --export /tmp/support-cases.json
    python labs/eval-gate/run.py
    python labs/eval-gate/run.py --answers candidate.json

Candidate answers are a JSON object keyed by fixture ID, with string fields route and reply. Missing answers fail. The scorer checks route, required wording and two forbidden phrases. The urgent check requires all 30 urgent cases to pass.

## Verified locally on 24 November 2026

The reference answers derived from the fixture labels passed 120 of 120. Empty candidate answers returned exit 1 and passed 0 of 120. These are controls for the scoring code. Provider comparison, independent judgement, cost and latency measurements require separately collected candidate responses.

## Compare two saved runs

`python labs/eval-gate/compare.py baseline.json candidate.json` compares
answer files on the same fixture IDs. It reports per-language results, newly
passing cases, regressions, and every candidate failure. It exits 1 when a
previously passing case regresses or any urgent case fails.

Run `python -m unittest discover -s labs/eval-gate -v` for the scorer's
positive and negative controls. The offline reference is label-derived.
Judge agreement, external provider baselines, variance, cost and latency
remain unmeasured.

## Live model run

`labs/eval-gate/live.py` sends the same 120 cases to live models and records
pass rate by language, urgent pass rate, token counts and latency. It needs an
API key and a model ID per provider and stops a model at a token ceiling. It is
run from the manual "Live model evaluation" workflow and is never part of
`make check`. Results are published to the `live-results` branch.
