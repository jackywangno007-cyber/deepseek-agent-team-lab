# Manual Testing Guide for V0.3

## 1. Start Backend

From the repository root:

```bash
python run_server.py
```

Confirm Swagger is available:

```text
http://127.0.0.1:8000/docs
```

## 2. Start Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 3. Create a Mock Task

Use this task:

```text
Design an MVP for a student course management system
```

Use:

- mock: checked
- model: `deepseek-v4-flash`

Click `Run agent team`.

## 4. Verify AgentOps Dashboard

Confirm:

- Task appears in the task list.
- Selected task status changes from `RUNNING` to `COMPLETED`.
- Agent cards change from `WAITING` to `RUNNING` to `COMPLETED`.
- Event timeline updates while the task runs.
- WebSocket status shows `CONNECTED` or `FINISHED`.

## 5. Verify Artifacts

Confirm the artifact list contains:

- `prd.md`
- `architecture.md`
- `frontend_plan.md`
- `api_design.md`
- `test_plan.md`
- `review_report.md`
- `final_summary.md`
- `evaluation.json`

Click:

- `prd.md`
- `review_report.md`
- `final_summary.md`

Confirm the viewer shows readable content.

## 6. Verify Evaluation

After completion, confirm the Evaluation panel shows:

```text
PASSED
artifacts_complete true
events_complete true
review_score_found true
final_summary_found true
```

## 7. Open a Previous Task

Click an older task in the task list.

Confirm:

- Existing events load.
- Existing artifacts load.
- Evaluation loads if available.
- WebSocket only connects for running tasks.

## 8. Backend Not Running State

Stop the backend and refresh the frontend.

Confirm:

- Backend status shows `OFFLINE`.
- Task loading or task creation shows a friendly error.
- No raw stack traces are shown.
