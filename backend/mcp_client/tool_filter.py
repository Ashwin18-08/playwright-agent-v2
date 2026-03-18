"""Filters ~44 MCP tools down to the subset each agent needs.

Based on the official Playwright agent definitions from:
  npx playwright init-agents --loop=claude

Each agent only gets the tools it actually uses — saves tokens
and prevents agents from calling tools they shouldn't.
"""

# ── Planner tools (explore app + run seed test) ─────────────
PLANNER_TOOLS = {
    # Browser exploration
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_select_option",
    "browser_hover",
    "browser_press_key",
    "browser_snapshot",
    "browser_screenshot",
    "browser_wait",
    "browser_scroll_down",
    "browser_scroll_up",
    "browser_go_back",
    "browser_go_forward",
    "browser_tab_new",
    "browser_tab_select",
    "browser_tab_close",
    "browser_drag",
    "browser_file_upload",
    # Test tools (run seed test to set up page)
    "test_run",
    # Planner-specific
    "planner_setup_page",
}


# ── Generator tools (write tests + verify locators) ─────────
GENERATOR_TOOLS = {
    # Browser (verify selectors live)
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_select_option",
    "browser_hover",
    "browser_press_key",
    "browser_snapshot",
    "browser_screenshot",
    "browser_wait",
    "browser_scroll_down",
    "browser_scroll_up",
    "browser_go_back",
    "browser_go_forward",
    # Locator generation
    "browser_generate_locator",
    # Test tools (run generated tests to verify)
    "test_run",
    "test_list",
    # Generator-specific
    "generator_setup_page",
}


# ── Healer tools (debug + fix failing tests) ────────────────
HEALER_TOOLS = {
    # Debugging
    "browser_console_messages",
    "browser_evaluate",
    "browser_generate_locator",
    "browser_network_requests",
    "browser_snapshot",
    "browser_screenshot",
    # Test execution
    "test_debug",
    "test_list",
    "test_run",
}


def get_tools_for_agent(
    all_tools: list[dict],
    agent_name: str,
) -> list[dict]:
    """Filter the full MCP tool list to only what this agent needs.

    Args:
        all_tools: all ~44 tools from PlaywrightTestMCP.list_tools()
        agent_name: "planner" | "generator" | "healer"

    Returns:
        Filtered list of tool dicts (only matching names)
    """
    tool_set = {
        "planner": PLANNER_TOOLS,
        "generator": GENERATOR_TOOLS,
        "healer": HEALER_TOOLS,
    }.get(agent_name, set())

    filtered = [t for t in all_tools if t["name"] in tool_set]

    return filtered


def tools_to_openai_functions(tools: list[dict]) -> list[dict]:
    """Convert MCP tool dicts to OpenAI function-calling format
    for use with llm.bind_tools()."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("input_schema", {
                    "type": "object", "properties": {}
                }),
            },
        }
        for t in tools
    ]