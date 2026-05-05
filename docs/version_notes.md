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

## Current Baseline

This Git baseline captures the current working state after V0.1 and V0.2 were completed. It is intentionally honest: the repository did not have Git commits during the original V0.1 and V0.2 development work, so this baseline does not pretend those historical commits existed.

The baseline is intended to make future work easier to review, roll back, present on GitHub, and explain in interviews.

## Next Version Plan

V0.3 - Human-in-the-loop Revision Workflow

Planned capabilities:

- Human feedback
- Artifact revision
- Artifact version backup
- Revision history
- Downstream agent rerun
- Updated evaluation after revision
