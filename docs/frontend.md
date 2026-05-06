# V0.3 Frontend Architecture

V0.3 adds a local React visualization UI for the existing FastAPI agent backend. The frontend is an API consumer only. It does not duplicate agent orchestration, artifact generation, evaluation, or task metadata logic.

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

## Agent Status Derivation

`frontend/src/utils/agentStatus.ts` derives frontend-only agent statuses from events:

- `agent_started` -> `RUNNING`
- `agent_completed` -> `COMPLETED`
- `final_summary` -> `ManagerAgent` completed
- `error` or failed status -> `FAILED`
- assignment but no start -> `WAITING`
- no selected task -> `IDLE`

No backend changes are required for these visual states.

## V0.4 Preparation

The V0.3 UI establishes the visual surfaces needed for V0.4 human-in-the-loop controls:

- selected task context
- live event stream
- agent status board
- artifact viewer
- evaluation result panel

V0.4 can add pause, resume, revise, and message-to-agent controls without changing the basic dashboard layout.

V0.3 now includes the first human-in-the-loop revision workflow. Future versions can improve it with diff views, approval gates, and more granular downstream rerun controls.
