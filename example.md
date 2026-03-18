# Example Inputs for Testing All 4 Agent Cards

---

## 1. Planner Card

**URL:**
```
https://todomvc.com/examples/react/dist/
```

**Goal:**
```
Create comprehensive CRUD tests — add, complete, edit, delete todos, filtering, and edge cases
```

**What happens:** The agent opens the browser, navigates to TodoMVC, clicks around to explore the input field, adds a todo, checks the checkbox, hovers to find the delete button, explores the filter links (All/Active/Completed). Then writes a structured markdown test plan.

**Expected output:** A markdown file like `specs/test-plan.md` with scenarios for adding, completing, editing, deleting, filtering, and edge cases.

---

## 2. Generator Card

**URL:**
```
https://todomvc.com/examples/react/dist/
```

**Spec (paste this into the textarea):**
```markdown
# TodoMVC React — CRUD Test Plan

## Application overview
React-based todo list app. Input field at top with placeholder "What needs to be done?". Todos appear in a list below. Each todo has a checkbox to complete and a delete button visible on hover.

## Test scenarios

### 1. Adding todos

#### 1.1 Add a single todo
**Steps:**
1. Click the input field with placeholder "What needs to be done?"
2. Type "Buy groceries"
3. Press Enter

**Expected results:**
- Todo "Buy groceries" appears in the list
- Input field is cleared
- Counter shows "1 item left"

#### 1.2 Add empty todo (negative)
**Steps:**
1. Click the input field
2. Press Enter without typing

**Expected results:**
- No todo is added
- List remains empty

### 2. Completing todos

#### 2.1 Mark a todo as complete
**Steps:**
1. Add a todo "Walk the dog"
2. Click the checkbox next to "Walk the dog"

**Expected results:**
- Todo text gets strikethrough style
- Counter decrements

### 3. Deleting todos

#### 3.1 Delete a todo
**Steps:**
1. Add a todo "Read a book"
2. Hover over "Read a book"
3. Click the × (destroy) button

**Expected results:**
- Todo is removed from the list
```

**What happens:** The agent reads the spec, opens the browser to verify locators (`browser_snapshot`, `browser_generate_locator`), writes `.spec.ts` files, and runs them with `test_run` to verify they pass.

**Expected output:** Generated TypeScript test files like `tests/adding-todos.spec.ts`, `tests/completing-todos.spec.ts`, etc.

---

## 3. Healer Card

**URL:**
```
https://todomvc.com/examples/react/dist/
```

**Test file (optional):**
```
tests/adding-todos.spec.ts
```

Leave test file empty to run ALL tests. Or specify one file to focus the healer.

**What happens:** The agent runs `test_run` to execute all tests. If any fail, it runs `test_debug` on the failing test, takes a `browser_snapshot` at the failure point, checks `browser_console_messages`, diagnoses the root cause (wrong locator, timing issue, etc.), fixes the code, and re-runs until passing.

**Expected output:** A report of what failed, what was diagnosed, what was fixed, and final pass/fail status.

---

## 4. Pipeline Card (all 3 chained)

**URL:**
```
https://todomvc.com/examples/react/dist/
```

**Goal:**
```
Create comprehensive CRUD tests — add, complete, edit, delete todos, filtering, and edge cases
```

**What happens:**
1. Phase indicator shows **▶ planner** — agent explores the app
2. Phase indicator shifts to **▶ generator** — agent writes test files
3. Phase indicator shifts to **▶ healer** — agent runs and fixes tests
4. All three phases complete

**Expected output:** Spec markdown + test files + healer report, all streamed live.

---

## Other URLs to test with

### SauceDemo (login page)
```
URL: https://www.saucedemo.com/
Goal: Create login tests — valid login, invalid credentials, empty fields, locked user
```

### The Internet (Heroku test app)
```
URL: https://the-internet.herokuapp.com/
Goal: Create tests for login, checkboxes, dropdown, and drag-and-drop features
```

### DemoQA
```
URL: https://demoqa.com/
Goal: Create tests for the forms section — text box, radio button, checkboxes, and buttons
```

### Swag Labs (full e-commerce)
```
URL: https://www.saucedemo.com/
Goal: Create end-to-end checkout tests — login, add to cart, checkout flow, order confirmation
```