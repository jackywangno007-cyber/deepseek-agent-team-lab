from backend.agents.base_agent import BaseAgent


class ProductAgent(BaseAgent):
    name = "ProductAgent"
    role = "Product requirements specialist"
    responsibilities = ["Convert the task input into a practical MVP product requirements document."]
    input_artifacts = ["task_input.md"]
    output_artifact = "prd.md"
    prompt_file = "product_agent.md"
