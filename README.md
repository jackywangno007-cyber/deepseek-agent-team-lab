# DeepSeek Agent Team Lab

DeepSeek Agent Team Lab is a lightweight local multi-agent collaboration system inspired by Manager-Workers architectures such as HiClaw. V0.1 validated the command-line agent runtime. V0.2 added a local FastAPI service. V0.3 adds a React dashboard for visual task creation, event streaming, artifact inspection, and evaluation review.

The system accepts a software project requirement, runs a fixed serial team of role-based agents, and writes every intermediate result as a markdown artifact inside an isolated task workspace.

## Why This Exists

Many multi-agent demos are just chat transcripts with several names attached. This project is different: agents collaborate through durable artifacts, constrained responsibilities, shared workspace state, and event logs. The goal is to learn how a real agent collaboration system can be structured before adding a backend service or visual interface.

## Design Principles

- Manager coordinates work; workers produce bounded artifacts.
- Every worker has declared input artifacts and one output artifact.
- Every important action is logged in `events.jsonl`.
- The reviewer uses a checklist and produces concrete revision items.
- Mock mode must run locally without an API key.
- No LangChain, CrewAI, AutoGen, LangGraph, database, Docker, frontend, or shell execution system in V0.1.

## Architecture

```text
CLI
 |
 v
ManagerAgent
 |-- task_plan.json
 |
 +--> ProductAgent    -> prd.md
 +--> ArchitectAgent  -> architecture.md
 +--> FrontendAgent   -> frontend_plan.md
 +--> BackendAgent    -> api_design.md
 +--> TestAgent       -> test_plan.md
 +--> ReviewerAgent   -> review_report.md
 |
 v
ManagerAgent          -> final_summary.md
Evaluator             -> evaluation.json
EventBus              -> events.jsonl
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

Copy `.env.example` to `.env` and set your credentials for real mode.

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
AGENT_TEMPERATURE=0.3
AGENT_MAX_TOKENS=4096
```

Never commit a real API key. The program does not print the API key.

## Run Mock Mode

```bash
python run_task.py --task "Design an MVP for a student course management system" --mock
```

Or read from a file:

```bash
python run_task.py --task-file examples/task_student_course_system.md --mock
```

Mock mode also runs automatically when no valid `DEEPSEEK_API_KEY` is present.

## Run Real DeepSeek Mode

```bash
python run_task.py --task "Design an MVP for a student course management system"
```

Override the model for a single run:

```bash
python run_task.py --task "Design an MVP for a student course management system" --model deepseek-v4-flash
```

## V0.2 Local API Service

V0.2 wraps the existing command-line agent runtime with a thin FastAPI service. It does not replace the CLI and it does not add a frontend yet. The workspace directory remains the source of truth.

What changed:

- REST APIs for task creation, task status, events, artifacts, and evaluation.
- `task_meta.json` in each task workspace.
- WebSocket event streaming for future visualization.
- `run_server.py` for local API startup.

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python run_server.py
```

Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

Create a mock task:

```bash
curl -X POST http://127.0.0.1:8000/api/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"task\":\"Design an MVP for a student course management system\",\"mock\":true,\"run_async\":false}"
```

On macOS or Linux:

```bash
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task":"Design an MVP for a student course management system","mock":true,"run_async":false}'
```

List tasks:

```bash
curl http://127.0.0.1:8000/api/tasks
```

Read an artifact:

```bash
curl http://127.0.0.1:8000/api/tasks/{task_id}/artifacts/prd.md
```

Stream task events:

```text
ws://127.0.0.1:8000/ws/tasks/{task_id}/events
```

The WebSocket first sends existing events from `events.jsonl`, then sends new appended events until the task reaches `COMPLETED` or `FAILED`. This prepares V0.3 for a React UI that can visualize agents, artifact creation, status changes, and review output in near real time.

## V0.3 React Visualization UI

V0.3 adds a local AgentOps-style dashboard under `frontend/`. It consumes the V0.2 REST APIs and WebSocket stream.

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the backend from the repository root:

```bash
python run_server.py
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The frontend backend URL is configured with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Manual test checklist:

