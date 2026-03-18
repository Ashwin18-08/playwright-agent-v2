"""Generator agent — takes spec markdown, produces tests/*.spec.ts.

Uses ReAct loop: LLM reads the spec, verifies locators with
browser tools, writes test code, runs tests to verify.
"""

from agents.base import BaseAgent
from prompts import get_generator_prompt


class GeneratorAgent(BaseAgent):
    agent_name = "generator"

    def _get_system_prompt(self) -> str:
        return get_generator_prompt()