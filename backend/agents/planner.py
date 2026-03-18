"""Planner agent — explores app via MCP tools, produces specs/*.md.

Uses ReAct loop: LLM decides which browser tools to call,
observes results, decides next action, until it has enough
context to write the test plan.
"""

from agents.base import BaseAgent
from prompts import get_planner_prompt


class PlannerAgent(BaseAgent):
    agent_name = "planner"

    def _get_system_prompt(self) -> str:
        return get_planner_prompt()