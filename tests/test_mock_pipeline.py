from pathlib import Path

from backend.config import load_settings
from backend.core.orchestrator import Orchestrator


def test_full_pipeline_runs_in_mock_mode(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    settings = load_settings()
    result = Orchestrator(settings=settings, mock=True).run("Design an MVP for a student course management system")

    required = {
        "task_input.md",
        "task_plan.json",
        "events.jsonl",
        "prd.md",
        "architecture.md",
        "frontend_plan.md",
        "api_design.md",
        "test_plan.md",
        "review_report.md",
        "final_summary.md",
        "evaluation.json",
    }
    assert required.issubset(set(result.generated_artifacts))
    assert result.evaluation["passed"] is True
