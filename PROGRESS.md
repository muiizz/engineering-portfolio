# Progress

One dated entry per session, newest first. Facts only. Each number can be reproduced from the linked repo.

## 23 Nov 2026: Project 9, quality-template

Repo: https://github.com/muiizz/quality-template
Commit: `9bf1909863aca5082efdbf53965d5d712cba40b6` (main, after PR 6)

Done:
- One `make check` that runs the gates locally and in CI. CI installs from lockfiles, then calls `make check`.
- Gates: gitleaks, ruff, ruff format, mypy strict, eslint, prettier, `tsc --noEmit`, sqlfluff, file hygiene, pytest and vitest with a 90% coverage bar, mutmut mutation score on the Python core (bar 0.95).
- 17 automated proofs: 14 injected faults (each blocked by the expected gate), 1 clean control, 2 adoption script tests.
- Branch protection on `main` (required `check`, up-to-date branch, applies to admins, no force push or deletion). A throwaway PR with a type error failed `check` and could not be merged (PR 4, closed).
- Private vulnerability reporting enabled. `scripts/adopt.sh` copies the gates into another repo.

Measured (README results table has dates, machine and commands):
- Mutation score 40 killed of 40. Python and TypeScript coverage 100%.
- `make check` 2 min 20 s, 2 min 25 s and 2 min 58 s locally; 2 min 4 s on GitHub Actions for PR 5.

Open items:
- `INTERVIEW.md` answers are empty. I write them.
- The fresh clone check ran on the same machine with warm caches, not a clean machine.
- Not shown: macOS, Windows or arm64; mutation testing for TypeScript; proofs for combined faults.
- Vetting items n/a for this repo: injection and leakage tests, spend cap test, run records or traces (no model is called).

Next step: Project 6, llm-safety-rules-engine. Plan first, then wait for approval. It adopts the gates with `scripts/adopt.sh`, which tests the adoption script on a real second repo.
