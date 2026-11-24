# Abdul Muizz | Engineering portfolio

Live site: https://muiizz.github.io/engineering-portfolio/

Applied AI evaluation, safety rules and PostgreSQL work, each with a demo built from recorded results. Scenarios and data are synthetic unless a page says otherwise.

## What is here

| Area | Where |
|---|---|
| Divia, a live doctor-led diabetes coach: architecture and live evaluation | `divia.html` |
| Reply checks published from Divia's evaluation runner | `labs/divia-reply-checks`, `divia-checks.html` |
| Runnable rewrite of the rules, model and checks flow | `labs/workbook-eval` |
| Three live models on 120 multilingual cases, plus a harder set | `labs/eval-gate`, `live-eval.html` |
| Tool-using agent scored on tool choice | `labs/support-agent`, `agent.html` |
| Multilingual safety rules and a mutation-testing blind spot | `safety-rules.html`, [llm-safety-rules-engine](https://github.com/muiizz/llm-safety-rules-engine) |
| Support routing, MCP grader, knowledge base retrieval | `labs/routing-audit`, `demo/`, `labs/support-kb` |
| PostgreSQL: query tuning, webhook queue, row-level security | `labs/postgres`, `labs/webhook-queue`, `labs/school-rls` |
| Release gates with fault proofs | `quality-gate.html`, [quality-template](https://github.com/muiizz/quality-template) |
| Ten incident reports | `labs/incidents`, `incidents.html` |
| Hard questions about this work | `INTERVIEW.md` |

## Run locally

Requires Python 3.12. From the repository root:

```sh
python -m http.server 8000
make check
```

`make check` runs every offline test and demo. It calls no model and needs no key. The reply checks need `pydantic` and run in their own workflow.

The live evaluations run only from the manual "Live model evaluation" workflow, which needs an `ANTHROPIC_API_KEY` secret and stops at a token or cost ceiling.

## How this is built

I work with AI coding agents. I decide the architecture, write the specification, set the tests and gates a change must pass, and review what merges.

## Publish

Pushes to `main` run the checks and deploy to GitHub Pages.
