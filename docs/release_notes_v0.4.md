# V0.4 Release Notes

## Summary

V0.4 introduces evaluation-driven agent improvement.

The system can now analyze reviewer and evaluator outputs, generate structured improvement suggestions, let the human approve or reject them, and reuse the existing V0.3 human feedback and revision workflow.

## Main Features

- Improvement suggestion generation from `review_report.md` and `evaluation.json`
- Suggestion approval and rejection
- Human-approved suggestions become regular V0.3 feedback and revisions
- Improvement history in `improvement_history.jsonl`
- Evaluation comparison in `evaluation_compare.json`
- Frontend panels for suggestions, history, and evaluation comparison
- Backend APIs for improvement generation, approval, rejection, history, and comparison

## Validation

Commands run:

```bash
.venv\Scripts\python.exe -m pytest
cd frontend
npm install
npm run build
```

Results:

- `pytest`: 23 passed
- `npm install`: passed
- `npm run build`: passed
- `/api/health`: returned `{"status":"ok","version":"0.4.0"}`
- Mock task creation worked
- Improvement generation returned suggestions
- Suggestion approval created human feedback and revision records
- Improvement history was written
- Evaluation comparison was written
- Suggestion rejection was persisted

## Limitations

- Suggestion generation is still rule-based.
- There is no visual artifact diff view yet.
- There is no advanced LLM-assisted suggestion refinement yet.
- Evaluation comparison is still simple.
- Suggestion quality is good enough for workflow validation, but not yet deeply intelligent.

## Recommended Next Version

V0.5 should focus on diff-aware review and smarter evaluation quality.

Recommended areas:

- Artifact diff viewer
- More useful evaluation rubric
- Revision effectiveness report
- Optional LLM-assisted suggestion refinement
- Better frontend review experience for before/after comparison
