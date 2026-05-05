from pathlib import Path

import pytest

from backend.core.workspace import TaskWorkspace, WorkspaceError


def test_task_workspace_can_create_and_read_artifacts(tmp_path: Path) -> None:
    workspace = TaskWorkspace(root=tmp_path)
    workspace.write_artifact("prd.md", "# PRD\n")

    assert workspace.artifact_exists("prd.md")
    assert workspace.read_artifact("prd.md") == "# PRD\n"
    assert "prd.md" in workspace.list_artifacts()


def test_workspace_blocks_path_traversal(tmp_path: Path) -> None:
    workspace = TaskWorkspace(root=tmp_path)

    with pytest.raises(WorkspaceError):
        workspace.write_artifact("../escape.md", "nope")
