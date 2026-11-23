# Finding one school's attendance in a million rows

A fictional school dashboard requests one tenant's records for a week, ordered by date and attendance ID. The table has a primary key on attendance ID. The baseline plan filters the heap. The new composite index on tenant and attendance date lets PostgreSQL locate matching rows first.

| Measurement | Primary key only | With composite index |
|---|---:|---:|
| Median execution time, five warm runs | 67.169 ms | 0.126 ms |
| Ordered rows returned | 96 | 96 |

The runner compared the two CSV exports byte for byte. Both conditions used one warm-up followed by five measured queries in the same single-user PostgreSQL 16.2 backend on Linux x86-64. The first condition always ran first. This measures a selective local query on generated data. It omits concurrency, network time, and the write and storage costs of maintaining the added index.

## Reproduce

From this directory on Linux, run:

    uv run --python 3.12 --with-requirements requirements.txt single.py run-results

Use a new output directory for each run. The SQL seed is deterministic. The runner creates a temporary private cluster, loads 1,000,000 rows, and exports all plans. Execution times vary by host and cache state.

See [dated timings and source revision](measured/summary.json), [baseline plan](measured/before-1.json), and [indexed plan](measured/after-1.json). Each plan includes buffer activity. No live school systems were queried.

## Six-query benchmark suite

Run from this directory with a fresh output path:

    uv run --python 3.12 --with-requirements requirements.txt suite.py run-results

Each case starts from a freshly seeded million-row database. It compares five
warm runs per phase, excludes one warmup per phase and verifies identical ordered
CSV results. The pagination case assumes a known cursor and the unchanged seed.
For arbitrary records, take the cursor from the preceding page.

| Case | Baseline median | Revised median | Matching rows |
|---|---:|---:|---:|
| Tenant week | 47.294 ms | 0.091 ms | 96 |
| Student history | 46.283 ms | 0.028 ms | 10 |
| Absence review | 49.983 ms | 0.471 ms | 500 |
| Date export | 55.440 ms | 0.171 ms | 1,370 |
| Month filter | 160.394 ms | 35.198 ms | 42,465 |
| Deep pagination | 114.436 ms | 0.027 ms | 100 |

The [measurement summary](suite-evidence/summary.json) includes the run dates,
host, server version and all timing samples. Representative JSON plans are in
suite-evidence. The runner exports every plan on reproduction.
