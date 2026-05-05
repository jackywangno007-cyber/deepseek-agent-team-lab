from __future__ import annotations

import re

from openai import OpenAI

from backend.config import Settings


class LLMClientError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings: Settings, mock: bool = False) -> None:
        self.settings = settings
        self.mock = mock or not settings.has_api_key
        self._client: OpenAI | None = None
        if not self.mock:
            self._client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if self.mock:
            return self._mock_complete(system_prompt, user_prompt)
        try:
            assert self._client is not None
            response = self._client.chat.completions.create(
                model=self.settings.deepseek_model,
                temperature=self.settings.agent_temperature,
                max_tokens=self.settings.agent_max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMClientError("DeepSeek API returned an empty response.")
            return content
        except Exception as exc:
            message = str(exc)
            api_key = self.settings.deepseek_api_key
            if api_key:
                message = message.replace(api_key, "[REDACTED_API_KEY]")
            raise LLMClientError(f"DeepSeek API call failed: {message}") from exc

    def _mock_complete(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n{user_prompt}".lower()
        title = self._extract_task_title(user_prompt)
        system = system_prompt.lower()
        if "revieweragent" in system or "review_report.md" in system:
            return self._mock_review(title)
        if "final_summary.md" in system or "final summary" in system:
            return self._mock_summary(title)
        if "productagent" in prompt or "product requirements" in prompt:
            return self._mock_prd(title)
        if "architectagent" in prompt or "architecture.md" in prompt:
            return self._mock_architecture(title)
        if "frontendagent" in prompt or "frontend_plan.md" in prompt:
            return self._mock_frontend(title)
        if "backendagent" in prompt or "api_design.md" in prompt:
            return self._mock_backend(title)
        if "testagent" in prompt or "test_plan.md" in prompt:
            return self._mock_tests(title)
        return self._mock_prd(title)

    @staticmethod
    def _extract_task_title(text: str) -> str:
        match = re.search(r"original user task:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        raw = match.group(1).strip().splitlines()[0] if match else "the requested software project"
        return raw[:120]

    def _mock_prd(self, title: str) -> str:
        return f"""# Product Requirements Document

## Project Background
This MVP explores: {title}. The goal is to validate the core workflow before expanding into advanced automation.

## Target Users
- Primary users who need a simple, reliable workflow.
- Administrators who configure records, permissions, and reporting.

## User Pain Points
- Current work is fragmented across documents and manual status tracking.
- Users need clear ownership, searchable records, and predictable outputs.

## MVP Scope
- Account-style role separation.
- Core create, read, update, and list workflows.
- Basic dashboard and exportable operational records.

## Core Features
- Guided task intake with required fields.
- Record management with status changes.
- Review step before final submission.
- Simple reporting for recent activity and unresolved items.

## Non-Functional Requirements
- Local-first development setup.
- Clear API boundaries.
- Audit-friendly logs for major actions.
- Tests for critical business rules.

## Out-of-Scope Items
- Native mobile apps.
- Payment processing.
- Complex AI automation.
- Enterprise SSO and multi-region deployment.
"""

    def _mock_architecture(self, title: str) -> str:
        return f"""# Architecture

## Recommended Tech Stack
- Frontend: React with TypeScript in a later version.
- Backend: FastAPI with Pydantic models.
- Storage: SQLite for early local development, PostgreSQL later.

## Module Breakdown
- Intake module for capturing user requirements.
- Domain module for records, roles, and status transitions.
- Reporting module for summaries and exports.
- Audit module for event logging.

## Data Flow
1. User submits a request.
2. Backend validates and persists domain entities.
3. Services apply business rules and emit audit events.
4. Frontend renders status and next actions.

## Core Entities
- User
- Role
- ProjectRecord
- Review
- AuditEvent

## System Boundaries
The system owns workflow state and audit history for {title}. It does not execute arbitrary shell commands or manage external infrastructure in V0.1.

## Risks
- Scope creep from reporting into full analytics.
- Permissions may become complex if roles are not defined early.
- Data model changes are likely after user testing.
"""

    def _mock_frontend(self, title: str) -> str:
        return f"""# Frontend Plan

## Page List
- Dashboard
- Record list
- Record detail
- Create or edit record
- Review queue

## Main Components
- Navigation shell
- Filterable table
- Status badge
- Record form
- Review decision panel

## User Interaction Flow
1. User opens dashboard and sees pending work.
2. User creates or edits a record.
3. Reviewer checks details and returns feedback or approves.
4. User sees final status and audit history.

## State Management Suggestions
- Keep server state behind query hooks in a later React version.
- Store only temporary form state in the browser.
- Use typed API clients generated from backend contracts when available.

## Backend API Dependencies
- Record CRUD endpoints.
- Review endpoints.
- Current user and role endpoint.
- Activity log endpoint.
"""

    def _mock_backend(self, title: str) -> str:
        return f"""# API Design

## Data Models
- User: id, name, email, role
- ProjectRecord: id, title, description, status, owner_id, created_at, updated_at
- Review: id, record_id, reviewer_id, decision, comments
- AuditEvent: id, actor_id, action, target_id, created_at

## API List
- `POST /records`
- `GET /records`
- `GET /records/{{id}}`
- `PATCH /records/{{id}}`
- `POST /records/{{id}}/reviews`
- `GET /records/{{id}}/events`

## Request and Response Examples
`POST /records` request:
```json
{{"title": "{title}", "description": "Initial MVP request"}}
```

`POST /records` response:
```json
{{"id": "rec_001", "status": "draft"}}
```

## Error Codes
- `400_INVALID_INPUT`
- `403_FORBIDDEN`
- `404_NOT_FOUND`
- `409_INVALID_STATUS_TRANSITION`

## Permission Boundaries
- Owners can edit draft records.
- Reviewers can approve or request changes.
- Admins can view all records and audit events.

## Future Extension Points
- Notification adapter.
- External identity provider.
- Analytics export pipeline.
"""

    def _mock_tests(self, title: str) -> str:
        return f"""# Test Plan

## Unit Test Suggestions
- Validate required fields for {title}.
- Verify status transition rules.
- Verify permission checks for owners, reviewers, and admins.

## API Test Suggestions
- Create, list, update, and retrieve records.
- Submit review decisions.
- Confirm error responses for invalid IDs and forbidden actions.

## E2E Test Suggestions
- User creates a record and reviewer approves it.
- Reviewer requests changes and user resubmits.

## Core Business Test Cases
- Draft records can be edited by owners.
- Approved records become read-only for normal users.
- Audit events are created for each state change.

## Edge Case and Error Scenario Test Cases
- Empty title.
- Duplicate submission.
- Invalid status transition.
- Missing reviewer permission.
"""

    def _mock_review(self, title: str) -> str:
        return f"""# Review Report

## Overall Score
8/10

## Requirement Completeness Score
8/10

## Architecture Consistency Score
8/10

## Frontend-Backend Consistency Score
7/10

## Test Coverage Score
8/10

## Checklist
- PRD includes users, pain points, scope, and out-of-scope items: pass.
- Architecture defines modules, entities, data flow, and boundaries: pass.
- Frontend references backend dependencies: pass with minor gaps.
- Backend API covers major MVP workflows: pass.
- Test plan covers unit, API, E2E, and edge scenarios: pass.

## Found Issues
- The reporting requirements for {title} need clearer metric definitions.
- The frontend plan should name exact table filters and form validation states.
- API examples should expand review decision payloads before implementation.

## Suggested Revision Items
- Define dashboard metrics in the PRD.
- Add exact request schemas for review endpoints.
- Add acceptance criteria for permission-related failures.

## Proceed Decision
Proceed to the next stage after addressing the revision items above.
"""

    def _mock_summary(self, title: str) -> str:
        return f"""# Final Summary

The V0.1 agent pipeline produced a complete artifact set for: {title}.

## Generated Artifacts
- `prd.md`
- `architecture.md`
- `frontend_plan.md`
- `api_design.md`
- `test_plan.md`
- `review_report.md`

## Key Outcome
The project is ready for a next implementation planning pass. The strongest next step is to refine dashboard metrics, review payloads, and permission acceptance criteria before coding.

## Recommended Next Action
Use the artifacts as the source of truth for a V0.2 FastAPI backend and keep all future agent outputs artifact-based.
"""
