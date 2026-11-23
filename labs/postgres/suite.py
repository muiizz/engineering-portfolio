"""Five repeated measurements per query phase, with ordered result parity."""
import argparse
import json
from pathlib import Path

from single import run, sql

BASE = "SELECT attendance_id, student_id, attended_on, present FROM attendance"
ORDERED = " ORDER BY attended_on, attendance_id"
CASES = {
    "tenant-week": (sql("query.sql"), sql("index.sql"), None),
    "student-history": (
        BASE + " WHERE tenant_id=37 AND student_id=41" + ORDERED,
        "CREATE INDEX ON attendance (tenant_id, student_id, attended_on, attendance_id)", None,
    ),
    "absence-review": (
        BASE + " WHERE tenant_id=37 AND NOT present" + ORDERED,
        "CREATE INDEX ON attendance (tenant_id, attended_on, attendance_id) WHERE NOT present", None,
    ),
    "date-export": (
        BASE + " WHERE attended_on=DATE '2025-03-01'" + ORDERED,
        "CREATE INDEX ON attendance(attended_on,attendance_id) INCLUDE(student_id,present)", None,
    ),
    "month-filter": (
        BASE + " WHERE date_trunc('month',attended_on::timestamp)=TIMESTAMP '2025-03-01'" + ORDERED,
        "CREATE INDEX ON attendance(attended_on,attendance_id)",
        BASE + " WHERE attended_on>=DATE '2025-03-01' AND attended_on<DATE '2025-04-01'" + ORDERED,
    ),
    "pagination": (
        BASE + " ORDER BY attendance_id LIMIT 100 OFFSET 800000",
        "",
        BASE + " WHERE attendance_id > 800000 ORDER BY attendance_id LIMIT 100",
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    output.mkdir()
    summary = {}
    for name, (query, index, revised_query) in CASES.items():
        summary[name] = run(output / name, query, index, revised_query)
    (output / "suite-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for name, result in summary.items():
        print(name, result["before"]["median_ms"], result["after"]["median_ms"], result["result_rows"])


if __name__ == "__main__":
    main()
