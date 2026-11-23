"""Repeat a warm PostgreSQL benchmark in one isolated, socket-free backend."""
import csv
import json
import platform
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from pgserver._commands import POSTGRES_BIN_PATH as BIN

def sql(name):
    return " ".join((Path("sql") / name).read_text().split()).rstrip(";")

def run(output, query=None, index=None, revised_query=None):
    query = query or sql("query.sql")
    index = sql("index.sql") if index is None else index
    output.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        db = temp / "db"
        subprocess.run([BIN / "initdb","-D",db,"-A","trust"], check=True, capture_output=True)
        cmds = sql("seed.sql").split(";")
        cmds.append("CREATE FUNCTION plan(q text) RETURNS json LANGUAGE plpgsql AS $$ DECLARE p json; BEGIN EXECUTE 'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' || q INTO p; RETURN p; END $$")
        def export(statement, filename):
            cmds.append(f"COPY ({statement}) TO '{temp/filename}' WITH CSV HEADER")
        export("SELECT count(*) AS rows, version() AS version FROM attendance", "environment.csv")
        for phase in ("before","after"):
            if phase == "after" and index:
                cmds.append(index)
            active_query = revised_query if phase == "after" and revised_query else query
            for n in range(6):
                export("SELECT plan($q$"+active_query+"$q$)", f"{phase}-{n}.csv")
            export(active_query,f"{phase}-result.csv")
        result = subprocess.run([BIN/"postgres","--single","-D",db,"postgres"], input=";\n".join(cmds)+";\n",text=True,capture_output=True,check=True)
        if "ERROR:" in result.stderr or "FATAL:" in result.stderr:
            raise RuntimeError(result.stderr)
        env = next(csv.DictReader((temp/"environment.csv").read_text().splitlines()))
        assert int(env["rows"]) == 1_000_000
        for phase in ("before","after"):
            times = []
            for n in range(6):
                with (temp/f"{phase}-{n}.csv").open() as f:
                    raw = next(csv.DictReader(f))["plan"]
                (output/f"{phase}-{n}.json").write_text(raw+"\n")
                if n:
                    times.append(json.loads(raw)[0]["Execution Time"])
            env[phase] = {"runs_ms":times, "median_ms":median(times)}
            (output/f"{phase}-result.csv").write_bytes((temp/f"{phase}-result.csv").read_bytes())
    rows = (output/"before-result.csv").read_bytes()
    assert rows == (output/"after-result.csv").read_bytes() and len(rows.splitlines())>1
    env.update(result_rows=len(rows.splitlines())-1, machine=platform.platform(), utc=datetime.now(timezone.utc).isoformat(),
               source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip())
    (output/"summary.json").write_text(json.dumps(env,indent=2)+"\n")
    return env

if __name__ == "__main__":
    import sys
    print(json.dumps(run(Path(sys.argv[1])), indent=2))
