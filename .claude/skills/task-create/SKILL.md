---
name: task-create
description: Create a new task in the project backlog with auto-assigned ID, codebase-informed technical details, and proper formatting in to-do.txt.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[task description]"
---

# Create a New Task

You are a task creation assistant for this project. Your job is to generate properly formatted task blocks and add them to the project backlog (`to-do.txt`).

Always respond and work in English. The task block content (field labels, descriptions, technical details) MUST also be written in **English**.

## Current Task State

### Next available task ID and existing prefixes:
!`python3 scripts/task_manager.py next-id --type task`

### Section headers in to-do.txt:
!`python3 scripts/task_manager.py sections --file to-do.txt`

## Arguments

The user wants to create a task for: **$ARGUMENTS**

## Instructions

### Step 1: Validate Input

If `$ARGUMENTS` is empty or unclear, ask the user to describe the task they want to create using `AskUserQuestion`:

> "Please describe the task you want to create. Include what the feature/fix should do and any known technical requirements."

Do NOT proceed without a clear task description.

### Step 2: Determine the Task Code Prefix

Analyze the task description and select an appropriate code prefix.

**Check the existing prefixes** from the data above. Each prefix represents a feature domain in this project.

**Rules:**
1. Reuse an existing prefix if the task clearly falls within that domain.
2. If no existing prefix fits, create a new one: 2-6 uppercase letters that clearly abbreviate the feature area.
3. Document the new prefix's domain when presenting the draft.

### Step 3: Compute the Next Task Number

Use the `next_number` field from the "Next available task ID" JSON above. The `prefixes` array shows all existing domain prefixes. No manual computation needed — the script handles global sequencing and false-positive filtering.

### Step 4: Explore the Codebase

Before writing the task block, explore the codebase to generate accurate technical details:

1. **Read relevant existing files** based on the task description — identify the key source directories and files in the project.
2. **Look at similar completed tasks** in `done.txt` for pattern reference — find a task with similar scope and mirror its structure.
3. **Identify files to create and modify** — be specific about file paths based on the actual directory structure. Use `Glob` to verify paths exist before listing them under `MODIFY`.

### Step 5: Draft the Task Block

Generate the task block in the **exact format** used by existing tasks. All content in English.

**Template:**

```
------------------------------------------------------------------------------
[ ] PREFIX-NNN — Task title (concise)
------------------------------------------------------------------------------
  Priority: [HIGH/MEDIUM/LOW]
  Dependencies: [TASK-CODE, TASK-CODE or None]

  DESCRIPTION:
  Multi-line description. Explain WHAT the task does, WHY it is
  needed, and its scope. Technical but readable, approximately
  4-10 lines.

  TECHNICAL DETAILS:
  Detailed technical implementation plan. Structure by layer/file:
[TECH_DETAIL_LAYERS]
  Use indented sub-sections with specific code snippets, type
  definitions, function signatures, and endpoint paths where appropriate.

  Files involved:
    CREATE:  path/to/new/file.ts
    MODIFY:  path/to/existing/file.ts
```

**Formatting rules:**
- Header separator lines are exactly 78 dashes: `------------------------------------------------------------------------------`
- Status prefix is `[ ] ` (pending)
- Title line format: `[ ] PREFIX-NNN — Task Title` (use `—` em dash, not `-` hyphen)
- Indent all content with 2 spaces
- Dependencies: use task codes like `AUTH-001, DB-002` or `None` if none
- Section labels in order: `DESCRIPTION:`, `TECHNICAL DETAILS:`, `Files involved:`
- File action labels: `CREATE:` (new files) and `MODIFY:` (existing files), indented 4 spaces
- End with two blank lines after the last file entry

### Step 6: Present the Draft and Ask for Confirmation

Present the complete task block to the user, along with:

1. **Task code:** The generated PREFIX-NNN
2. **Suggested section:** Which section it should be placed in, with reasoning
3. **Suggested priority:** HIGH / MEDIUM / LOW, with reasoning

Then use `AskUserQuestion` with these options:
- **"Looks good, create it"** — proceed to Step 7
- **"Needs changes"** — let the user specify what to adjust (section, priority, description, etc.)
- **"Cancel"** — abort without creating

### Step 7: Check for Duplicates

Before writing, perform a final duplicate check:

1. Run: `python3 scripts/task_manager.py duplicates --keywords "keyword1,keyword2,keyword3"`
   Use 2-3 key terms from the task title and description as keywords.
2. If the JSON output contains matches that look like a similar task, warn the user and ask whether to proceed or abort.
3. If no duplicates found, continue to Step 8.

### Step 8: Insert the Task into to-do.txt

Determine the correct insertion point based on the confirmed section.

**Insertion rules:**
1. Use the section data from the "Section headers" JSON above to find the target section's line number.
2. Read that range of lines to find the last task block in the section.
3. Insert the new task block **after the last existing task** in the section (or after the section header + blank lines if the section is empty).
4. Maintain whitespace conventions: two blank lines between tasks, two blank lines before the next section header.

Use the `Edit` tool to insert the task block at the correct position.

### Step 9: Confirm and Report

After successfully inserting the task, report:

> "Task **PREFIX-NNN — Task Title** has been created in `to-do.txt`, SECTION X.
>
> - **Code:** PREFIX-NNN
> - **Priority:** HIGH/MEDIUM/LOW
> - **Dependencies:** list or None
> - **Section:** SECTION X — Section Name
> - **Files to create:** N
> - **Files to modify:** N"

## Section Selection Guide

Sections are defined in `to-do.txt`. Read the section headers to understand the project's organizational structure. If the task does not clearly fit any existing section, suggest Section B (enhancements) and note this to the user. If needed, propose a new section.

## Important Rules

1. **NEVER modify `progressing.txt` or `done.txt`** — only append to `to-do.txt`.
2. **NEVER create duplicate tasks** — always cross-reference all three files first.
3. **NEVER reuse a task number that already exists** — always use global max + 1.
4. **NEVER skip user confirmation** — always present the draft and wait for approval.
5. **English content in task blocks** — field labels (`Priority`, `Dependencies`, `DESCRIPTION`, `TECHNICAL DETAILS`, `Files involved`, `CREATE`, `MODIFY`) and descriptions are always in English.
6. **Accurate file paths** — only reference files that actually exist (for `MODIFY`) or directories that exist (for `CREATE`). Verify with `Glob` before listing.
7. **Follow the exact formatting** of existing tasks — same indentation, same dash count (78), same field order.
