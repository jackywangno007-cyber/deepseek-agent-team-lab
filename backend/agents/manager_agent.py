from __future__ import annotations

import json

from backend.agents.base_agent import AgentContext
from backend.schemas.task import TaskPlan, TaskStep


class ManagerAgent:
    name = "ManagerAgent"

    def create_task_plan(self, context: AgentContext) -> TaskPlan:
        plan = TaskPlan(
            goal=context.user_task,
            pipeline=[
                TaskStep(
                    agent="ProductAgent",
                    task="Generate the product requirements document",
                    input_artifacts=["task_input.md"],
                    output_artifact="prd.md",
                ),
                TaskStep(
                    agent="ArchitectAgent",
                    task="Generate architecture from the PRD",
                    input_artifacts=["prd.md"],
                    output_artifact="architecture.md",
                ),
                TaskStep(
                    agent="FrontendAgent",
                    task="Plan frontend pages, components, and interactions",
                    input_artifacts=["prd.md", "architecture.md"],
                    output_artifact="frontend_plan.md",
                ),
                TaskStep(
                    agent="BackendAgent",
                    task="Design backend data models and API contracts",
                    input_artifacts=["prd.md", "architecture.md"],
                    output_artifact="api_design.md",
                ),
                TaskStep(
                    agent="TestAgent",
                    task="Generate the test strategy and test cases",
                    input_artifacts=["prd.md", "architecture.md", "frontend_plan.md", "api_design.md"],
                    output_artifact="test_plan.md",
                ),
                TaskStep(
                    agent="ReviewerAgent",
                    task="Review all artifacts and produce concrete quality feedback",
                    input_artifacts=[
                        "prd.md",
                        "architecture.md",
                        "frontend_plan.md",
                        "api_design.md",
                        "test_plan.md",
                    ],
                    output_artifact="review_report.md",
                ),
            ],
        )
        context.workspace.write_json("task_plan.json", plan.model_dump())
        context.event_bus.emit(
            from_agent=self.name,
            type="artifact_created",
            content="Created task_plan.json",
            artifact_refs=["task_plan.json"],
            status="created",
        )
        return plan

    def assign(self, context: AgentContext, agent_name: str, task: str, output_artifact: str) -> None:
        context.event_bus.emit(
            from_agent=self.name,
            to_agent=agent_name,
            type="task_assign",
            content=task,
            artifact_refs=[output_artifact],
            status="sent",
        )

    def create_final_summary(self, context: AgentContext) -> str:
        prompt = self._load_summary_prompt()
        artifact_names = [
            "prd.md",
            "architecture.md",
            "frontend_plan.md",
            "api_design.md",
            "test_plan.md",
            "review_report.md",
        ]
        artifacts = []
        for name in artifact_names:
            artifacts.append(f"Artifact: {name}\n\n{context.workspace.read_artifact(name)}")
        user_prompt = (
            f"Original user task:\n{context.user_task}\n\n"
            f"Artifacts:\n\n" + "\n\n---\n\n".join(artifacts) + "\n\nWrite final_summary.md."
        )
        summary = context.llm_client.complete(prompt, user_prompt)
        context.workspace.write_artifact("final_summary.md", summary)
        context.event_bus.emit(
            from_agent=self.name,
            type="final_summary",
            content="Created final_summary.md",
            artifact_refs=["final_summary.md"],
            status="succeeded",
        )
        return summary

    @staticmethod
    def _load_summary_prompt() -> str:
        from pathlib import Path

        return (Path(__file__).resolve().parents[1] / "prompts" / "manager_summary.md").read_text(encoding="utf-8")

    @staticmethod
    def plan_as_pretty_json(plan: TaskPlan) -> str:
        return json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)
