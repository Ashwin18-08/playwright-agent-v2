"""Healer agent — runs tests, debugs failures, fixes code.

Uses ReAct loop: LLM runs tests, sees failures, uses debug
tools to investigate, fixes code, re-runs until passing.
"""

from agents.base import BaseAgent
from prompts import get_healer_prompt


class HealerAgent(BaseAgent):
    agent_name = "healer"

    def _get_system_prompt(self) -> str:
        return get_healer_prompt()