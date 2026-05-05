from backend.agents.base_agent import AgentContext, BaseAgent


class ReviewerAgent(BaseAgent):
    name = "ReviewerAgent"
    role = "Design reviewer"
    responsibilities = ["Review all design artifacts with a concrete checklist and scores."]
    input_artifacts = ["prd.md", "architecture.md", "frontend_plan.md", "api_design.md", "test_plan.md"]
    output_artifact = "review_report.md"
    prompt_file = "reviewer_agent.md"

    def run(self, context: AgentContext) -> str:
        context.event_bus.emit(
            from_agent="ManagerAgent",
            to_agent=self.name,
            type="review_request",
            content="Review the complete artifact set.",
            artifact_refs=self.input_artifacts,
            status="sent",
        )
        output = super().run(context)
        context.event_bus.emit(
            from_agent=self.name,
            to_agent="ManagerAgent",
            type="review_result",
            content="Review report is ready.",
            artifact_refs=[self.output_artifact],
            status="succeeded",
        )
        return output
