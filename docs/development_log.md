# Development Log

## Template

### Date

### Goal

### Changes

### Tests Run

### Issues Encountered

### Lessons Learned

### Next Steps

## 2026-05-06

### Goal

Introduce a professional Git workflow after V0.1 and V0.2 were completed.

### Changes

- Initialized Git for the repository.
- Added a safe `.gitignore`.
- Added retrospective version notes.
- Documented the baseline strategy and future branching workflow.

### Tests Run

- `pytest`
- `npm run build` from `frontend/`

### Issues Encountered

- V0.1 and V0.2 were developed before Git history existed, so historical commits cannot be reconstructed honestly.

### Lessons Learned

- Git should be introduced at the beginning of a project, even for local prototypes.
- Retrospective version notes are better than fake history.
- Future versions should use branches, commits, tags, and testing notes.

### Next Steps

- Commit the current working codebase as the stable baseline.
- Tag the baseline.
- Continue work on a dedicated next-version branch.

## 2026-05-06 - V0.3

### Goal

Upgrade the observable AgentOps dashboard into a human-in-the-loop multi-agent collaboration system.

### Changes

- Added human feedback persistence through `human_feedback.jsonl`.
- Added revision requests and `revision_history.jsonl`.
- Added artifact version backup under `versions/` before overwriting artifacts.
- Added target-agent rerun and explicit downstream rerun rules.
- Refreshed `evaluation.json` after revisions.
- Added FastAPI endpoints for feedback, revisions, artifact versions, and version reads.
- Added frontend HumanControlPanel, RevisionHistory, and ArtifactVersions components.
- Updated API, frontend, manual testing, and human-in-the-loop documentation.

### Tests Run

- `.venv\Scripts\python.exe -m pytest`
- `npm install` from `frontend/`
- `npm run build` from `frontend/`
- CLI mock task smoke test
- Local backend health smoke test
- Local frontend dev-server smoke test

### Issues Encountered

- Vite/esbuild needed normal process-spawn permissions on Windows; sandboxed build attempts can fail with `spawn EPERM`.
- Artifact backup names initially used second-level timestamps, which could collide during fast repeated revisions.
- The artifact-version API initially returned an empty list for a missing artifact instead of a clearer 404.

### Lessons Learned

- Human intervention is safer when feedback is persisted before revision starts.
- Revision systems should never overwrite artifacts without first saving a versioned backup.
- Upstream artifact changes need explicit downstream rerun rules so behavior stays understandable.
- API contracts should distinguish "no versions yet" from "artifact does not exist."

### Next Steps

V0.4 - Evaluation-driven agent improvement or more advanced AgentOps features.

## 2026-05-06 - V0.4 Design

### Goal

Design the next engineering iteration without implementing V0.4 code.

### Changes

- Added `docs/v0.4_design.md`.
- Defined the V0.4 theme: evaluation-driven agent improvement.
- Planned improvement suggestions, approval/rejection flow, and before/after evaluation comparison.
- Documented that V0.4 must reuse the V0.3 human feedback and revision workflow.

### Tests Run

- No code changes for V0.4 design.
- V0.3 final polish was validated before this branch with `pytest` and `npm run build`.

### Issues Encountered

- V0.4 needs to stay proactive without becoming fully automatic. Human approval remains a product and safety requirement.

### Lessons Learned

- V0.3 makes revision possible; V0.4 should make the system better at proposing what to revise.
- Keeping improvement suggestions as workspace artifacts preserves the project’s artifact-driven architecture.

### Next Steps

- Implement suggestion extraction in a small backend service.
- Add frontend panels for suggestions and evaluation comparison.
- Keep all V0.4 changes behind explicit human approval.

## 2026-05-06 - V0.4 Implementation

### Goal

Implement the evaluation-driven improvement loop described in the V0.4 design.

### Changes

- Added a rule-based `ImprovementEngine`.
- Added `ImprovementService` to persist suggestions, history, and evaluation comparisons.
- Added APIs for generating, listing, approving, and rejecting suggestions.
- Reused V0.3 feedback and revision workflow for approved suggestions.
- Added frontend panels for suggestions, improvement history, and evaluation comparison.
- Added backend tests for suggestion generation, approval, rejection, and evaluation comparison.

### Tests Run

- `.venv\Scripts\python.exe -m pytest`
- `npm install` from `frontend/`
- `npm run build` from `frontend/`

### Issues Encountered

- API version tests needed to move from `0.3.0` to `0.4.0`.
- JSX text containing `->` needed escaping in React components.

### Lessons Learned

- The existing V0.3 revision workflow was reusable with a thin improvement service.
- Rule-based suggestion generation is enough to validate the improvement loop before adding smarter extraction.

### Next Steps

- Manually test the full browser flow.
- Review suggestion quality and mapping rules before expanding V0.4.

## 2026-05-06 - V0.3 Final Polish

### Goal

Finalize small V0.3 reliability and documentation fixes before moving into V0.4 design.

### Changes

- Allowed local development CORS origins across localhost and 127.0.0.1 ports.
- Stopped sending `Content-Type: application/json` on bodyless frontend GET requests.
- Added periodic backend health checks so the UI can recover from an initial offline state.
- Hardened `.env` parsing by trimming accidental spaces and wrapping quotes.
- Updated V0.3 version notes and roadmap language.

### Tests Run

- `.venv\Scripts\python.exe -m pytest`
- `npm install` from `frontend/`
- `npm run build` from `frontend/`
- Manual CORS preflight check for `OPTIONS /api/health`
- Manual backend health check for `GET /api/health`

### Issues Fixed

- Browser CORS preflight requests to `/api/health` could return `400 Bad Request`.
- The dashboard could remain `OFFLINE` if the backend started after the frontend page loaded.
- `.env` values with accidental quotes or surrounding whitespace could cause confusing connection failures.

### Lessons Learned

- Local dashboards should tolerate backend restart order during manual testing.
- GET requests should avoid unnecessary JSON headers to reduce CORS preflight behavior.
- CORS tests should include both `localhost` and `127.0.0.1` origins.

### Next Steps

V0.4 - Evaluation-driven agent improvement or more advanced AgentOps features.
