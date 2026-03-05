---
name: task-pick
description: Pick up the next task for implementation. Prioritizes verifying and closing in-progress tasks before picking new ones.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, TaskOutput
argument-hint: "[TASK-CODE]"
---

# Pick Up a Task

You are a task manager for this project. Your job is to:
1. **First**: verify and close any in-progress tasks that have already been implemented
2. **Then**: pick up a new task only when all in-progress tasks are resolved

Tasks are split across three files by status:
- `to-do.txt` — Pending tasks `[ ]`
- `progressing.txt` — In-progress tasks `[~]`
- `done.txt` — Completed tasks `[x]`

## Current Task State

### In-progress tasks:
!`python3 scripts/task_manager.py list --status progressing --format summary`

### Pending tasks:
!`python3 scripts/task_manager.py list --status todo --format summary`

### Completed tasks:
!`python3 scripts/task_manager.py list --status done --format summary`

### Recommended implementation order:
!`python3 scripts/task_manager.py sections --file to-do.txt`

## Instructions

The user wants to pick up a task. The argument provided is: **$ARGUMENTS**

---

### Step 0: Verify and Close In-Progress Tasks (PRIORITY)

Before picking any new task, you MUST process in-progress tasks from `progressing.txt`.

**If a specific task code was provided as argument** AND that task is already `[~]` in `progressing.txt`: jump directly to Step 0b for that task only, then stop (do not process other in-progress tasks).

**If no argument was provided** OR the argument is not found in `progressing.txt`: process ALL in-progress tasks sequentially as described below.

**0a. Read the in-progress task list:**
Read `progressing.txt` and identify all tasks marked `[~]`. If there are none, skip to Step 1.

**0b. For each in-progress task (in order), verify implementation:**

First, get the full parsed task data and file existence report:
```
python3 scripts/task_manager.py parse TASK-CODE
python3 scripts/task_manager.py verify-files TASK-CODE
```

The `parse` command returns all task fields as JSON (description, technical_details, files_create, files_modify).
The `verify-files` command checks whether each file in "Files involved" exists and returns a JSON report with `all_exist` boolean.

Then perform deeper verification checks:

1. **File existence checks:**
   - Review the `verify-files` JSON output. For any file marked `"exists": false`, search for the filename in nearby directories (implementations may use slightly different paths).
   - For files that exist, proceed to content checks.

2. **Implementation content checks:**
   - For files marked **CREATE**: Read the file and verify it contains meaningful implementation (not empty or stub-only). Check for key exports, components, or functions described in TECHNICAL DETAILS.
   - For files marked **MODIFY**: Use `Grep` to verify the key changes described in TECHNICAL DETAILS are present. Look for new imports, function names, route paths, component names, API endpoints, store fields, and UI elements described in the task.
   - Cross-check against TECHNICAL DETAILS: for each numbered technical requirement, verify at least one code artifact proves it was implemented.

3. **Build a verification report:**
   ```
   VERIFICATION: [TASK-CODE] — [Task Title]
   OK [file path] — [what was found]
   MISSING [file path] — MISSING: [what was expected]

   Technical checks:
   OK [requirement] — verified in [file]
   MISSING [requirement] — NOT FOUND
   ```

**0c. Decision based on verification result:**

- **ALL checks pass (task fully implemented):**
  1. **Quality Gate (MANDATORY):** Before closing the task, run your project's verify command (see CLAUDE.md). If it fails:
     - Fix ALL errors and warnings reported
     - Re-run the verify command until it passes with zero errors
     - Only proceed to step 2 when the quality gate passes
  2. **Smoke-Test (MANDATORY):** After the quality gate passes, verify the app starts without runtime errors:

     **2a. Start the application:**
     Run your project's start command using the Bash tool with `run_in_background: true`.

     **2b. Wait for startup and check ports:**
     Wait for startup and verify dev ports are listening:
     ```bash
     python3 scripts/app_manager.py verify-ports --wait 8 --expect bound DEV_PORTS
     ```

     **2c. Check for startup errors:**
     Read the background process output using `TaskOutput`. Scan for common error indicators:
     - Port conflicts: `EADDRINUSE`, `Address already in use`, `port is already allocated`
     - Missing dependencies: `Cannot find module`, `ModuleNotFoundError`, `no required module`, `package not found`
     - Connection failures: `ECONNREFUSED`, `Connection refused`, `connection error`
     - Generic errors: `Error`, `FATAL`, `panic`, `traceback`, stack traces or crash dumps

     **Note on false positives:** Ignore occurrences of "error" that appear in variable names, file paths, log format strings, or middleware names (e.g., `errorHandler`, `error.middleware.ts`). Only flag actual runtime errors.

     **2d. Decision:**
     - **If startup errors are found:** Fix all errors, then re-run the verify command and repeat the smoke-test from 2a (max 2 retries total). If still failing after retries, present the errors to the user and stop.
     - **If no errors (or only false positives):** Proceed to 2e.

     **2e. Stop the application (MANDATORY — no processes must remain):**
     Kill all processes on dev ports and verify:
     ```bash
     python3 scripts/app_manager.py kill-ports DEV_PORTS
     python3 scripts/app_manager.py verify-ports --wait 2 --expect free DEV_PORTS
     ```

  3. Present the verification report to the user (including quality gate result and smoke-test result)
  4. **Run the Step 6 completion flow** (Testing Guide -> Confirm -> Close -> Commit) for this task
  5. **Continue to the next `[~]` task** in progressing.txt — repeat Step 0b

