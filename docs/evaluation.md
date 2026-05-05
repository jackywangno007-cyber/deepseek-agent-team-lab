# Evaluation

V0.1 uses a lightweight rule-based evaluator. It does not call an LLM.

The evaluator checks:

- Required files exist.
- Markdown artifacts are non-empty.
- `review_report.md` contains a score in the form `N/10`.
- `final_summary.md` exists.
- Required event types appear in `events.jsonl`.

The output is written to `evaluation.json` and includes a single `passed` boolean.
