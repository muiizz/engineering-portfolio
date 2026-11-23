# Abdul Muizz | Engineering portfolio

A recruiter-facing site with reproducible synthetic projects in PostgreSQL tuning, multilingual routing, support evaluation and release quality. The site works from a local HTTP server and uses relative links for GitHub Pages project paths.

[Printable résumé](resume.html) · [PostgreSQL measurements](labs/postgres/README.md) · [Routing audit](labs/routing-audit/README.md) · [Quality proofs](https://github.com/muiizz/quality-template) · [Multilingual rules engine](https://github.com/muiizz/llm-safety-rules-engine)

Run `make demo` for the fast offline checks.

## Run locally

Requires Python 3.10 or later. From the repository root:

```sh
python -m http.server 8000
```

Open `http://localhost:8000/`. Run the demonstrations and tests:

```sh
python -m unittest discover -s tests -v
python demo/quality_gate.py
python demo/eval.py
python demo/eval.py path/to/answers.json
```

The evaluator expects a JSON object keyed by case ID, with `route` and `reply` fields. A missing or incorrect answer fails the gate. See `demo/answers.json` for the format and `demo/cases.json` for the fictional cases. The scorer checks exact routes and case-insensitive required phrases. It does not assess general response quality.

The optional MCP server requires the Python MCP SDK (`python -m pip install mcp`). Run `python demo/server.py` as a stdio server. Its `grade_answer` tool uses the same scorer and expects a known case ID.

## Publish

Push this repository to GitHub with `main` as the default branch. In repository settings, select **Pages → Build and deployment → GitHub Actions**. The Pages workflow deploys on pushes to `main` or can be run manually. CI runs the tests and command-line demos on pushes and pull requests.

All scenarios and data are synthetic. The examples are intentionally narrow and do not represent production performance.
