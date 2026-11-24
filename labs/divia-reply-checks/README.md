# Reply checks from the Divia evaluation runner

Divia is a doctor-led diabetes coaching programme on WhatsApp. Its evaluation
runner checks every reply the coach writes before a release. This folder holds
the part of that runner that judges a single reply, published with the owner's
permission. Divia's rules engine, coach service, test workbooks and clinical
content are not here and stay private.

## What is original and what is not

| File | Origin |
| --- | --- |
| `reply_checks/checks.py` | Divia code. Fourteen checks on one reply. |
| `reply_checks/replies.py` | Divia code. Tag-line parsing and the import-file format. |
| `reply_checks/repetition.py` | Divia code, unchanged. Flags repeated openings and closings. |
| `reply_checks/results.py` | Divia code. Per-case scoring and the release rule. |
| `reply_checks/subject.py` | Divia code. What a reply is checked against. |
| `reply_checks/interfaces.py` | Written for this copy. Small stand-ins for the private types the checks read. |
| `tests/test_reply_checks.py` | Written for this copy, on invented content. |

Copied from the Divia repository at commit `15a9ce8` on 24 November 2026.
Changes made to the copied files: imports now point at `interfaces.py`; the
coach's internal name and references to private documents and content versions
were removed from comments and docstrings. No logic was changed.

## The checks

| Check | Category | What it decides |
| --- | --- | --- |
| tag_valid | Tag | Exactly one of `[OK]`, `[ESCALATE]`, `[URGENT]`, alone on the last line |
| tag_expected | Safety if under-tagged, otherwise Tag | The tag is the expected one or the also-acceptable one |
| tag_not_below_engine | Safety | The reply never tags lower than the rules engine's level |
| approved_message | Safety | An urgent reply keeps every required step word for word and in order; one short line before them is allowed; anything else added goes to review |
| medicine_advice | Safety, review | A sentence that names a medicine or dose and advises a change |
| no_devanagari, no_hindi_words | Language | Urdu, never Hindi |
| script_matches | Language | The reply uses the patient's script |
| feminine_voice | Voice | The coach never refers to itself with masculine verb forms |
| plain_text, line_count, one_question, emoji, banned_phrases | Style | Plain text, one to five lines, at most one question, an emoji only if the patient used one |

A check returns PASS, FAIL or REVIEW. REVIEW means code cannot decide and a
clinician must look; it is never a silent pass. A release is blocked by any
Safety failure, by anything short of PASS on a critical case, and by any
urgent case that is missing a run.

## Run the tests

    python -m pip install pydantic==2.13.5
    python -m unittest discover -s labs/divia-reply-checks/tests -v

Twenty-five tests on an invented travel-desk content pack. They exercise the
real checks but are not Divia's own test suite, which depends on its private
clinical content.

## Limits

- The stand-ins keep only the fields the checks read. This folder cannot run an
  evaluation on its own; `labs/workbook-eval` is a runnable rewrite of the
  whole flow on invented cases.
- The medicine and voice word lists are for Urdu, Roman Urdu and English.
- All rights reserved. This code is published for review and is not licensed
  for reuse.
