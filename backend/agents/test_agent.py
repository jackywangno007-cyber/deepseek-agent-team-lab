from backend.agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    name = "TestAgent"
    role = "Test strategy specialist"
    responsibilities = ["Translate design artifacts into a practical testing plan."]
    input_artifacts = ["prd.md", "architecture.md", "frontend_plan.md", "api_design.md"]
    output_artifact = "test_plan.md"
    prompt_file = "test_agent.md"
