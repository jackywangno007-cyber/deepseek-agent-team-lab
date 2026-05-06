# Version Notes

## V0.1 - CLI Multi-Agent Runtime

Status: Completed before Git baseline.

Main capabilities:

- Command-line task creation
- ManagerAgent
- ProductAgent
- ArchitectAgent
- FrontendAgent
- BackendAgent
- TestAgent
- ReviewerAgent
- Artifact-driven collaboration
- Workspace output
- `events.jsonl` logging
- Mock mode
- Real DeepSeek mode
- Evaluator

Engineering lessons:

- Agent collaboration should be artifact-driven, not just chat-driven.
- Each agent needs a clear role boundary.
- Mock mode is useful for local testing.
- Event logs are important for debugging.

## V0.2 - Local API Service and Visualization Dashboard

Status: Completed before Git baseline.

Main capabilities:

- FastAPI backend
- REST APIs for task creation, task list, task status, events, artifacts, and evaluation
- WebSocket event streaming
- React dashboard
- TaskCreator
- TaskList
- AgentBoard
- EventTimeline
- ArtifactExplorer
- ArtifactViewer
- EvaluationPanel
- Local AgentOps-style visualization

Engineering lessons:

- The core agent runtime should stay independent from the API layer.
- The frontend should consume backend APIs instead of duplicating logic.
- Agent status can be derived from event logs.
- Visualization makes agent collaboration easier to debug.

## V0.3 - Human-in-the-loop Revision Workflow

### Goal

Upgrade the project from an observable AgentOps dashboard into a controllable human-in-the-loop multi-agent collaboration system.

### Added

- Human feedback persistence
- Artifact revision workflow
- Artifact version backup
- Revision history
- Downstream agent rerun
- Evaluation refresh after revision
- HumanControlPanel
- RevisionHistory
- ArtifactVersions
- Human feedback and revision events
- Updated API and frontend documentation

### Validation

V0.3 was validated with:

- Mock task creation
- Human feedback saving
- Artifact revision
- Artifact version backup
- Revision history display
- Downstream rerun
- Evaluation refresh
- Backend pytest
- Frontend build

### Engineering Lessons

- Agent systems should allow humans to intervene when intermediate artifacts are wrong.
- Artifact revision should preserve previous versions before overwriting.
- Human feedback should be auditable and persisted.
- Changing upstream artifacts should trigger downstream regeneration when needed.
- A good multi-agent system should be observable, controllable, and reproducible.

### Manual Validation Details

The following V0.3 behaviors were verified:

- Mock task creation works.
- Human feedback can be saved.
- Artifact revision can be triggered.
- Old artifact versions are backed up.
- Revision history is visible through the API and frontend components.
- Downstream rerun works in mock mode.
- Evaluation refreshes after revision.

## Current Baseline

The first Git baseline captured the working state after V0.1 and V0.2 were completed. It is intentionally honest: the repository did not have Git commits during the original V0.1 and V0.2 development work, so this baseline does not pretend those historical commits existed.

V0.3 is the first feature version developed on top of that baseline branch workflow.

## Next Version Plan

## V0.4 - Evaluation-driven Agent Improvement

### Goal

Upgrade the system from manual human-found revisions to system-proposed, human-approved improvement suggestions.

### Added

- Rule-based improvement suggestion generation from `review_report.md` and `evaluation.json`.
- `improvement_suggestions.jsonl`.
- `improvement_history.jsonl`.
- `evaluation_compare.json`.
- Improvement suggestion APIs.
- Approve/reject suggestion APIs.
- Reuse of V0.3 feedback and revision workflow after approval.
- Frontend ImprovementSuggestions panel.
- Frontend ImprovementHistory panel.
- Frontend EvaluationComparePanel.

### Validation

V0.4 was validated with:

- `pytest`: 23 passed
- `npm run build`: passed
- `/api/health`: returned `0.4.0`
- Mock task creation worked
- Improvement generation returned suggestions
- Suggestion approval created human feedback and revision records
- Improvement history was written
- Evaluation comparison was written
- Suggestion rejection was persisted

### Known Limitations

- Suggestion generation is still rule-based.
- No visual diff view yet.
- No advanced LLM-assisted suggestion refinement yet.
- Evaluation comparison is still simple.
- Suggestion quality is good enough for workflow validation, but not yet deeply intelligent.

## Next Version Plan

V0.5 - Advanced AgentOps Review

Planned capabilities:

- Diff views for artifact revisions.
- More precise issue extraction.
- Better evaluation scoring and trend history.
- Optional approval gates before applying downstream reruns.
