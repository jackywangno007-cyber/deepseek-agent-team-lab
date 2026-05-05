from backend.agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    name = "ArchitectAgent"
    role = "Software architecture planner"
    responsibilities = ["Turn product requirements into a bounded technical architecture."]
    input_artifacts = ["prd.md"]
    output_artifact = "architecture.md"
    prompt_file = "architect_agent.md"
