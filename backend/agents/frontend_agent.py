from backend.agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):
    name = "FrontendAgent"
    role = "Frontend planning specialist"
    responsibilities = ["Define pages, components, interaction flows, and API dependencies."]
    input_artifacts = ["prd.md", "architecture.md"]
    output_artifact = "frontend_plan.md"
    prompt_file = "frontend_agent.md"
