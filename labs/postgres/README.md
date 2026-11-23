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
