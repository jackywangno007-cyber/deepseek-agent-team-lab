from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.backend_agent import BackendAgent
from backend.agents.base_agent import AgentContext
from backend.agents.frontend_agent import FrontendAgent
from backend.agents.manager_agent import ManagerAgent
from backend.agents.product_agent import ProductAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.test_agent import TestAgent
from backend.config import Settings
from backend.core.evaluator import Evaluator
from backend.core.event_bus import EventBus
from backend.core.llm_client import LLMClient
from backend.core.workspace import TaskWorkspace
from backend.schemas.task import TaskRunResult


class Orchestrator:
    def __init__(self, settings: Settings, mock: bool = False, console: Console | None = None) -> None:
        self.settings = settings
        self.mock = mock
        self.console = console or Console()
        self.manager = ManagerAgent()
        self.agents = {
            "ProductAgent": ProductAgent(),
            "ArchitectAgent": ArchitectAgent(),
            "FrontendAgent": FrontendAgent(),
            "BackendAgent": BackendAgent(),
            "TestAgent": TestAgent(),
            "ReviewerAgent": ReviewerAgent(),
        }

    def run(self, user_task: str, workspace: TaskWorkspace | None = None, event_source: str = "CLI") -> TaskRunResult:
        workspace = workspace or TaskWorkspace()
        event_bus = EventBus(workspace, self.console)
        llm_client = LLMClient(self.settings, mock=self.mock)
        context = AgentContext(user_task=user_task, workspace=workspace, event_bus=event_bus, llm_client=llm_client)
        agent_status: dict[str, str] = {}

        workspace.write_artifact("task_input.md", user_task.strip() + "\n")
        event_bus.emit(
            from_agent=event_source,
            to_agent="ManagerAgent",
            type="task_created",
            content="Task workspace created.",
            artifact_refs=["task_input.md"],
            status="created",
        )

        plan = self.manager.create_task_plan(context)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            for step in plan.pipeline:
                self.manager.assign(context, step.agent, step.task, step.output_artifact)
                progress_task = progress.add_task(f"{step.agent}: {step.task}", total=None)
                try:
                    self.agents[step.agent].run(context)
                    agent_status[step.agent] = "succeeded"
                except Exception as exc:
                    agent_status[step.agent] = "failed"
                    event_bus.emit(
                        from_agent=step.agent,
                        to_agent="ManagerAgent",
                        type="error",
                        content=f"{type(exc).__name__}: {exc}",
                        artifact_refs=step.input_artifacts,
                        status="failed",
                    )
                    raise
                finally:
                    progress.remove_task(progress_task)

            progress_task = progress.add_task("ManagerAgent: final summary", total=None)
            try:
                self.manager.create_final_summary(context)
                agent_status["ManagerAgent"] = "succeeded"
            finally:
                progress.remove_task(progress_task)

        evaluation = Evaluator(workspace, event_bus).evaluate()
        review_excerpt = self._review_excerpt(workspace)
        return TaskRunResult(
            task_id=workspace.task_id,
            workspace_path=str(workspace.path),
            agent_status=agent_status,
            generated_artifacts=workspace.list_artifacts(),
            review_excerpt=review_excerpt,
            final_summary_path=str(workspace._safe_path("final_summary.md")),
            evaluation=evaluation,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def _review_excerpt(workspace: TaskWorkspace) -> str:
        if not workspace.artifact_exists("review_report.md"):
            return ""
        lines = [line.strip() for line in workspace.read_artifact("review_report.md").splitlines() if line.strip()]
        return " ".join(lines[:8])[:600]
