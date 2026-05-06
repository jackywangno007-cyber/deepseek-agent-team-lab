# Manual Testing V0.4

Use this guide to manually verify the evaluation-driven improvement loop.

## 1. Start Backend

```bash
python run_server.py
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 2. Start Frontend

```bash
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 3. Create Mock Task

Create:

```text
Design an MVP for a student course management system
```

Use:

```text
mock = true
model = deepseek-v4-flash
```

Wait until the task is `COMPLETED`.

## 4. Generate Improvement Suggestions

In the Improvement Suggestions panel, click:

```text
Generate
```

Confirm:

- Suggestions appear.
- Each suggestion has a responsible agent.
- Each suggestion has a target artifact.
- `events.jsonl` includes `improvement_suggestions_generated`.
- `improvement_suggestions.jsonl` exists in the task workspace.

## 5. Approve One Suggestion

Choose a suggestion related to `api_design.md` or `test_plan.md`.

Optionally edit the proposed feedback, keep downstream rerun enabled, and click:

```text
Approve
```

Confirm:

- Human feedback is created.
- Revision workflow starts.
- EventTimeline shows `improvement_approved`.
- EventTimeline shows `improvement_revision_started`.
- EventTimeline shows `improvement_revision_completed`.
- Artifact versions are backed up if artifacts are overwritten.
- ImprovementHistory shows the approved action.
- EvaluationComparePanel shows before and after evaluation data.

## 6. Reject Another Suggestion

Enter a reason such as:

```text
Not relevant for MVP scope.
```

Click:

```text
Reject
```

Confirm:

- Suggestion status becomes `REJECTED`.
- ImprovementHistory records the rejected action.
- EventTimeline shows `improvement_rejected`.

## 7. Inspect Workspace

Open the generated task folder under:

```text
workspace/task_YYYYMMDD_HHMMSS_xxxxxx/
```

Confirm these files exist after V0.4 actions:

- `improvement_suggestions.jsonl`
- `improvement_history.jsonl`
- `evaluation_compare.json`
- `human_feedback.jsonl`
- `revision_history.jsonl`
- `events.jsonl`

## 8. Backend API Checks

Useful endpoints:

```text
POST /api/tasks/{task_id}/improvements/generate
GET /api/tasks/{task_id}/improvements
POST /api/tasks/{task_id}/improvements/{suggestion_id}/approve
POST /api/tasks/{task_id}/improvements/{suggestion_id}/reject
GET /api/tasks/{task_id}/improvements/history
GET /api/tasks/{task_id}/evaluation/compare
```

## Expected Result

V0.4 passes manual testing when suggestions can be generated, approved, rejected, persisted, linked to revisions, and reflected in evaluation comparison without breaking V0.3 human feedback or manual revision flows.
