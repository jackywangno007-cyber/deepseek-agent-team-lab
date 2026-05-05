# Agent Methodology

The project models collaboration as artifact production instead of free-form conversation. Each agent has a narrow responsibility and a known output. This makes runs inspectable, reproducible, and easier to debug.

## Manager-Workers Pattern

The manager owns coordination:

- Understand the task.
- Create `task_plan.json`.
- Assign workers in order.
- Collect the reviewer output.
- Produce the final summary.

Workers own deliverables:

- Product produces `prd.md`.
- Architect produces `architecture.md`.
- Frontend produces `frontend_plan.md`.
- Backend produces `api_design.md`.
- Test produces `test_plan.md`.
- Reviewer produces `review_report.md`.

## Why Artifacts Matter

Artifacts make the pipeline educational. A human can open each file and see how one role's output shaped the next role's input. This is the first step toward a visual system where each artifact and event becomes inspectable in a UI.
