# Tool-using support agent

A model with four tools (look up a booking, search help, hand off, raise urgent)
on a small in-memory mock, scored on the tools it chooses.

    ANTHROPIC_API_KEY=... python labs/support-agent/agent_eval.py --models MODEL_A,MODEL_B

Each of the 24 tasks (eight per language) states the required tool sequence,
forbidden tools, the booking code that must be passed and a fact the reply must
contain. A task passes only if all five checks pass.

Run of 24 November 2026, three runs per model: Haiku 5.5 passed 24, 23, 24;
Sonnet 5.5 and Opus 5.5 passed 23, 23, 23. The repeated failure is one
ambiguous task ("When do I check in?") where the model made one extra,
reasonable search. See [the recorded results](results/summary.json).

Not covered: long conversations, failing tools, or tasks written by someone else.
