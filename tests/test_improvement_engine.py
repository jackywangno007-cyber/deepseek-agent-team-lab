from backend.core.improvement_engine import ImprovementEngine


def test_improvement_engine_generates_mapped_suggestions() -> None:
    review = """# Review Report

## Requirement Completeness Score
7/10

## Frontend-Backend Consistency Score
6/10

## Found Issues
- API design does not cover course withdrawal.
- The frontend plan should name exact table filters.

## Suggested Revision Items
- Add acceptance criteria for permission-related failures.
"""
    suggestions = ImprovementEngine().generate(
        task_id="task_test",
        review_report=review,
        evaluation={"passed": True},
        now=lambda: "2026-05-06T15:30:00",
        id_factory=lambda prefix: f"{prefix}_fixed",
    )

    assert suggestions
    assert all(suggestion["status"] == "PENDING" for suggestion in suggestions)
    assert all(suggestion["responsible_agent"].endswith("Agent") for suggestion in suggestions)
    assert all(suggestion["target_artifact"].endswith(".md") for suggestion in suggestions)
    assert any(suggestion["responsible_agent"] == "BackendAgent" for suggestion in suggestions)
    assert any(suggestion["responsible_agent"] == "TestAgent" for suggestion in suggestions)
