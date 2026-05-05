from backend.agents.base_agent import BaseAgent


class BackendAgent(BaseAgent):
    name = "BackendAgent"
    role = "Backend API designer"
    responsibilities = ["Design data models, API contracts, errors, permissions, and extension points."]
    input_artifacts = ["prd.md", "architecture.md"]
    output_artifact = "api_design.md"
    prompt_file = "backend_agent.md"