- Create a mock task from the browser.
- Watch AgentBoard status changes.
- Watch EventTimeline append events.
- Open `prd.md`, `review_report.md`, and `final_summary.md`.
- Confirm EvaluationPanel shows `passed=true`.
- Select a previous task and inspect its artifacts.
- Stop the backend and confirm the UI shows a friendly offline/error state.

Known limitations:

- No authentication; local development only.
- Artifact markdown is displayed in a readable preformatted viewer.
- WebSocket streaming is backed by simple backend polling over `events.jsonl`.

## V0.3 Human-in-the-loop Revision

Human feedback is an auditable instruction saved against a specific agent and artifact. Feedback is stored in:

```text
workspace/task_xxx/human_feedback.jsonl
```

Revision is a separate action. When a revision runs, the backend:

1. reads saved feedback
2. backs up the current artifact into `versions/`
3. reruns the target agent with the human feedback
4. optionally reruns downstream agents
5. refreshes `evaluation.json`
6. logs all actions into `events.jsonl`

Revision history is stored in:

```text
workspace/task_xxx/revision_history.jsonl
```

Run locally:

```bash
python run_server.py
cd frontend
npm run dev
```

Run validation:

```bash
pytest
cd frontend
npm run build
```

Manual test:

- Create a mock task in the browser.
- Open `prd.md`.
- Save feedback for `ProductAgent`.
- Run revision with downstream rerun enabled.
- Confirm EventTimeline shows revision events.
- Confirm ArtifactVersions shows the old `prd.md`.
- Confirm EvaluationPanel refreshes after completion.

Current limitations:

- No artifact diff view yet.
- No approve/reject gate before applying a revision.
- No task cancellation, pause, or resume controls.
- Revision state is stored locally in workspace files rather than a database.

## Output Files

Each run creates a directory like:

```text
workspace/task_YYYYMMDD_HHMMSS_xxxxxx/
```

The directory contains:

- `task_input.md`: original requirement
- `task_meta.json`: local API task metadata
- `task_plan.json`: manager-generated execution plan
- `events.jsonl`: event stream for the run
- `prd.md`: product requirements
- `architecture.md`: technical architecture
- `frontend_plan.md`: frontend planning artifact
- `api_design.md`: backend API design
- `test_plan.md`: testing strategy
- `review_report.md`: reviewer checklist, scores, and revisions
- `final_summary.md`: manager summary
- `evaluation.json`: rule-based completion checks

## Tests

```bash
pytest
```

## Versioning and Git Workflow

V0.1 and V0.2 were completed before this repository had a Git baseline. The current baseline commit captures the working command-line runtime, local API service, and visualization dashboard state without pretending earlier historical commits existed.

Future versions should use feature branches. Each version should have:

- focused commits
- a version tag
- version notes
- manual testing notes
- screenshots if useful

Suggested workflow:

```bash
git checkout -b v0.3-human-in-the-loop
```

After completing a feature:

```bash
git add .
git commit -m "feat(api): add human feedback endpoints"
```

After completing a version:

```bash
git tag v0.3.0
```

## Roadmap

V0.2: Add a small FastAPI backend to start and inspect task runs. Completed.

V0.3: Add a React visualization plus human-in-the-loop artifact revision workflow. Completed.

V0.4: Add evaluation-driven improvement suggestions that parse review findings, propose revisions, and keep humans in the approval loop.

## Resume-Ready Highlights

- Built a framework-free Manager-Workers multi-agent pipeline.
- Implemented artifact-driven collaboration with role boundaries.
- Added reproducible mock mode for local development.
- Added event logging and rule-based evaluation.
- Designed the project as a foundation for future API and visualization layers.
