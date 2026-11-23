# Incident and failure reports

These reports cover reproducible failures in synthetic fixtures or disposable
development environments. They contain no production records.

## 1. A multilingual message missed the review queue

**Impact.** The baseline missed seven of ten review-worthy fixtures.
**Root cause.** Three English phrases did not cover Roman Urdu and Urdu wording.
**Fix.** Added six translated phrases and normalized punctuation and selected Urdu
characters. This reduced missed reviews from seven to one and introduced one
false alert when the matched phrase was followed by a denial.
**Verification.** Run `make -C labs/routing-audit demo`. Keep the denial and
the unmatched English paraphrase as explicit regression cases.

## 2. A TypeScript error passed the commit hook

**Impact.** A deliberately invalid type assignment was recorded in a disposable
repository. The staged checks had no TypeScript type check.
**Root cause.** The fast commit hook checks staged files for secrets and Python
formatting and lint. Full compilation happens at the push gate and in CI.
**Fix.** Restore the compatible assignment. Keep type checking in both the push
gate and CI so a local bypass does not remove the server-side check.
**Verification.** The faulty commit exited 0, the push exited 1 at TypeScript,
and the repaired push exited 0. See the
[quality template evidence](https://github.com/muiizz/quality-template/blob/main/docs/evidence.md).

## 3. Mutation artifacts interfered with normal test discovery

**Impact.** In the early template prototype, pytest discovered both the real
tests and copies emitted by mutmut after a mutation run.
**Root cause.** Test discovery started at the repository root and included the
mutation work directory.
**Fix.** Set pytest discovery to the tests directory. Rerun the ordinary gate
after a mutation run to verify collection stays scoped.
**Verification.** The prototype's gate passed after the change. The prototype
and current public template have separate mutation evidence.

## 4. A selective attendance query scanned a million rows

**Impact.** The synthetic weekly dashboard query returned 96 rows, with a
median execution time of 67.169 ms over five warm runs.
**Root cause.** The primary key did not serve the tenant and date filters.
**Fix.** Add a composite index on tenant and attendance date. Recheck ordered
result parity before comparing timings.
**Verification.** The indexed median was 0.126 ms and both ordered CSV exports
matched byte for byte. See the [plans and measurement protocol](../postgres/README.md).

**Customer-facing explanation.** The weekly attendance report used to look
through records for every school before finding yours. The revised lookup goes
directly to the matching school and dates. In our test with invented records,
both versions returned the same results in the same order.

## 5. Delivery was accepted before the worker recorded it

**Impact.** In a disposable database, a synthetic provider accepted a
delivery, then the worker failed before it could mark the outbox row sent.
The next worker tried the delivery again.

**Sequence.** The provider inbox insert committed, the test raised a synthetic
interruption, the outbox transaction rolled back, and a second worker retried.

**Cause.** The provider and local database have separate commit boundaries.
A local outbox lock cannot make both commits atomic.

**Fix.** Retry with the same event ID. The sample provider uses that ID as a
unique key. A retry marks the outbox row sent while leaving one inbox row.

**Prevention and verification.** The PostgreSQL integration test checks the
interruption and asserts that delivery succeeded without a duplicate inbox
record. An external provider needs its own idempotency or reconciliation
contract. See [webhook queue PR #3](https://github.com/muiizz/engineering-portfolio/pull/3).

## 6. A section name pointed to the wrong destination

**Impact.** In the synthetic promotion fixture, the same display name
identified position two in one year and position one in the next. A name
match would send a student to the wrong destination.

**Sequence.** The old section was selected, its name appeared in the next
year, and that name belonged to a different position.

**Cause.** The display label is editable. It is unsuitable as the identity
of a section across grade and year boundaries.

**Fix.** Select by target grade, year, and stable position. The matching
position can have a different label.

**Prevention and verification.** Keep a uniqueness constraint on year,
grade, and position. Retain the fixture where matching labels and matching
positions disagree. See the [synthetic school lab](../school-rls/README.md).
