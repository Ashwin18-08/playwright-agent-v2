"""Pipeline state — used when running all 3 agents in sequence."""

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel


class PipelineState(BaseModel):
    """State for the combined Planner → Generator → Healer pipeline."""

    # Input
    user_goal: str = ""
    target_url: str = ""
    session_id: str = ""

    # Planner output
    spec_markdown: str = ""

    # Generator output (text summary — actual files are on disk via MCP)
    generator_output: str = ""

    # Healer output
    healer_output: str = ""

    # Flow
    current_agent: Literal["planner", "generator", "healer", "done"] = "planner"
    error: str = ""

    # Events collected from all agents
    events: list[dict[str, Any]] = []

    def add_event(self, kind: str, data: dict[str, Any]) -> None:
        self.events.append({"kind": kind, **data})