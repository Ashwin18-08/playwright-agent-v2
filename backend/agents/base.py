"""BaseAgent — ReAct loop powered by LangGraph.

Each agent (Planner, Generator, Healer) inherits from this.
The LLM has tools bound via .bind_tools() and runs in a
reason → act → observe loop until it decides to stop.

Key difference from our old code:
- OLD: custom Dispatcher + Executor + MCP Healer (5 nodes)
- NEW: one ReAct node that lets the LLM call MCP tools directly
"""

from __future__ import annotations
import json
from typing import Any, AsyncGenerator
from dataclasses import dataclass, field

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, ToolMessage
)

from mcp_client.server import get_mcp_client
from mcp_client.tool_filter import get_tools_for_agent, tools_to_openai_functions
from config import get_settings
from utils.logger import log


@dataclass
class AgentEvent:
    """A single event emitted during agent execution."""
    kind: str               # "thinking", "tool_call", "tool_result", "output", "error"
    data: dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    """ReAct agent that calls MCP tools via Azure OpenAI function calling.

    Usage:
        agent = PlannerAgent()
        async for event in agent.run("Explore the todo app", max_iter=25):
            print(event)
    """

    agent_name: str = "base"        # override in subclass
    prompt_loader: Any = None       # override: callable returning prompt string

    def __init__(self) -> None:
        self._llm: AzureChatOpenAI | None = None
        self._tools: list[dict] | None = None
        self._openai_tools: list[dict] | None = None

    async def _setup(self) -> None:
        """Lazy init — load tools and bind to LLM."""
        if self._llm is not None:
            return

        s = get_settings()
        client = await get_mcp_client()
        all_tools = await client.list_tools()

        # Filter to only this agent's tools
        self._tools = get_tools_for_agent(all_tools, self.agent_name)
        self._openai_tools = tools_to_openai_functions(self._tools)

        log.info(f"{self.agent_name}.setup",
                 total_tools=len(all_tools),
                 filtered_tools=len(self._tools),
                 tool_names=[t["name"] for t in self._tools])

        # Create LLM with tools bound
        base_llm = AzureChatOpenAI(
            azure_deployment=s.azure_openai_deployment,
            azure_endpoint=s.azure_openai_endpoint,
            api_key=s.azure_openai_api_key,
            api_version=s.azure_openai_api_version,
            temperature=0,
        )
        self._llm = base_llm.bind_tools(self._openai_tools)

    def _get_system_prompt(self) -> str:
        """Override in subclass to return the agent's system prompt."""
        raise NotImplementedError

    async def run(
        self,
        user_prompt: str,
        max_iterations: int | None = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Execute the ReAct loop.

        The LLM reasons, picks tool(s) to call, we execute them via MCP,
        feed results back, and repeat until the LLM responds with text
        (no more tool calls) or we hit max_iterations.

        Yields AgentEvent at each step for real-time streaming.
        """
        await self._setup()
        assert self._llm is not None

        s = get_settings()
        max_iter = max_iterations or s.max_iterations
        client = await get_mcp_client()

        # Build initial messages
        messages: list = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_prompt),
        ]

        yield AgentEvent("started", {
            "agent": self.agent_name,
            "tools_count": len(self._tools or []),
            "tool_names": [t["name"] for t in (self._tools or [])],
        })

        # Track recent tool calls to detect loops
        recent_calls: list[str] = []
        LOOP_WINDOW = 5       # check last N calls
        LOOP_THRESHOLD = 3    # if same call appears this many times, force stop

        for iteration in range(1, max_iter + 1):
            log.info(f"{self.agent_name}.iteration", i=iteration)

            yield AgentEvent("thinking", {
                "agent": self.agent_name,
                "iteration": iteration,
            })

            # ── Nudge LLM to finish when approaching limit ──
            if iteration == max_iter - 3:
                messages.append(HumanMessage(
                    content=(
                        "IMPORTANT: You are running low on iterations. "
                        "Finish your exploration and respond with your final "
                        "text output within the next 2-3 iterations. "
                        "Do NOT call more tools unless absolutely necessary."
                    )
                ))

            # ── LLM call ─────────────────────────────────
            response: AIMessage = await self._llm.ainvoke(messages)
            messages.append(response)

            # ── Check if LLM wants to call tools ─────────
            tool_calls = response.tool_calls or []

            if not tool_calls:
                # LLM responded with text — done reasoning
                text = response.content or ""
                yield AgentEvent("output", {
                    "agent": self.agent_name,
                    "text": text,
                    "iteration": iteration,
                })
                log.info(f"{self.agent_name}.done",
                         iterations=iteration,
                         output_length=len(text))
                return

            # ── Execute each tool call via MCP ───────────
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("args", {})
                tool_id = tc.get("id", "")

                # ── Loop detection ───────────────────────
                call_sig = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
                recent_calls.append(call_sig)
                if len(recent_calls) > LOOP_WINDOW:
                    recent_calls.pop(0)

                # Count duplicates in the window
                dupes = sum(1 for c in recent_calls if c == call_sig)
                if dupes >= LOOP_THRESHOLD:
                    log.warning(f"{self.agent_name}.loop_detected",
                                tool=tool_name, dupes=dupes)
                    yield AgentEvent("loop_detected", {
                        "agent": self.agent_name,
                        "tool": tool_name,
                        "message": f"Tool {tool_name} called {dupes} times with same args — forcing stop. Respond with your output now.",
                    })
                    # Inject a message telling the LLM to stop
                    messages.append(ToolMessage(
                        content=(
                            f"STOP: You have called {tool_name} with the same arguments "
                            f"{dupes} times. This is a loop. Do NOT call any more tools. "
                            f"Instead, respond with your final text output NOW."
                        ),
                        tool_call_id=tool_id,
                    ))
                    continue  # skip executing, force LLM to respond

                yield AgentEvent("tool_call", {
                    "agent": self.agent_name,
                    "iteration": iteration,
                    "tool": tool_name,
                    "args": tool_args,
                })

                # Call the actual MCP tool
                result = await client.call_tool(tool_name, tool_args)

                # Format result as text for the LLM
                if result.get("success"):
                    result_text = "\n".join(
                        blk.get("text", blk.get("raw", ""))
                        for blk in result.get("content", [])
                        if blk.get("type") == "text"
                    )
                    if not result_text:
                        result_text = "Tool executed successfully (no text output)"
                else:
                    result_text = f"ERROR: {result.get('error', 'unknown error')}"

                yield AgentEvent("tool_result", {
                    "agent": self.agent_name,
                    "iteration": iteration,
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result_preview": result_text[:500],
                })

                # Feed result back to LLM as ToolMessage
                messages.append(ToolMessage(
                    content=result_text,
                    tool_call_id=tool_id,
                ))

            # Loop continues — LLM will reason about the results
            # and decide what to do next

        # Hit max iterations
        yield AgentEvent("max_iterations", {
            "agent": self.agent_name,
            "iterations": max_iter,
        })
        log.warning(f"{self.agent_name}.max_iterations", max=max_iter)