from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.core.event_bus import EventBus
from backend.core.llm_client import LLMClient
from backend.core.workspace import TaskWorkspace


@dataclass
class AgentContext:
    user_task: str
    workspace: TaskWorkspace
    event_bus: EventBus
    llm_client: LLMClient


class BaseAgent:
    name = "BaseAgent"
    role = "Base role"
    responsibilities: list[str] = []
    input_artifacts: list[str] = []
    output_artifact: str = ""
    prompt_file: str = ""

    def run(self, context: AgentContext) -> str:
        context.event_bus.emit(
            from_agent=self.name,
            type="agent_started",
            content=f"Started {self.output_artifact}",
            artifact_refs=self.input_artifacts,
            status="running",
        )
        prompt = self._load_prompt()
        user_prompt = self._build_user_prompt(context)
        output = context.llm_client.complete(prompt, user_prompt)
        context.workspace.write_artifact(self.output_artifact, output)
        context.event_bus.emit(
            from_agent=self.name,
            type="artifact_created",
            content=f"Created {self.output_artifact}",
            artifact_refs=[self.output_artifact],
            status="created",
        )
        context.event_bus.emit(
            from_agent=self.name,
            type="agent_completed",
            content=f"Completed {self.output_artifact}",
            artifact_refs=[self.output_artifact],
            status="succeeded",
        )
        return output

    def _load_prompt(self) -> str:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / self.prompt_file
        return prompt_path.read_text(encoding="utf-8")

    def _build_user_prompt(self, context: AgentContext) -> str:
        sections = [f"Original user task:\n{context.user_task}\n"]
        for artifact in self.input_artifacts:
            content = context.workspace.read_artifact(artifact)
            sections.append(f"Input artifact: {artifact}\n\n{content}\n")
        sections.append(f"Write only the markdown content for `{self.output_artifact}`.")
        return "\n---\n".join(sections)
