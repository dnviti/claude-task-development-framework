---
name: task-continue
description: Resume work on an in-progress task. Assesses current implementation state and presents what remains.
disable-model-invocation: true
argument-hint: "[TASK-CODE]"
---

# Continue an In-Progress Task

You are a task manager for this project. Your job is to help the user resume work on a task that is already in-progress.

This skill does NOT close or commit tasks — use `/task-pick` for that.

## Mode Detection

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py platform-config`

Use the `mode` field to determine behavior: `platform-only`, `dual-sync`, or `local-only`. The JSON includes `platform`, `enabled`, `sync`, `repo`, `cli` (gh/glab), and `labels`.

## Platform Commands

Use `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py platform-cmd <operation> [key=value ...]` to generate the correct CLI command for the detected platform (GitHub/GitLab).

Supported operations: `list-issues`, `search-issues`, `view-issue`, `edit-issue`, `close-issue`, `comment-issue`, `create-issue`, `create-pr`, `list-pr`, `merge-pr`, `create-release`, `edit-release`.

Example: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py platform-cmd create-issue title="[CODE] Title" body="Description" labels="task,status:todo"`

## Worktree Detection

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py worktree-info`

Use the `in_worktree`, `main_root`, and `worktrees` fields to determine context. Task management files (`to-do.txt`, `progressing.txt`, `done.txt`) always live in `main_root`. Source code for the current task lives in the worktree directory.

---

## Current Task State

### Platform-only mode — In-progress tasks:

```bash
gh issue list --repo "$TRACKER_REPO" --label "task,status:in-progress" --state open --json number,title --jq '.[] | "\(.title)"' 2>/dev/null
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:in-progress" --state opened --output json | jq '.[] | "\(.title)"' 2>/dev/null
```

### Local/Dual mode — In-progress tasks:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py list --status progressing --format summary`

## Instructions

The user wants to continue working on a task. The argument provided is: **$ARGUMENTS**

---

### Step 1: Select the Task

**In Platform-only mode:**
- Query in-progress tasks: `gh issue list --repo "$TRACKER_REPO" --label "task,status:in-progress" --state open --json number,title`
  <!-- GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:in-progress" --state opened --output json -->
- If a task code was provided, search: `gh issue list --repo "$TRACKER_REPO" --search "[TASK-CODE] in:title" --label "task,status:in-progress" --json number,title`
  <!-- GitLab: glab issue list -R "$TRACKER_REPO" --search "[TASK-CODE]" -l "task,status:in-progress" --output json -->

**In local/dual mode:**
- Read `progressing.txt` and identify all tasks marked `[~]`.

**Common logic:**
- **If no in-progress tasks exist:** Inform the user there are no in-progress tasks and suggest using `/task-pick` to pick one up. Stop here.
- **If a task code was provided as argument:** Find that specific task. If not found, inform the user and list the available in-progress tasks.
- **If no argument was provided and exactly one in-progress task exists:** Use that task automatically.
- **If no argument was provided and multiple in-progress tasks exist:** Use `AskUserQuestion` to let the user choose which task to continue.

### Step 1.5: Enter or create the task worktree

After selecting the task, set up an isolated worktree for the implementation work.

**1.5a. Get worktree context:**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py worktree-info
```
Store the `main_root` path and check the `worktrees` array.

**1.5b. Determine the worktree state:**

- **If already in the correct worktree** (the `task_code` from `worktree-info` matches the selected task): No action needed. Inform the user and proceed to Step 2.

- **If a worktree already exists for this task** (found in the `worktrees` array): Change the working directory to that worktree path. Inform the user: "Entering existing worktree for `[TASK-CODE]`."

- **If no worktree exists but the branch exists** (normal case — worktree was removed when task was previously closed):
  ```bash
  WORKTREE_DIR="<main_root>/.worktrees/task/<task-code-lowercase>"
  mkdir -p "<main_root>/.worktrees/task"
  grep -qxF '.worktrees/' "<main_root>/.gitignore" 2>/dev/null || echo '.worktrees/' >> "<main_root>/.gitignore"
  git worktree add "$WORKTREE_DIR" task/<task-code-lowercase>
  ```
  Change the working directory to `$WORKTREE_DIR`. Inform the user: "Created fresh worktree from existing branch `task/<task-code-lowercase>`."

- **If neither worktree nor branch exists:** Inform the user that no task branch or worktree was found. Suggest using `/task-pick <TASK-CODE>` to properly set up the task.

**Important:** All subsequent steps operate within the worktree directory.

### Step 2: Read the Full Task Block

**In Platform-only mode:**
- Find the issue number: `gh issue list --repo "$TRACKER_REPO" --search "[TASK-CODE] in:title" --label task --json number --jq '.[0].number'`
  <!-- GitLab: glab issue list -R "$TRACKER_REPO" --search "[TASK-CODE]" -l task --output json | jq '.[0].iid' -->
- Read the full issue body: `gh issue view $ISSUE_NUM --repo "$TRACKER_REPO" --json body --jq '.body'`
  <!-- GitLab: glab issue view $ISSUE_NUM -R "$TRACKER_REPO" --output json | jq '.body' -->
- Parse the issue body to extract:
  - **Description** section
  - **Technical Details** section
  - **Files Involved** section (files to CREATE and MODIFY)

**In local/dual mode:**
- Get the full parsed task data and file existence report:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py parse TASK-CODE
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py verify-files TASK-CODE
```
- The `parse` command returns all task fields as structured JSON: description, technical_details, files_create, files_modify, priority, dependencies.
- The `verify-files` command returns a JSON report showing which files exist (`"exists": true/false`) and an `all_exist` summary.

### Step 3: Assess Current Implementation State

For each file in the files involved section, check what has already been done:

**For files marked CREATE:**
1. Use `Glob` to check if the file exists at the specified path
2. If not found at the exact path, search for the filename in nearby directories
3. If found, read it and check for key exports, components, or functions described in Technical Details
4. Note whether the file is: **missing**, **stub/empty**, or **implemented** (with details)

**For files marked MODIFY:**
1. Read the file to understand its current state
2. Use `Grep` to check for key changes described in Technical Details (new imports, function names, route paths, component names, API endpoints, store fields, UI elements)
3. Note which changes are: **already applied** vs. **still needed**

**Cross-check against Technical Details:**
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
