---
name: idea-approve
description: Approve an idea from ideas.txt, convert it into a full task with technical details, and add it to to-do.txt. This is the ONLY bridge from ideas to the task pipeline.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[IDEA-NNN]"
---

# Approve an Idea

You are the idea approval gateway for this project. Your job is to take an idea from `ideas.txt`, flesh it out with codebase-informed technical details, and promote it to a full task in `to-do.txt`.

This skill is the **ONLY** bridge between the idea backlog and the task pipeline. Ideas must go through this process to become actionable tasks.

Always respond and work in English. The task block content (field labels, descriptions, technical details) MUST also be written in **English**.

## Current State

### Ideas available for approval:
!`python3 scripts/task_manager.py list-ideas --file ideas --format summary`

### Next available task ID and existing prefixes:
!`python3 scripts/task_manager.py next-id --type task`

### Section headers in to-do.txt:
!`python3 scripts/task_manager.py sections --file to-do.txt`

## Arguments

The user wants to approve: **$ARGUMENTS**

## Instructions

### Step 1: Select the Idea

- **If an IDEA-NNN code was provided**: Find that idea in `ideas.txt`. If not found, inform the user and list available ideas.
- **If no argument was provided**: List all ideas from `ideas.txt` with their codes, titles, and categories. Use `AskUserQuestion` to ask the user which idea to approve.

If `ideas.txt` has no ideas, inform the user: "No ideas available for approval. Use `/idea-create` to add ideas first."

### Step 2: Read the Full Idea

Get the full parsed idea data:
```bash
python3 scripts/task_manager.py parse IDEA-NNN
```
This returns all fields as JSON: title, category, date, description, motivation.

Present the idea to the user as context for what will be converted.

### Step 3: Determine the Task Code Prefix

Analyze the idea's description and category to select an appropriate task prefix.

**Check the existing prefixes** from the data above. Each prefix represents a feature domain.

**Rules:**
1. Reuse an existing prefix if the idea clearly falls within that domain.
2. If no existing prefix fits, create a new one: 2-6 uppercase letters that clearly abbreviate the feature area.

### Step 4: Compute the Next Task Number

Use the `next_number` field from the "Next available task ID" JSON above. The `prefixes` array shows existing domain prefixes. No manual computation needed.

### Step 5: Explore the Codebase

Before writing the task block, explore the codebase to generate accurate technical details:

1. **Read relevant existing files** based on the idea description — identify the key source directories and files in the project.
2. **Look at similar completed tasks** in `done.txt` for pattern reference.
3. **Identify files to create and modify** — be specific about file paths. Use `Glob` to verify paths exist before listing them under `MODIFY`.

### Step 6: Draft the Full Task Block

Convert the idea into a complete task block, expanding the high-level idea with concrete technical details from your codebase exploration.

**Template:**

```
------------------------------------------------------------------------------
[ ] PREFIX-NNN — Task title (concise)
------------------------------------------------------------------------------
  Priority: [HIGH/MEDIUM/LOW]
  Dependencies: [TASK-CODE, TASK-CODE or None]

  DESCRIPTION:
  Expanded description based on the original idea's DESCRIPTION
  and MOTIVATION. More detailed than the idea, explaining WHAT, WHY,
  and the scope. Approximately 4-10 lines.

  TECHNICAL DETAILS:
  Detailed technical implementation plan. Structure by layer/file:
[TECH_DETAIL_LAYERS]
  This section is NEW — the original idea did not have this.
  Include specific code snippets, function signatures, endpoint paths.

  Files involved:
    CREATE:  path/to/new/file.ts
    MODIFY:  path/to/existing/file.ts
```

**Formatting rules:**
- Header separator lines are exactly 78 dashes
- Status prefix is `[ ] ` (pending)
- Title line format: `[ ] PREFIX-NNN — Task Title` (use `—` em dash)
- Indent all content with 2 spaces
- Dependencies: use task codes or `None`
- Section labels: `DESCRIPTION:`, `TECHNICAL DETAILS:`, `Files involved:`
- File action labels: `CREATE:` and `MODIFY:`, indented 4 spaces
- End with two blank lines

### Step 7: Present the Draft and Ask for Confirmation

Present the complete task block to the user, along with:

1. **Original idea:** IDEA-NNN and its title
2. **New task code:** PREFIX-NNN
3. **Suggested section:** Which section and why
4. **Suggested priority:** HIGH / MEDIUM / LOW and why

Then use `AskUserQuestion` with these options:
- **"Looks good, approve it"** — proceed to Step 8
- **"Needs changes"** — let the user specify adjustments
- **"Cancel"** — abort without approving

### Step 8: Check for Duplicates

Run: `python3 scripts/task_manager.py duplicates --keywords "keyword1,keyword2,keyword3" --files "to-do.txt,progressing.txt,done.txt"`

Use 2-3 key terms from the task title and description. If the JSON output contains matches that look like a similar task, warn the user and ask whether to proceed or abort.

### Step 9: Insert the Task and Remove the Idea

This step performs TWO operations:

**9a. Add the task to `to-do.txt`:**
1. Use the section data from the "Section headers" JSON above to find the target section's line number.
2. Find the last task block in the section.
3. Insert the new task block after the last existing task using the `Edit` tool.
4. Maintain whitespace conventions: two blank lines between tasks.

**9b. Remove the idea from `ideas.txt`:**
Run: `python3 scripts/task_manager.py remove IDEA-NNN --file ideas.txt`
This cleanly removes the idea block and handles whitespace cleanup automatically.

### Step 10: Confirm and Report

After successfully completing both operations, report:

> "Idea **IDEA-NNN** has been approved and promoted to task **PREFIX-NNN — Task Title**.
>
> - **Task code:** PREFIX-NNN
> - **Priority:** HIGH/MEDIUM/LOW
> - **Dependencies:** list or None
> - **Section:** SECTION X — Section Name
> - **Files to create:** N
> - **Files to modify:** N
>
> The idea has been removed from `ideas.txt`. The task is now in `to-do.txt` and can be picked up with `/task-pick PREFIX-NNN`."

## Section Selection Guide

Sections are defined in `to-do.txt`. Read the section headers to understand the project's organizational structure. If the task does not clearly fit any existing section, suggest a default section and note this to the user.

## Important Rules

1. **This is the ONLY way ideas become tasks** — ideas must never be added to `to-do.txt` by any other means.
2. **NEVER modify `progressing.txt` or `done.txt`** — only add to `to-do.txt` and remove from `ideas.txt`.
3. **NEVER reuse a task number** — always use global max + 1.
4. **NEVER skip user confirmation** — always present the draft and wait for approval.
5. **English content in task blocks** — same conventions as existing tasks.
6. **Accurate file paths** — verify with `Glob` before listing.
7. **Follow the exact task formatting** — same indentation, dash count (78), field order as existing tasks.
8. **Always remove the approved idea from `ideas.txt`** — an approved idea must not remain in the idea backlog.
