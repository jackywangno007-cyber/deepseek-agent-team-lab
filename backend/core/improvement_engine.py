from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4


class ImprovementEngine:
    """Rule-based issue extraction for V0.4 improvement suggestions."""

    SCORE_RULES = [
        ("requirement completeness", "ProductAgent", "prd.md", "medium"),
        ("architecture consistency", "ArchitectAgent", "architecture.md", "medium"),
        ("frontend-backend consistency", "BackendAgent", "api_design.md", "medium"),
        ("test coverage", "TestAgent", "test_plan.md", "medium"),
    ]

    KEYWORD_RULES = [
        (("dashboard", "metric", "requirement", "scope"), "ProductAgent", "prd.md", "Define clearer product requirements and acceptance criteria."),
        (("architecture", "module", "boundary", "risk"), "ArchitectAgent", "architecture.md", "Clarify architecture modules, boundaries, data flow, and risks."),
        (("frontend", "component", "interaction", "state"), "FrontendAgent", "frontend_plan.md", "Clarify frontend pages, component behavior, and state flow."),
        (("api", "endpoint", "payload", "request", "schema", "backend"), "BackendAgent", "api_design.md", "Expand backend API design with request/response examples and error cases."),
        (("test", "coverage", "edge", "acceptance", "permission"), "TestAgent", "test_plan.md", "Add concrete test cases for edge cases, permissions, and business rules."),
        (("review", "score", "checklist"), "ReviewerAgent", "review_report.md", "Make the review more specific with checklist findings and actionable revision items."),
        (("summary", "next step", "handoff"), "ManagerAgent", "final_summary.md", "Clarify final summary decisions, risks, and next steps."),
    ]

    def generate(
        self,
        *,
        task_id: str,
        review_report: str,
        evaluation: dict[str, Any],
        now: Callable[[], str] | None = None,
        id_factory: Callable[[str], str] | None = None,
    ) -> list[dict[str, Any]]:
        now = now or self._now
        id_factory = id_factory or self._new_id
        suggestions: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for score_label, agent, artifact, severity in self.SCORE_RULES:
            score = self._extract_score(review_report, score_label)
            if score is not None and score < 8:
                issue = f"{score_label.title()} score is {score}/10."
                feedback = self._feedback_for(agent, artifact, issue)
                self._add_suggestion(suggestions, seen, task_id, issue, agent, artifact, feedback, severity, f"ReviewerAgent score for {score_label} is below 8.", "review_report.md", now, id_factory)

        for issue in self._extract_issue_lines(review_report):
            agent, artifact, base_feedback = self._map_issue(issue)
            self._add_suggestion(
                suggestions,
                seen,
                task_id,
                issue,
                agent,
                artifact,
                f"{base_feedback} Address this review finding concretely: {issue}",
                self._severity_for_issue(issue),
                "ReviewerAgent found a concrete issue or revision item.",
                "review_report.md",
                now,
                id_factory,
            )

        for key, value in evaluation.items():
            if isinstance(value, bool) and not value:
                agent, artifact, feedback = self._map_evaluation_key(key)
                issue = f"Evaluator check failed: {key}."
                self._add_suggestion(suggestions, seen, task_id, issue, agent, artifact, feedback, "high", "Rule-based evaluator reported an incomplete output.", "evaluation.json", now, id_factory)

        if not suggestions:
            issue = "Review and evaluation passed, but final handoff can be made more actionable."
            self._add_suggestion(
                suggestions,
                seen,
                task_id,
                issue,
                "ManagerAgent",
                "final_summary.md",
                "Improve the final summary with sharper risks, decisions, and implementation next steps.",
                "low",
                "No blocking issue was found, so suggest a lightweight handoff improvement.",
                "review_report.md",
                now,
                id_factory,
            )
        return suggestions

    def _add_suggestion(
        self,
        suggestions: list[dict[str, Any]],
        seen: set[tuple[str, str, str]],
        task_id: str,
        issue: str,
        agent: str,
        artifact: str,
        feedback: str,
        severity: str,
        reason: str,
        source: str,
        now: Callable[[], str],
        id_factory: Callable[[str], str],
    ) -> None:
        key = (agent, artifact, issue.lower())
        if key in seen:
            return
        seen.add(key)
        timestamp = now()
        suggestions.append(
            {
                "suggestion_id": id_factory("suggestion"),
                "task_id": task_id,
                "issue_summary": issue[:240],
                "responsible_agent": agent,
                "target_artifact": artifact,
                "proposed_feedback": feedback[:1000],
                "severity": severity,
                "reason": reason,
                "source": source,
                "status": "PENDING",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )

    @staticmethod
    def _extract_score(text: str, label: str) -> int | None:
        pattern = rf"{re.escape(label)}(?:\s+score)?[^\d]{{0,80}}(\d{{1,2}})\s*/\s*10"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _extract_issue_lines(text: str) -> list[str]:
        lines: list[str] = []
        in_relevant_section = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower.startswith("## "):
                in_relevant_section = any(marker in lower for marker in ("found issues", "suggested revision", "revision item"))
                continue
            if in_relevant_section and line.startswith("-"):
                cleaned = line.lstrip("- ").strip()
                if cleaned:
                    lines.append(cleaned)
        return lines

    def _map_issue(self, issue: str) -> tuple[str, str, str]:
        lower = issue.lower()
        for keywords, agent, artifact, feedback in self.KEYWORD_RULES:
            if any(keyword in lower for keyword in keywords):
                return agent, artifact, feedback
        return "ReviewerAgent", "review_report.md", "Make the review finding more concrete and assign it to the right artifact."

    @staticmethod
    def _map_evaluation_key(key: str) -> tuple[str, str, str]:
        lower = key.lower()
        if "review" in lower:
            return "ReviewerAgent", "review_report.md", "Revise the review report so it contains concrete scoring and findings."
        if "summary" in lower:
            return "ManagerAgent", "final_summary.md", "Regenerate the final summary with clear handoff guidance."
        return "ManagerAgent", "final_summary.md", f"Resolve the failed evaluator check `{key}` and summarize the correction."

    @staticmethod
    def _feedback_for(agent: str, artifact: str, issue: str) -> str:
        return f"Please revise {artifact} as {agent}. Address this evaluation concern: {issue}"

    @staticmethod
    def _severity_for_issue(issue: str) -> str:
        lower = issue.lower()
        if any(word in lower for word in ("missing", "invalid", "permission", "security", "error")):
            return "high"
        if any(word in lower for word in ("unclear", "expand", "define", "should")):
            return "medium"
        return "low"

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat()

    @staticmethod
    def _new_id(prefix: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{stamp}_{uuid4().hex[:6]}"
