# Windows Setup — Step by Step

---

## Phase 1 — System prerequisites (one time)

### 1.1 Python 3.11+

```cmd
python --version
```

If not installed: download from https://www.python.org/downloads/
CHECK "Add to PATH" during install.

### 1.2 Node.js 18+

```cmd
node --version
npm --version
```

If not installed: download LTS from https://nodejs.org/

### 1.3 Playwright browsers

```cmd
npx playwright install chromium
```

---

## Phase 2 — Create the Playwright project

The MCP server needs a real Playwright project to run inside.

```cmd
cd backend
mkdir pw_project
cd pw_project

npm init -y
npm install -D @playwright/test
npx playwright install chromium
```

Create `pw_project\playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  use: { headless: true },
});
```

Create the folders:

```cmd
mkdir tests
mkdir specs
```

Create `pw_project\tests\seed.spec.ts`:

```typescript
import { test } from '@playwright/test';
test('seed', async ({ page }) => {
  // seed test — add setup logic here
});
```

Go back to backend:

```cmd
cd ..
```

---

## Phase 3 — Backend setup

```cmd
cd backend

python -m venv .venv
.venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```
AZURE_OPENAI_API_KEY=your-actual-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o
PLAYWRIGHT_PROJECT_PATH=./pw_project
MAX_ITERATIONS=25
```

---

## Phase 4 — Start backend

```cmd
cd backend
.venv\Scripts\activate
python main.py
```

You should see:

```
  Playwright Agent v2
  ───────────────────────────────
  WebSocket endpoints:
    ws://localhost:8000/ws/planner
    ws://localhost:8000/ws/generator
    ws://localhost:8000/ws/healer
    ws://localhost:8000/ws/pipeline
  Utility:
    http://localhost:8000/api/health
    http://localhost:8000/api/tools
```

Verify:

```cmd
curl http://localhost:8000/api/health
```

Should return `{"status":"ok"}`

```cmd
curl http://localhost:8000/api/tools
```

Should return the ~44 tools with agent assignments.

---

## Phase 5 — Start frontend (new CMD window)

Open a **second CMD/PowerShell window**:

```cmd
cd frontend
npm install
npm run dev
```

You should see:

```
  VITE v6.x.x  ready in 300ms

  ➜  Local:   http://localhost:3000/
```

---

## Phase 6 — Open the UI

Go to **http://localhost:3000**

You'll see 4 cards:
- **Planner** — enter URL + goal, click "Explore & Plan"
- **Generator** — paste a spec + URL, click "Generate tests"
- **Healer** — click "Run & heal"
- **Pipeline** — enter URL + goal, click "Run full pipeline"

---

## Quick reference — all commands

```cmd
:: ═══ ONE TIME SETUP ═══
python --version                          :: verify 3.11+
node --version                            :: verify 18+
npx playwright install chromium           :: browser binary

:: ═══ PLAYWRIGHT PROJECT ═══
cd backend
mkdir pw_project && cd pw_project
npm init -y
npm install -D @playwright/test
npx playwright install chromium
mkdir tests specs
:: create playwright.config.ts and tests/seed.spec.ts (see above)
cd ..

:: ═══ BACKEND ═══
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env                    :: edit with your keys
python main.py

:: ═══ FRONTEND (new terminal) ═══
cd frontend
npm install
npm run dev

:: ═══ OPEN ═══
:: http://localhost:3000
```

---

## Common Windows errors

| Error | Fix |
|-------|-----|
| `python not found` | Install Python, check "Add to PATH" |
| `npx not found` | Install Node.js, restart terminal |
| `MCP spawn fails` | Make sure `pw_project/` exists with `package.json` and `@playwright/test` installed |
| `MODULE_NOT_FOUND playwright.config.ts` | You're in the wrong directory — `PLAYWRIGHT_PROJECT_PATH` in `.env` must point to `pw_project/` |
| `Azure 401/403` | Check `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in `.env` |
| `WebSocket connection failed` in UI | Backend not running — start `python main.py` first |
| `Port 3000 in use` | Kill other process or change port in `vite.config.ts` |
| `No tools returned` | `pw_project/` missing `@playwright/test` — run `npm install -D @playwright/test` inside it |