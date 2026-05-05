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
