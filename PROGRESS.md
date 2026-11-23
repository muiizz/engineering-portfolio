# Progress

One dated entry per session, newest first. Facts only. Each number can be reproduced from the linked repo.

## 23 Nov 2026: Portfolio release candidate

The public-facing site includes a printable résumé, existing rules-engine and quality-template evidence, a reproducible PostgreSQL case study, a consent-aware routing audit and an MCP support grader. Local checks and negative controls are recorded in the project materials. The PostgreSQL experiment used a single local PostgreSQL 16.2 backend with one million synthetic rows. See [the measured plans](labs/postgres/README.md).

## 23 Nov 2026: Project 6, llm-safety-rules-engine

Repo: https://github.com/muiizz/llm-safety-rules-engine
Commit: `d0d5e92bd69a0748796ca4c709879c0edc43b498` (main). Gates adopted from quality-template `f5d8ff6` (rewritten history, see the Project 9 entry) with `scripts/adopt.sh`, trimmed to Python only.

Done:
- Toy rules engine in English, Roman Urdu and Urdu script on invented data. Pipeline order: normalise, rules, consent, model stub, output check.
- Hypothesis properties: urgent never reaches the model, no model call without consent, adding text never lowers the level, normalisation idempotent.
- Synthetic set of 342 messages (seeded, dev and test split), paraphrase generator, per-language confusion matrix.
- Four rounds of the fix loop, each committed with result files. Four ADRs. Branch protection on `main`, private vulnerability reporting on.

Measured (test split; the README and `docs/fix_loop.md` have commands, machine and commits):
- Mutation killed 112/115 at R0 and 189/196 at R3 (7 survivors, all equivalent).
- R0: Roman Urdu and Urdu recall 0.00 while mutation score 0.97. R3: recall 1.00 and 1.00, English 0.90.
- Missed urgent 81 to 3 of 90. False urgent rate 0.049 to 0.148.
- `make check` 22 s locally, 131 tests, coverage 98.70%. GitHub `check` passed on `6dd2f27`.

What failed: folding repeated letters broke the output check ("need" became "ned"). A unit test caught it. Fixed by splitting `normalise` and `plain`.

Open items:
- A native reader has not reviewed the Roman Urdu and Urdu script text. No number is hand checked.
- The test split is not blind. Three English test misses are not yet examined.
- `INTERVIEW.md` answers are empty.
- No past-system figures or naming permission were provided, so none are used.
- Not done: the proof that branch protection blocks a failing PR was run on quality-template only.

Next step: Project 4, llm-eval-gate. Plan first, then wait for approval.

## 23 Nov 2026: Project 9, quality-template

Repo: https://github.com/muiizz/quality-template
Commit: `f5d8ff6c4a7ebae0d8d9c4ba0f211361924df6b0` (main, after PR 6). Note: on 23 Nov 2026 I rewrote this repo's history to remove a file that should not have been public. The commit I first recorded here, `9bf1909`, no longer exists; `f5d8ff6` has the same content minus that file and two edited lines in CLAUDE.md. The repo was then deleted and recreated with the same history, so its commit SHAs are unchanged and GitHub no longer serves the old ones. PR numbers restart at 1, and the README evidence links were updated.

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
