# Playwright Test Agents v2

Custom web UI for the **official Playwright Test Agents** (Planner, Generator, Healer) using **LangGraph ReAct loops**, **Azure OpenAI**, and the **Playwright Test MCP server** (`npx playwright run-test-mcp-server`).

Each agent uses real tool-calling (`llm.bind_tools()`) — the LLM natively decides which MCP tool to call at every step. No custom dispatcher, no manual JSON parsing.

---

## What's different from v1

| | v1 (old) | v2 (this) |
|---|---|---|
| MCP server | `@playwright/mcp` (19 tools) | `playwright run-test-mcp-server` (~44 tools) |
| Agent loop | Custom pipeline with Dispatcher | ReAct loop with `llm.bind_tools()` |
| Tool calling | LLM returns JSON text, we parse manually | LLM calls tools natively via function calling |
| Tool filtering | None (all tools given to all agents) | Per-agent filtering (Planner: 20, Generator: 17, Healer: 9) |
| UI | Single panel | 4 cards (each agent independent + combined) |
| Prompts | Custom prompts | Based on official Playwright agent definitions |

---

## Architecture

```
┌─────────────────── React Frontend ───────────────────┐
│  Planner Card    Generator Card    Healer Card        │
│  Pipeline Card (all 3 chained)                        │
│  Each card ↔ WebSocket ↔ /ws/{agent}                  │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────── aiohttp Backend ────────────────────┐
│  /ws/planner   →  PlannerAgent.run()                  │
│  /ws/generator →  GeneratorAgent.run()                │
│  /ws/healer    →  HealerAgent.run()                   │
│  /ws/pipeline  →  Planner → Generator → Healer        │
│                                                       │
│  Each agent inherits BaseAgent:                       │
│    1. Filter ~44 MCP tools to agent's subset          │
│    2. llm.bind_tools(filtered_tools)                  │
│    3. ReAct loop: LLM reasons → picks tool →          │
│       we call MCP → feed result back → repeat         │
└───────────────────────┬──────────────────────────────┘
                        │
┌──── Playwright Test MCP Server (stdio child) ────────┐
│  npx playwright run-test-mcp-server                   │
│  ~44 tools: browser_*, test_*, planner_*, generator_* │
│  Runs inside a Playwright project directory           │
│  Manages tests/, specs/, playwright.config.ts         │
└──────────────────────────────────────────────────────┘
```

---

## Tool filtering

The MCP server exposes ~44 tools. Each agent only gets the tools it needs:

### Planner (20 tools)
Browser exploration + `test_run` (for seed) + `planner_setup_page`

```
browser_navigate, browser_click, browser_type, browser_select_option,
browser_hover, browser_press_key, browser_snapshot, browser_screenshot,
browser_wait, browser_scroll_down, browser_scroll_up, browser_go_back,
browser_go_forward, browser_tab_new, browser_tab_select, browser_tab_close,
browser_drag, browser_file_upload, test_run, planner_setup_page
```

### Generator (17 tools)
Browser verification + locator generation + test running

```
browser_navigate, browser_click, browser_type, browser_select_option,
browser_hover, browser_press_key, browser_snapshot, browser_screenshot,
browser_wait, browser_scroll_down, browser_scroll_up, browser_go_back,
browser_go_forward, browser_generate_locator, test_run, test_list,
generator_setup_page
```

### Healer (9 tools)
Debugging + test execution only

```
browser_console_messages, browser_evaluate, browser_generate_locator,
browser_network_requests, browser_snapshot, browser_screenshot,
test_debug, test_list, test_run
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Azure OpenAI** with GPT-4o deployment
- **Playwright 1.56+** (`npm install -D @playwright/test`)
- Chromium browser: `npx playwright install chromium`

---

## Setup

### Step 1 — Clone

```bash
git clone <repo>
cd playwright-agent-v2
```

### Step 2 — Backend

```bash
cd backend
python3 -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### Step 3 — Playwright project

The MCP server needs a Playwright project directory to run in:

```bash
cd backend
mkdir pw_project && cd pw_project
npm init -y
npm install -D @playwright/test
npx playwright install chromium
```

Create `playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  use: { headless: true },
});
```

Create `tests/seed.spec.ts`:
```typescript
import { test } from '@playwright/test';
test('seed', async ({ page }) => {
  // add setup here
});
```

Create `specs/` directory:
```bash
mkdir specs
```

### Step 4 — Frontend

```bash
cd frontend
npm install
```

### Step 5 — Run

**Option A: one command**
```bash
chmod +x start.sh
./start.sh
```

**Option B: two terminals**
```bash
# Terminal 1
cd backend && source .venv/bin/activate && python main.py

# Terminal 2
cd frontend && npm run dev
```

### Step 6 — Open http://localhost:3000

---

## Usage

### Planner (standalone)
1. Enter URL + test goal
2. Click "Explore & Plan"
3. Watch the agent navigate the app, click around, take snapshots
4. Get a structured markdown test plan

### Generator (standalone)
1. Paste a markdown test plan (from Planner or hand-written)
2. Enter the target URL
3. Click "Generate tests"
4. Agent verifies locators live, writes .spec.ts files, runs them

### Healer (standalone)
1. Optionally enter a specific test file to focus on
2. Click "Run & heal"
3. Agent runs all tests, debugs failures, fixes code, re-runs

