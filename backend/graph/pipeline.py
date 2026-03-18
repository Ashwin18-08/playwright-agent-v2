"""Combined pipeline: Planner → Generator → Healer.

Runs all 3 agents in sequence. Each agent's output feeds
into the next agent's input as a user prompt.

This is NOT a LangGraph state machine — it's a simple
async generator that runs each agent and yields events.
We use LangGraph inside each agent (the ReAct loop in base.py).
"""

from __future__ import annotations
from typing import Any, AsyncGenerator

from agents import PlannerAgent, GeneratorAgent, HealerAgent
from agents.base import AgentEvent
from utils.logger import log


async def run_pipeline(
    user_goal: str,
    target_url: str,
    max_iterations: int = 25,
) -> AsyncGenerator[AgentEvent, None]:
    """Run Planner → Generator → Healer in sequence.

    Each agent runs its full ReAct loop. The output text from
    one agent becomes the input prompt for the next.
    """

    # ─── Phase 1: Planner ────────────────────────────────────
    yield AgentEvent("pipeline_phase", {
        "phase": "planner",
        "message": "Starting Planner — exploring app and writing test plan...",
    })

    planner = PlannerAgent()
    planner_prompt = (
        f"Explore the application at {target_url} and create a test plan.\n\n"
        f"Goal: {user_goal}\n\n"
        f"Start by navigating to {target_url}, take a snapshot, then explore "
        f"all features relevant to the goal. When done, output the test plan "
        f"as structured markdown."
    )

    spec_markdown = ""
    async for event in planner.run(planner_prompt, max_iterations):
        yield event
        if event.kind == "output":
            spec_markdown = event.data.get("text", "")

    if not spec_markdown:
        yield AgentEvent("pipeline_error", {
            "phase": "planner",
            "message": "Planner produced no output",
        })
        return

    yield AgentEvent("pipeline_artifact", {
        "phase": "planner",
        "artifact_type": "spec",
        "filename": "specs/test-plan.md",
        "content": spec_markdown,
    })

    # ─── Phase 2: Generator ──────────────────────────────────
    yield AgentEvent("pipeline_phase", {
        "phase": "generator",
        "message": "Starting Generator — converting spec to .spec.ts files...",
    })

    generator = GeneratorAgent()
    generator_prompt = (
        f"Generate Playwright tests from the following test plan.\n\n"
        f"## Test plan\n\n{spec_markdown}\n\n"
        f"## Target URL\n{target_url}\n\n"
        f"Use the browser tools to verify locators are correct before "
        f"writing the test code. Run the tests with test_run to verify "
        f"they pass."
    )

    generator_output = ""
    async for event in generator.run(generator_prompt, max_iterations):
        yield event
        if event.kind == "output":
            generator_output = event.data.get("text", "")

    yield AgentEvent("pipeline_artifact", {
        "phase": "generator",
        "artifact_type": "tests",
        "content": generator_output,
    })

    # ─── Phase 3: Healer ─────────────────────────────────────
    yield AgentEvent("pipeline_phase", {
        "phase": "healer",
        "message": "Starting Healer — running tests and fixing failures...",
    })

    healer = HealerAgent()
    healer_prompt = (
        f"Run all Playwright tests with test_run. If any fail, debug them "
        f"with test_debug, investigate the root cause, fix the code, and "
        f"re-run until all tests pass.\n\n"
        f"Target URL: {target_url}"
    )

    healer_output = ""
    async for event in healer.run(healer_prompt, max_iterations):
        yield event
        if event.kind == "output":
            healer_output = event.data.get("text", "")

    yield AgentEvent("pipeline_artifact", {
        "phase": "healer",
        "artifact_type": "report",
        "content": healer_output,
    })

    yield AgentEvent("pipeline_done", {
        "message": "Pipeline complete: Planner → Generator → Healer",
    })