from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend.config import load_settings
from backend.core.orchestrator import Orchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DeepSeek Agent Team Lab V0.1 pipeline.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--task", help="Project requirement text.")
    source.add_argument("--task-file", help="Path to a markdown file containing the project requirement.")
    parser.add_argument("--mock", action="store_true", help="Run without calling the DeepSeek API.")
    parser.add_argument("--model", help="Override DEEPSEEK_MODEL for this run.")
    return parser.parse_args()


def load_task(args: argparse.Namespace) -> str:
    if args.task:
        return args.task
    path = Path(args.task_file)
    return path.read_text(encoding="utf-8").strip()


def main() -> None:
    args = parse_args()
    console = Console()
    task = load_task(args)
    settings = load_settings(model_override=args.model)
    mock = args.mock or not settings.has_api_key
    mode_label = "mock" if mock else "real"

    console.print(Panel.fit(f"DeepSeek Agent Team Lab V0.1\nMode: {mode_label}\nModel: {settings.deepseek_model}"))
    result = Orchestrator(settings=settings, mock=mock, console=console).run(task)

    status_table = Table(title="Agent Results")
    status_table.add_column("Agent")
    status_table.add_column("Status")
    for agent, status in result.agent_status.items():
        style = "green" if status == "succeeded" else "red"
        status_table.add_row(agent, f"[{style}]{status}[/{style}]")
    console.print(status_table)

    artifact_table = Table(title="Generated Artifacts")
    artifact_table.add_column("File")
    for artifact in result.generated_artifacts:
        artifact_table.add_row(artifact)
    console.print(artifact_table)

    console.print(Panel(result.review_excerpt or "No review excerpt available.", title="Review Report Excerpt"))
    console.print(f"[bold]task_id:[/bold] {result.task_id}")
    console.print(f"[bold]workspace:[/bold] {result.workspace_path}")
    console.print(f"[bold]final_summary:[/bold] {result.final_summary_path}")
    console.print(f"[bold]evaluation passed:[/bold] {result.evaluation.get('passed')}")


if __name__ == "__main__":
    main()