### Pipeline (all 3 chained)
1. Enter URL + test goal
2. Click "Run full pipeline"
3. Watch: Planner explores → Generator writes tests → Healer fixes
4. Phase indicators show which agent is currently active

---

## API reference

| Endpoint | Type | Input | Description |
|----------|------|-------|-------------|
| `/ws/planner` | WebSocket | `{url, goal}` | Run Planner agent |
| `/ws/generator` | WebSocket | `{url, spec}` | Run Generator agent |
| `/ws/healer` | WebSocket | `{url, test_file?}` | Run Healer agent |
| `/ws/pipeline` | WebSocket | `{url, goal}` | Run all 3 in sequence |
| `/api/tools` | GET | — | List all tools with agent assignments |
| `/api/health` | GET | — | Health check |

### WebSocket events

| Event | Data | When |
|-------|------|------|
| `started` | `{agent, tools_count, tool_names}` | Agent begins |
| `thinking` | `{agent, iteration}` | LLM reasoning |
| `tool_call` | `{agent, iteration, tool, args}` | LLM called a tool |
| `tool_result` | `{agent, iteration, tool, success, result_preview}` | Tool returned |
| `output` | `{agent, text}` | Agent final output |
| `max_iterations` | `{agent, iterations}` | Hit limit |
| `pipeline_phase` | `{phase, message}` | Pipeline switched agent |
| `pipeline_artifact` | `{phase, artifact_type, content}` | File produced |
| `pipeline_done` | `{message}` | Pipeline complete |
| `done` | — | Agent finished |
| `error` | `{message}` | Error occurred |

---

## How the ReAct loop works (base.py)

```python
# 1. Filter tools for this agent
tools = get_tools_for_agent(all_44_tools, "planner")  # → 20 tools

# 2. Bind to LLM (native function calling)
llm = AzureChatOpenAI(...).bind_tools(tools)

# 3. ReAct loop
messages = [SystemMessage(prompt), HumanMessage(user_input)]

for iteration in range(max_iterations):
    response = await llm.ainvoke(messages)

    if no tool_calls in response:
        # LLM responded with text — done
        yield AgentEvent("output", {text: response.content})
        return

    for tool_call in response.tool_calls:
        # LLM wants to call browser_click({ref: "e15"})
        result = await mcp_client.call_tool(tool_call.name, tool_call.args)
        messages.append(ToolMessage(result))
        yield AgentEvent("tool_result", {...})

    # Loop: LLM sees the result, decides what to do next
```

No Dispatcher, no custom JSON parsing, no MCP Healer. The LLM handles everything through native tool calling.

---

## Project structure

```
playwright-agent-v2/
├── backend/
│   ├── main.py                 # aiohttp + 4 WebSocket endpoints
│   ├── config.py               # .env settings
│   ├── mcp_client/
│   │   ├── server.py           # Spawns playwright run-test-mcp-server
│   │   └── tool_filter.py      # Filters ~44 tools per agent
│   ├── agents/
│   │   ├── base.py             # ReAct loop with bind_tools()
│   │   ├── planner.py          # 10 lines — inherits BaseAgent
│   │   ├── generator.py        # 10 lines — inherits BaseAgent
│   │   └── healer.py           # 10 lines — inherits BaseAgent
│   ├── prompts/
│   │   ├── planner.md          # Official-style prompt (editable)
│   │   ├── generator.md
│   │   └── healer.md
│   ├── graph/
│   │   ├── state.py            # Pipeline state
│   │   └── pipeline.py         # Planner → Generator → Healer
│   └── utils/
│       └── logger.py
├── frontend/
│   └── src/
│       ├── App.tsx             # 4-card grid
│       ├── components/
│       │   ├── AgentCard.tsx   # Reusable card wrapper
│       │   ├── PlannerCard.tsx
│       │   ├── GeneratorCard.tsx
│       │   ├── HealerCard.tsx
│       │   ├── PipelineCard.tsx
│       │   ├── EventStream.tsx # Live event log
│       │   ├── FileViewer.tsx  # Code viewer + copy
│       │   ├── ToolBadges.tsx  # Shows agent's tools
│       │   └── StatusIndicator.tsx
│       ├── hooks/useAgent.ts   # Shared WebSocket hook
│       ├── api/agent.ts        # WS + fetch helpers
│       └── types/index.ts
├── start.sh
└── README.md
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | — | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | — | Azure endpoint URL |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | API version |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` | Model deployment |
| `PLAYWRIGHT_PROJECT_PATH` | `./pw_project` | Playwright project dir |
| `MAX_ITERATIONS` | `25` | Max ReAct loop iterations per agent |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

---

## Extending

### Edit agent prompts
Modify `backend/prompts/planner.md`, `generator.md`, or `healer.md`. Changes take effect on next agent run — no restart needed.

### Add/remove tools per agent
Edit the tool sets in `backend/mcp_client/tool_filter.py`.

### Change LLM
Swap `AzureChatOpenAI` in `agents/base.py` for `ChatOpenAI`, `ChatAnthropic`, etc.

### Add a new agent
1. Create `prompts/your_agent.md`
2. Create `agents/your_agent.py` (inherit BaseAgent, set agent_name)
3. Add tool set in `tool_filter.py`
4. Add WebSocket endpoint in `main.py`
5. Create a card component in the frontend