- **Some checks fail (task partially implemented or not implemented):**
  1. Present the verification report showing what is implemented and what is missing
  2. **Do NOT close the task** — leave it as `[~]` in progressing.txt
  3. Read all existing files related to the task to understand current state
  4. Proceed to Step 4 (Explore codebase) and Step 5 (Present briefing) for this task, focusing the briefing on **what remains to be done**
  5. **Stop processing further in-progress tasks** — the user should finish this one first

**0d. When all in-progress tasks have been verified and closed:**
Inform the user how many tasks were closed, then continue to Step 1 to pick a new task.

---

### Step 1: Determine which task to pick

This step is only reached when there are NO in-progress tasks remaining in `progressing.txt`.

- **If a task code was provided** (e.g., `AUTH-001`): Use that specific task. Verify it exists in `to-do.txt` and is in `[ ]` (todo) status. If found in `done.txt` as `[x]` (completed), inform the user and suggest the next available task.

- **If no argument was provided**: Select the next task from the recommended implementation order that is still `[ ]` (todo) in `to-do.txt`. Skip tasks found in `done.txt` (completed) or `progressing.txt` (in-progress). Also verify that the task's dependencies are satisfied (dependency tasks should be in `done.txt` as `[x]`). If a task has unsatisfied dependencies, skip it and pick the next one.

### Step 2: Move task to progressing.txt

Run the move command:
```bash
python3 scripts/task_manager.py move TASK-CODE --to progressing
```

This automatically removes the block from `to-do.txt`, inserts it into `progressing.txt`, and updates the status symbol from `[ ]` to `[~]`. Verify the JSON output shows `"success": true`.

If the task appears in the recommended order section of `to-do.txt`, update its status annotation to `[IN PROGRESS]`.

### Step 3: Read the full task details

Get the full parsed task data:
```bash
python3 scripts/task_manager.py parse TASK-CODE
```
This returns all fields as structured JSON: priority, dependencies, description, technical_details, files_create, files_modify.

### Step 4: Explore the codebase

For each file listed in the "Files involved" section:
- If the file exists, read it to understand the current state
- If marked "CREATE", check the target directory and look at similar files for patterns to follow
- Identify relevant interfaces, types, and patterns

### Step 5: Present the implementation briefing

Present a clear English-language briefing:

1. **Task Selected**: Code, title, and priority
2. **Status Update**: Confirm the task was moved to progressing.txt and marked as in-progress
3. **Scope Summary**: What needs to be done
4. **Technical Approach**: Implementation steps based on task details and codebase exploration
5. **Files to Create/Modify**: Every file with what needs to happen in each
6. **Dependencies**: Status of all dependencies (check done.txt for completed deps)
7. **Risks**: Any concerns found during exploration
8. **Quality Gate**: Remind that the project's verify command must pass before the task can be closed

After presenting the briefing, ask the user: "Ready to start implementation, or would you like to adjust the approach?"

---

### Step 6: Post-Implementation — Confirm, Close & Commit

After a task has been **fully implemented and the quality gate passes**, execute this completion flow:

**6a. Present a Testing Guide:**

Before asking the user to confirm, generate and present a **manual testing guide** specific to the task that was just implemented. Derive the guide from the task's TECHNICAL DETAILS and Files involved sections.

Present it in this format:

> ### Testing Guide for [TASK-CODE] — [Task Title]
>
> **Prerequisites:**
> - [What needs to be running — e.g., dev server, Docker containers, specific env vars]
>
> **Steps to test:**
> 1. [Concrete action the user can perform in the browser or terminal]
>    - **Expected:** [What they should see or what should happen]
> 2. [Next action]
>    - **Expected:** [Result]
> 3. [Continue as needed...]
>
> **Edge cases to check:**
> - [2-3 edge cases worth verifying — e.g., empty states, error handling, permissions, invalid input]

The guide must be actionable and specific — use real URLs, real UI element names, and real API endpoints from the implementation. Do not use generic placeholders.

**6b. Ask for user confirmation:**

Present a summary of what was done and ask the user to confirm:

> "Implementation of **[TASK-CODE] — [Task Title]** is complete and the quality gate passed.
>
> **Summary of work done:**
> - [brief list of what was created/modified]
>
> Can you confirm this task is done?"

Use `AskUserQuestion` with options:
- **"Yes, task is done"** — proceed to 6c
- **"Not yet, needs more work"** — stop the completion flow; the task stays as `[~]` in `progressing.txt`

**6c. Move task to done.txt (automatic on confirmation):**

Once the user confirms the work is done:

1. Run the move command with a completion summary:
   ```bash
   python3 scripts/task_manager.py move TASK-CODE --to done --completed-summary "Brief summary of what was implemented"
   ```
   This automatically removes from `progressing.txt`, inserts into `done.txt`, updates `[~]` to `[x]`, and adds the `COMPLETED:` line.
2. If the task appears in the recommended order section of `to-do.txt`, update its status annotation to `[COMPLETED]`
3. Inform the user: "Task [TASK-CODE] has been moved to done.txt."

**6d. Ask to commit:**

After closing the task, ask the user:

> "Would you like me to commit these changes?"

Use `AskUserQuestion` with options:
- **"Yes, commit"** — create a commit using the `/commit` skill (or follow the standard git commit workflow). The commit message should reference the task code and briefly describe what was implemented.
- **"No, skip commit"** — skip the commit; done.

**Important:** Always ask — never auto-commit or auto-close without user confirmation.
