---
name: task-continue
description: Resume work on an in-progress task from progressing.txt. Assesses current implementation state and presents what remains.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
argument-hint: "[TASK-CODE]"
---

# Continue an In-Progress Task

You are a task manager for this project. Your job is to help the user resume work on a task that is already in-progress in `progressing.txt`.

This skill does NOT close or commit tasks — use `/task-pick` for that.

## Current Task State

### In-progress tasks:
!`python3 scripts/task_manager.py list --status progressing --format summary`

## Instructions

The user wants to continue working on a task. The argument provided is: **$ARGUMENTS**

---

### Step 1: Select the Task

Read `progressing.txt` and identify all tasks marked `[~]`.

- **If no `[~]` tasks exist:** Inform the user there are no in-progress tasks and suggest using `/task-pick` to pick one up. Stop here.

- **If a task code was provided as argument:** Find that specific task in `progressing.txt`. If not found, inform the user and list the available in-progress tasks.

- **If no argument was provided and exactly one `[~]` task exists:** Use that task automatically.

- **If no argument was provided and multiple `[~]` tasks exist:** Use `AskUserQuestion` to let the user choose which task to continue.

### Step 2: Read the Full Task Block

Get the full parsed task data and file existence report:
```bash
python3 scripts/task_manager.py parse TASK-CODE
python3 scripts/task_manager.py verify-files TASK-CODE
```

The `parse` command returns all task fields as structured JSON: description, technical_details, files_create, files_modify, priority, dependencies.
The `verify-files` command returns a JSON report showing which files exist (`"exists": true/false`) and an `all_exist` summary.

### Step 3: Assess Current Implementation State

Use the `verify-files` report as a starting point. For each file:

**For files marked CREATE that exist (`"exists": true`):**
1. Read the file and check for key exports, components, or functions described in TECHNICAL DETAILS
2. Note whether the file is: **stub/empty** or **implemented** (with details)

**For files marked CREATE that are missing (`"exists": false`):**
1. Search for the filename in nearby directories (implementations may use slightly different paths)
2. If still not found, mark as **missing**

**For files marked MODIFY:**
1. Read the file to understand its current state
2. Use `Grep` to check for key changes described in TECHNICAL DETAILS (new imports, function names, route paths, component names, API endpoints, store fields, UI elements)
3. Note which changes are: **already applied** vs. **still needed**

**Cross-check against TECHNICAL DETAILS:**
For each numbered technical requirement, check whether code artifacts prove it was implemented.

### Step 4: Explore Related Code

Read all existing files related to the task to understand the current codebase state. Look at:
- Files that will be modified (full content)
- Similar files for patterns to follow (e.g., if creating a new route, look at existing routes)
- Related types, interfaces, and imports

### Step 5: Present the Continuation Briefing

Present a clear English-language briefing:

1. **Task**: Code, title, and priority
2. **Description**: Brief summary of what the task accomplishes
3. **Implementation Progress**:
   - What is already done (with file paths and evidence)
   - What remains to be done
4. **Next Steps**: Ordered list of concrete implementation actions for the remaining work
5. **Files to Create/Modify**: Every file with what still needs to happen in each
6. **Quality Gate Reminder**: Your project's verify command must pass before the task can be closed via `/task-pick`

After presenting the briefing, ask the user:

> "Ready to continue implementation, or would you like to adjust the approach?"
