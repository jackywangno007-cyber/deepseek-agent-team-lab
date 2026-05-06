# V0.4 Frontend Architecture

The React dashboard visualizes the FastAPI agent backend and V0.4 evaluation-driven improvement loop. The frontend is an API consumer only. It does not duplicate agent orchestration, artifact generation, evaluation, or task metadata logic.

## Stack

- React
- Vite
- TypeScript
- Plain CSS

The frontend reads `VITE_API_BASE_URL`, defaulting to:

```text
http://127.0.0.1:8000
```

## Component Responsibilities

- `App.tsx`: owns dashboard state, task selection, REST loading, and WebSocket lifecycle.
- `Layout.tsx`: page shell and top status bar.
- `TaskCreator.tsx`: form for task input, model, and mock mode.
- `TaskList.tsx`: workspace-backed task history from `GET /api/tasks`.
- `AgentBoard.tsx`: visual cards for Manager and worker agents.
- `EventTimeline.tsx`: chronological event stream from REST and WebSocket.
- `ArtifactExplorer.tsx`: clickable artifact list from the backend.
- `ArtifactViewer.tsx`: selected artifact content viewer.
- `EvaluationPanel.tsx`: rule-based evaluation result display.
- `HumanControlPanel.tsx`: save human feedback and request revision.
- `RevisionHistory.tsx`: show revision records.
- `ArtifactVersions.tsx`: show backed up versions for the selected artifact.
- `ImprovementSuggestions.tsx`: generate, edit, approve, and reject improvement suggestions.
- `ImprovementHistory.tsx`: show approved and rejected improvement actions.
- `EvaluationComparePanel.tsx`: show before/after evaluation data.
- `StatusBadge.tsx`: shared status label component.

## API Client

`frontend/src/api/client.ts` centralizes all backend calls:

- `getHealth`
- `createTask`
- `listTasks`
- `getTask`
- `getTaskEvents`
- `listArtifacts`
- `getArtifact`
- `getEvaluation`
- `createFeedback`
- `listFeedback`
- `requestRevision`
- `listRevisions`
- `listArtifactVersions`
- `getArtifactVersion`
- `generateImprovementSuggestions`
- `listImprovementSuggestions`
- `approveImprovementSuggestion`
- `rejectImprovementSuggestion`
- `getImprovementHistory`
- `getEvaluationCompare`
- `buildTaskEventsWebSocketUrl`

Components should not construct backend URLs themselves.

## WebSocket Flow

When a task is created or a running task is selected, `App.tsx` connects to:

```text
ws://127.0.0.1:8000/ws/tasks/{task_id}/events
```

The backend first sends existing events from `events.jsonl`, then streams new appended events. The frontend deduplicates events by:

```text
created_at + from_agent + to_agent + type + content
```

When a `task_finished` message arrives, the frontend refreshes:

- task metadata
- task list
- artifacts
- evaluation
- human feedback and revisions
- improvement suggestions and history
- evaluation comparison

## Agent Status Derivation

`frontend/src/utils/agentStatus.ts` derives frontend-only agent statuses from events:

- `agent_started` -> `RUNNING`
- `agent_completed` -> `COMPLETED`
- `final_summary` -> `ManagerAgent` completed
- `error` or failed status -> `FAILED`
- assignment but no start -> `WAITING`
- no selected task -> `IDLE`

No backend changes are required for these visual states.

## V0.4 Improvement Flow

V0.4 adds a proactive but human-approved improvement loop:

1. User creates a task and waits for completion.
2. User generates improvement suggestions from review and evaluation outputs.
3. User edits, approves, or rejects suggestions.
4. Approved suggestions create normal human feedback.
5. The existing V0.3 revision workflow runs.
6. Evaluation comparison and improvement history refresh.

The UI must keep approval explicit. Suggestions are recommendations, not automatic revisions.
