"""Combined pipeline: Planner → Generator → Healer.

Key: after the Generator outputs test code as text, we parse
the file blocks and write them to disk in the Playwright project
so the Healer can actually run them.
"""

from __future__ import annotations
import os
import re
from typing import AsyncGenerator

from agents import PlannerAgent, GeneratorAgent, HealerAgent
from agents.base import AgentEvent
from config import get_settings
from utils.logger import log


def _write_generated_files(text: str) -> list[dict]:
    """Parse Generator output for file blocks and write to disk.

    The Generator outputs files like:
        ### FILE: tests/adding-todos.spec.ts
        ```typescript
        import { test } from '@playwright/test';
        ...
        ```

    Or without fences:
        ### FILE: tests/adding-todos.spec.ts
        import { test } from '@playwright/test';
        ...
        ### FILE: tests/next-file.spec.ts

    We extract each file and write it to the Playwright project.
    """
    s = get_settings()
    project_dir = os.path.abspath(s.playwright_project_path)
    written: list[dict] = []

    # Strategy 1: split on ### FILE: headers
    parts = re.split(r'###\s*FILE:\s*', text)

    for part in parts[1:]:  # skip everything before first ### FILE:
        lines = part.strip().splitlines()
        if not lines:
            continue

        # First line is the filename
        filename = lines[0].strip().rstrip(":")
        # Remove backtick fences if present
        content_lines = lines[1:]
        content = "\n".join(content_lines)

        # Strip ```typescript ... ``` wrapper
        content = re.sub(r'^```(?:typescript|ts|javascript|js)?\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        content = content.strip()

        if not content or not filename:
            continue

        # Write to disk
        filepath = os.path.join(project_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content + "\n")

        written.append({"filename": filename, "length": len(content)})
        log.info("pipeline.wrote_file", filename=filename, length=len(content))

    # Strategy 2: if no ### FILE: found, look for a single code block
    if not written:
        code_match = re.search(r'```(?:typescript|ts)\s*\n(.*?)```', text, re.DOTALL)
        if code_match:
            content = code_match.group(1).strip()
            filename = "tests/generated.spec.ts"
            filepath = os.path.join(project_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            written.append({"filename": filename, "length": len(content)})
            log.info("pipeline.wrote_fallback_file", filename=filename)

    return written


def _write_spec_file(text: str) -> str:
    """Write the Planner's markdown output to specs/test-plan.md."""
    s = get_settings()
    project_dir = os.path.abspath(s.playwright_project_path)
    specs_dir = os.path.join(project_dir, "specs")
    os.makedirs(specs_dir, exist_ok=True)

    filepath = os.path.join(specs_dir, "test-plan.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    log.info("pipeline.wrote_spec", filename="specs/test-plan.md", length=len(text))
    return filepath


async def run_pipeline(
    user_goal: str,
    target_url: str,
    max_iterations: int = 25,
) -> AsyncGenerator[AgentEvent, None]:

    # ─── Phase 1: Planner ────────────────────────────────────
    yield AgentEvent("pipeline_phase", {
        "phase": "planner",
        "message": "Starting Planner — exploring app and writing test plan...",
    })

    planner = PlannerAgent()
    planner_prompt = (
        f"Explore the application at {target_url} and create a test plan.\n\n"
        f"Goal: {user_goal}\n\n"
        f"Start by calling planner_setup_page with no arguments to set up, "
        f"then navigate to {target_url}. Explore the app and produce a "
        f"markdown test plan."
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

    # Write spec to disk
    _write_spec_file(spec_markdown)

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
        f"Start by calling generator_setup_page with no arguments, "
        f"then navigate to {target_url} and verify a few key locators. "
        f"Output the test files using ### FILE: headers."
    )

    generator_output = ""
    async for event in generator.run(generator_prompt, max_iterations):
        yield event
        if event.kind == "output":
            generator_output = event.data.get("text", "")

    if not generator_output:
        yield AgentEvent("pipeline_error", {
            "phase": "generator",
            "message": "Generator produced no output",
        })
        return

    # Write generated test files to disk
    written_files = _write_generated_files(generator_output)

    yield AgentEvent("pipeline_artifact", {
        "phase": "generator",
        "artifact_type": "tests",
        "content": generator_output,
        "files_written": written_files,
    })

    if not written_files:
        yield AgentEvent("pipeline_error", {
            "phase": "generator",
            "message": "Generator output could not be parsed into files. "
                       "Check the output format.",
        })
        return

    yield AgentEvent("pipeline_phase", {
        "phase": "files_written",
        "message": f"Wrote {len(written_files)} test file(s) to disk: "
                   + ", ".join(f["filename"] for f in written_files),
    })

    # ─── Phase 3: Healer ─────────────────────────────────────
    yield AgentEvent("pipeline_phase", {
        "phase": "healer",
        "message": "Starting Healer — running tests and fixing failures...",
    })

    healer = HealerAgent()
    healer_prompt = (
        f"Run all Playwright tests with test_run (no projects argument). "
        f"If any fail, debug them with test_debug, investigate the root "
        f"cause, fix the code, and re-run until all tests pass.\n\n"
        f"Target URL: {target_url}\n\n"
        f"IMPORTANT: Call test_run with empty arguments {{}} — do NOT "
        f"specify a project name."
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