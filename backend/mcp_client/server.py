"""Spawns the Playwright TEST MCP server via stdio.

This is NOT @playwright/mcp (19 browser tools).
This is `npx playwright run-test-mcp-server` (~44 tools)
which includes test_run, test_debug, test_list,
browser_generate_locator, planner_setup_page, etc.
"""

from __future__ import annotations
import sys, os, shutil
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from utils.logger import log
from config import get_settings

IS_WINDOWS = sys.platform == "win32"


def _find_npx() -> str:
    if IS_WINDOWS:
        found = shutil.which("npx.cmd") or shutil.which("npx.exe")
        return found or "npx.cmd"
    return "npx"


def _ensure_pw_project(cwd: str, npx: str) -> None:
    """Auto-create minimal Playwright project if it doesn't exist.
    Only needs package.json + @playwright/test + playwright.config.ts.
    Everything else (specs/, tests/, seed.spec.ts) is created by the
    agents through MCP tools — we don't touch those.
    """
    os.makedirs(cwd, exist_ok=True)

    pkg = os.path.join(cwd, "package.json")
    if not os.path.exists(pkg):
        log.info("mcp.setup", msg="Creating package.json")
        with open(pkg, "w") as f:
            f.write('{"devDependencies":{"@playwright/test":"latest"}}')

    node_modules = os.path.join(cwd, "node_modules")
    if not os.path.exists(node_modules):
        log.info("mcp.setup", msg="Running npm install...")
        npm = shutil.which("npm.cmd" if IS_WINDOWS else "npm") or ("npm.cmd" if IS_WINDOWS else "npm")
        import subprocess
        subprocess.run([npm, "install"], cwd=cwd, capture_output=True)
        log.info("mcp.setup", msg="Installing chromium...")
        subprocess.run([npx, "playwright", "install", "chromium"], cwd=cwd, capture_output=True)

    config = os.path.join(cwd, "playwright.config.ts")
    if not os.path.exists(config):
        log.info("mcp.setup", msg="Creating playwright.config.ts")
        with open(config, "w") as f:
            f.write(
                "import { defineConfig } from '@playwright/test';\n"
                "export default defineConfig({\n"
                "  testDir: './tests',\n"
                "  use: { headless: true },\n"
                "});\n"
            )


class PlaywrightTestMCP:
    """Manages the Playwright Test MCP server child process."""

    def __init__(self) -> None:
        self._session: ClientSession | None = None
        self._cm: Any = None
        self._all_tools: list[dict] | None = None

    async def connect(self) -> None:
        s = get_settings()
        npx = _find_npx()

        cwd = os.path.abspath(s.playwright_project_path)

        # Auto-setup: ensure minimal Playwright project exists
        _ensure_pw_project(cwd, npx)

        log.info("mcp.spawning",
                 command=f"{npx} playwright run-test-mcp-server",
                 cwd=cwd)

        params = StdioServerParameters(
            command=npx,
            args=["playwright", "run-test-mcp-server"],
            env={**os.environ, "NODE_NO_WARNINGS": "1"},
            cwd=cwd,
        )

        self._cm = stdio_client(params)
        rd, wr = await self._cm.__aenter__()

        self._session = ClientSession(rd, wr)
        await self._session.__aenter__()
        await self._session.initialize()

        log.info("mcp.connected")

    async def disconnect(self) -> None:
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._cm:
            await self._cm.__aexit__(None, None, None)
        log.info("mcp.disconnected")

    async def list_tools(self) -> list[dict]:
        """Returns ALL tools from the Playwright Test MCP server (~44)."""
        if self._all_tools:
            return self._all_tools
        assert self._session
        result = await self._session.list_tools()
        self._all_tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in result.tools
        ]
        log.info("mcp.tools_listed", count=len(self._all_tools),
                 names=[t["name"] for t in self._all_tools])
        return self._all_tools

    async def call_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call any MCP tool by name."""
        assert self._session
        log.info("mcp.call", tool=name, args_keys=list(args.keys()))

        try:
            result = await self._session.call_tool(name, args)
            output: dict[str, Any] = {"success": True, "content": []}

            for blk in result.content:
                if blk.type == "text":
                    output["content"].append({"type": "text", "text": blk.text})
                elif blk.type == "image":
                    output["content"].append({
                        "type": "image", "data": blk.data,
                        "mimeType": blk.mimeType,
                    })
                else:
                    output["content"].append({"type": blk.type, "raw": str(blk)})

            log.info("mcp.call.ok", tool=name)
            return output

        except Exception as exc:
            log.error("mcp.call.fail", tool=name, err=str(exc))
            return {"success": False, "error": str(exc), "content": []}


# ── Singleton ────────────────────────────────────────────────
_client: PlaywrightTestMCP | None = None


async def get_mcp_client() -> PlaywrightTestMCP:
    global _client
    if _client is None:
        _client = PlaywrightTestMCP()
        await _client.connect()
    return _client