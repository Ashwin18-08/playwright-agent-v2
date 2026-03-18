"""aiohttp server — 4 WebSocket endpoints.

/ws/planner   — run Planner alone
/ws/generator — run Generator alone
/ws/healer    — run Healer alone
/ws/pipeline  — run all 3 in sequence
"""

from __future__ import annotations
import sys, json
from aiohttp import web

from config import get_settings
from agents import PlannerAgent, GeneratorAgent, HealerAgent
from agents.base import AgentEvent
from graph.pipeline import run_pipeline
from mcp_client.server import get_mcp_client
from utils.logger import setup_logging, log


# ─── Generic agent WebSocket runner ──────────────────────────
async def _run_agent_ws(ws: web.WebSocketResponse, agent, user_prompt: str, max_iter: int):
    """Runs any BaseAgent and streams events over WebSocket."""
    try:
        async for event in agent.run(user_prompt, max_iter):
            await ws.send_json({"kind": event.kind, **event.data})
        await ws.send_json({"kind": "done"})
    except Exception as exc:
        log.error("agent.error", err=str(exc))
        if not ws.closed:
            await ws.send_json({"kind": "error", "message": str(exc)})


# ─── /ws/planner ─────────────────────────────────────────────
async def ws_planner(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    msg = await ws.receive_json()

    url = msg.get("url", "")
    goal = msg.get("goal", "")
    max_iter = msg.get("max_iterations", get_settings().max_iterations)

    prompt = (
        f"Explore the application at {url} and create a test plan.\n\n"
        f"Goal: {goal}\n\n"
        f"Start by navigating to {url}, take a snapshot, then explore "
        f"all features relevant to the goal. When done, output the test plan "
        f"as structured markdown."
    )

    await _run_agent_ws(ws, PlannerAgent(), prompt, max_iter)
    return ws


# ─── /ws/generator ───────────────────────────────────────────
async def ws_generator(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    msg = await ws.receive_json()

    url = msg.get("url", "")
    spec = msg.get("spec", "")
    max_iter = msg.get("max_iterations", get_settings().max_iterations)

    prompt = (
        f"Generate Playwright tests from the following test plan.\n\n"
        f"## Test plan\n\n{spec}\n\n"
        f"## Target URL\n{url}\n\n"
        f"Start by calling generator_setup_page with no arguments, "
        f"then navigate to {url} and verify a few key locators. "
        f"Output the test files using ### FILE: headers."
    )

    generator_output = ""
    try:
        agent = GeneratorAgent()
        async for event in agent.run(prompt, max_iter):
            await ws.send_json({"kind": event.kind, **event.data})
            if event.kind == "output":
                generator_output = event.data.get("text", "")

        # Write files to disk
        if generator_output:
            from graph.pipeline import _write_generated_files
            written = _write_generated_files(generator_output)
            await ws.send_json({
                "kind": "files_written",
                "files": written,
                "message": f"Wrote {len(written)} file(s) to disk",
            })

        await ws.send_json({"kind": "done"})
    except Exception as exc:
        log.error("generator.error", err=str(exc))
        if not ws.closed:
            await ws.send_json({"kind": "error", "message": str(exc)})

    return ws


# ─── /ws/healer ──────────────────────────────────────────────
async def ws_healer(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    msg = await ws.receive_json()

    url = msg.get("url", "")
    test_file = msg.get("test_file", "")
    max_iter = msg.get("max_iterations", get_settings().max_iterations)

    prompt = (
        f"Run all Playwright tests with test_run. If any fail, debug them "
        f"with test_debug, investigate the root cause, fix the code, and "
        f"re-run until all tests pass.\n\n"
        f"Target URL: {url}"
    )
    if test_file:
        prompt += f"\n\nFocus on this test file: {test_file}"

    await _run_agent_ws(ws, HealerAgent(), prompt, max_iter)
    return ws


# ─── /ws/pipeline ────────────────────────────────────────────
async def ws_pipeline(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    msg = await ws.receive_json()

    url = msg.get("url", "")
    goal = msg.get("goal", "")
    max_iter = msg.get("max_iterations", get_settings().max_iterations)

    try:
        async for event in run_pipeline(goal, url, max_iter):
            await ws.send_json({"kind": event.kind, **event.data})
        await ws.send_json({"kind": "done"})
    except Exception as exc:
        log.error("pipeline.error", err=str(exc))
        if not ws.closed:
            await ws.send_json({"kind": "error", "message": str(exc)})

    return ws


# ─── Utility endpoints ───────────────────────────────────────
async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def list_tools(request: web.Request) -> web.Response:
    """Returns all ~44 tools with agent assignments."""
    from mcp_client.tool_filter import PLANNER_TOOLS, GENERATOR_TOOLS, HEALER_TOOLS
    client = await get_mcp_client()
    all_tools = await client.list_tools()

    enriched = []
    for t in all_tools:
        name = t["name"]
        enriched.append({
            "name": name,
            "description": t["description"],
            "agents": [
                a for a, s in [
                    ("planner", PLANNER_TOOLS),
                    ("generator", GENERATOR_TOOLS),
                    ("healer", HEALER_TOOLS),
                ]
                if name in s
            ],
        })

    return web.json_response({
        "total": len(enriched),
        "tools": enriched,
    })


# ─── CORS ────────────────────────────────────────────────────
@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# ─── Lifecycle ───────────────────────────────────────────────
async def on_startup(app: web.Application) -> None:
    setup_logging()
    log.info("server.starting", platform=sys.platform)
    client = await get_mcp_client()
    tools = await client.list_tools()
    log.info("server.ready", total_mcp_tools=len(tools))


async def on_shutdown(app: web.Application) -> None:
    from mcp_client.server import _client
    if _client:
        await _client.disconnect()
    log.info("server.stopped")


# ─── App factory ─────────────────────────────────────────────
def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Individual agent endpoints
    app.router.add_get("/ws/planner", ws_planner)
    app.router.add_get("/ws/generator", ws_generator)
    app.router.add_get("/ws/healer", ws_healer)
    app.router.add_get("/ws/pipeline", ws_pipeline)

    # Utility
    app.router.add_get("/api/health", health)
    app.router.add_get("/api/tools", list_tools)

    return app


if __name__ == "__main__":
    s = get_settings()
    print(f"\n  Playwright Agent v2")
    print(f"  ───────────────────────────────")
    print(f"  WebSocket endpoints:")
    print(f"    ws://localhost:{s.port}/ws/planner")
    print(f"    ws://localhost:{s.port}/ws/generator")
    print(f"    ws://localhost:{s.port}/ws/healer")
    print(f"    ws://localhost:{s.port}/ws/pipeline")
    print(f"  Utility:")
    print(f"    http://localhost:{s.port}/api/health")
    print(f"    http://localhost:{s.port}/api/tools")
    print()
    web.run_app(create_app(), host=s.host, port=s.port)