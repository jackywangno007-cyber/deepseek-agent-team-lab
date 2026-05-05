# Architecture Notes

V0.1 uses a serial Manager-Workers pipeline. The manager creates the task workspace, writes a fixed plan, assigns each agent, and then produces a final summary. Each worker reads only its declared input artifacts and writes one output artifact.

## Runtime Components

- `run_task.py`: CLI entrypoint.
- `Orchestrator`: owns one complete task run.
- `TaskWorkspace`: creates isolated task directories and blocks path traversal.
- `EventBus`: appends structured JSONL events.
- `LLMClient`: calls DeepSeek through the OpenAI-compatible SDK or returns mock markdown.
- `Evaluator`: checks artifacts, events, review score, and final summary.

## Data Flow

```text
task_input.md
 -> task_plan.json
 -> prd.md
 -> architecture.md
 -> frontend_plan.md + api_design.md
 -> test_plan.md
 -> review_report.md
 -> final_summary.md
 -> evaluation.json
```

V0.1 is intentionally serial. Parallel execution, revision loops, and visual inspection belong in later versions.
