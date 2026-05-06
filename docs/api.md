# V0.4 API Documentation

The API exposes the local agent runtime, human feedback workflow, and evaluation-driven improvement loop through FastAPI. It is intended for local development and the React AgentOps dashboard.

## Task Lifecycle

```text
CREATED -> RUNNING -> COMPLETED
                 \-> FAILED
```

- `CREATED`: task workspace and `task_meta.json` exist.
- `RUNNING`: the agent pipeline is executing.
- `COMPLETED`: all artifacts and `evaluation.json` were generated.
- `FAILED`: the pipeline raised an error; `task_meta.json` contains a sanitized error string.

## Endpoints

### GET /api/health

Response:

```json
{
  "status": "ok",
  "version": "0.4.0"
}
```

### POST /api/tasks

Request:

```json
{
  "task": "Design an MVP for a student course management system",
  "mock": true,
  "model": "deepseek-v4-flash",
  "run_async": false
}
```

Response:

```json
{
  "task_id": "task_20260504_210000_ab12cd",
  "status": "COMPLETED",
  "workspace_path": "workspace/task_20260504_210000_ab12cd"
}
```

Set `run_async` to `true` to return immediately while the pipeline runs in the background.

### GET /api/tasks

Lists tasks by scanning `workspace/*/task_meta.json`, sorted by `created_at` descending.

### GET /api/tasks/{task_id}

Returns task metadata, including status, model, mock flag, workspace path, and error.

### GET /api/tasks/{task_id}/events

Reads `events.jsonl` and returns the event list.

### GET /api/tasks/{task_id}/artifacts

Lists files inside the task workspace with name, path, size, and modified time.

### GET /api/tasks/{task_id}/artifacts/{artifact_name}

Reads one artifact.

Example:

```bash
curl http://127.0.0.1:8000/api/tasks/task_xxx/artifacts/prd.md
```

### GET /api/tasks/{task_id}/evaluation

Reads `evaluation.json`.

Response:

```json
{
  "task_id": "task_xxx",
  "evaluation": {
    "artifacts_complete": true,
    "events_complete": true,
    "review_score_found": true,
    "final_summary_found": true,
    "passed": true
  }
}
```

### GET /api/tasks/{task_id}/evaluation/compare

Reads `evaluation_compare.json` if an approved improvement has refreshed evaluation.

Response:

```json
{
  "task_id": "task_xxx",
  "before": {},
  "after": {},
  "changed": true,
  "summary": "Evaluation refreshed after approved improvement."
}
```

### POST /api/tasks/{task_id}/feedback

Saves human feedback without running a revision.

Request:

```json
{
  "target_agent": "ProductAgent",
  "target_artifact": "prd.md",
  "content": "The target users should be university students."
}
```

Response:

```json
{
  "feedback_id": "feedback_20260506_153000_ab12cd",
  "status": "PENDING"
}
```

### GET /api/tasks/{task_id}/feedback

Lists saved human feedback records from `human_feedback.jsonl`.

### POST /api/tasks/{task_id}/revisions

Requests a revision from saved feedback.

Request:

```json
{
  "feedback_id": "feedback_20260506_153000_ab12cd",
  "rerun_downstream": true,
  "run_async": true
}
```

Response:

```json
{
  "revision_id": "revision_20260506_153100_cd34ef",
  "status": "RUNNING"
}
```

### GET /api/tasks/{task_id}/revisions

Lists revision records from `revision_history.jsonl`.

### GET /api/tasks/{task_id}/artifacts/{artifact_name}/versions

Lists backed up versions for one artifact.

### GET /api/tasks/{task_id}/artifacts/{artifact_name}/versions/{version_name}

Reads a backed up artifact version from `versions/`.

### POST /api/tasks/{task_id}/improvements/generate

Generates rule-based improvement suggestions from `review_report.md` and `evaluation.json`.

Request:

```json
{
  "force": false
}
```

Response:

```json
{
  "task_id": "task_xxx",
  "suggestions": [
    {
      "suggestion_id": "suggestion_20260506_153000_ab12cd",
      "issue_summary": "API design does not cover course withdrawal.",
      "responsible_agent": "BackendAgent",
      "target_artifact": "api_design.md",
      "proposed_feedback": "Please add course withdrawal API design.",
      "severity": "medium",
      "reason": "ReviewerAgent found missing backend coverage.",
      "source": "review_report.md",
      "status": "PENDING",
      "created_at": "2026-05-06T15:30:00",
      "updated_at": "2026-05-06T15:30:00"
    }
  ]
}
```

### GET /api/tasks/{task_id}/improvements

Lists suggestions from `improvement_suggestions.jsonl`.

### POST /api/tasks/{task_id}/improvements/{suggestion_id}/approve

Approves a suggestion, creates human feedback, and triggers the V0.3 revision workflow.

Request:

```json
{
  "edited_feedback": null,
  "rerun_downstream": true,
  "run_async": true
}
```

### POST /api/tasks/{task_id}/improvements/{suggestion_id}/reject

Rejects a suggestion and records the reason in `improvement_history.jsonl`.

### GET /api/tasks/{task_id}/improvements/history

Lists approved and rejected improvement actions.

## WebSocket Event Stream

Endpoint:

```text
ws://127.0.0.1:8000/ws/tasks/{task_id}/events
```

When a client connects, the server first sends existing events from `events.jsonl`, then polls for appended events.

Event message:

```json
{
  "type": "event",
  "data": {
    "task_id": "task_xxx",
    "from_agent": "ProductAgent",
    "to_agent": null,
    "type": "agent_completed",
    "content": "Completed prd.md",
    "artifact_refs": ["prd.md"],
    "status": "succeeded",
    "created_at": "2026-05-04T21:00:30"
  }
}
```

Finished message:

```json
{
  "type": "task_finished",
  "status": "COMPLETED"
}
```

## Security Notes

- Artifact reads are restricted to the selected task workspace.
- Path traversal such as `../.env` is blocked.
- Version reads are restricted to files inside `versions/`.
- Revisions back up artifacts before overwriting them.
- Improvements reuse human feedback and revisions instead of bypassing the approval loop.
- API keys are loaded from environment variables and are never returned by API responses.
- The API does not execute shell commands generated by users or agents.
- V0.4 has no authentication and is intended for local development only.
