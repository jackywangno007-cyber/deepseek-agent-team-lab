# Human-in-the-loop Revision Workflow

V0.3 upgrades the local AgentOps dashboard into a controllable multi-agent collaboration system. A human can now give feedback to a specific agent, request an artifact revision, preserve the previous artifact version, and optionally rerun downstream agents.

## Design Motivation

The earlier system made agent collaboration observable. V0.3 makes it steerable while keeping the same local-first design:

- workspace remains the source of truth
- no database
- no authentication
- no shell command execution
- every human action is logged
- every overwritten artifact is backed up first

## Human Feedback Lifecycle

1. User selects a target artifact and agent.
2. User writes concrete feedback.
3. Backend validates the task, agent, and artifact.
4. Feedback is appended to `human_feedback.jsonl`.
5. A `human_feedback_created` event is written to `events.jsonl`.
6. Feedback starts as `PENDING`.

Feedback record:

```json
{
  "feedback_id": "feedback_20260506_153000_ab12cd",
  "task_id": "task_xxx",
  "target_agent": "ProductAgent",
  "target_artifact": "prd.md",
  "content": "The target users should be university students.",
  "created_at": "2026-05-06T15:30:00",
  "status": "PENDING"
}
```

## Revision Lifecycle

1. User selects saved feedback.
2. User requests revision.
3. Backend creates a revision record in `revision_history.jsonl`.
4. Backend backs up the current target artifact into `versions/`.
5. Backend reruns the target agent with the original prompt, inputs, current artifact, and human feedback.
6. Backend overwrites the target artifact.
7. If requested, backend reruns downstream agents.
8. Evaluator refreshes `evaluation.json`.
9. Feedback becomes `APPLIED`.
10. Revision becomes `COMPLETED`.

If anything fails, feedback becomes `FAILED`, revision becomes `FAILED`, and the error is stored without exposing stack traces or API keys.

## Backend APIs

- `POST /api/tasks/{task_id}/feedback`
- `GET /api/tasks/{task_id}/feedback`
- `POST /api/tasks/{task_id}/revisions`
- `GET /api/tasks/{task_id}/revisions`
- `GET /api/tasks/{task_id}/artifacts/{artifact_name}/versions`
- `GET /api/tasks/{task_id}/artifacts/{artifact_name}/versions/{version_name}`

## Frontend Components

- `HumanControlPanel`: save feedback and request revisions.
- `RevisionHistory`: inspect revision records.
- `ArtifactVersions`: inspect backed up artifact versions.

Existing panels continue to work:

- AgentBoard derives status from events.
- EventTimeline shows human feedback and revision events.
- ArtifactViewer can show current artifacts or backed up versions.
- EvaluationPanel refreshes after task completion or revision completion.

## Artifact Versioning

Before overwriting an artifact during revision, the backend copies it to:

```text
workspace/task_xxx/versions/
```

Example:

```text
versions/prd.20260506_153000.md
```

Version files are read only through dedicated version APIs. Path traversal is blocked.

## Safety Notes

- Do not execute shell commands from users or agents.
- Do not expose API keys.
- Do not write outside the task workspace.
- Do not overwrite artifacts without backup.
- Keep revision dependencies explicit and easy to understand.

## Future Improvements

- Diff viewer for current vs previous artifact.
- Pause/resume long-running revisions.
- Human approval before downstream rerun.
- More granular rerun selection.
- Richer revision scoring and comparison.
