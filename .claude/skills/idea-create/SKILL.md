---
name: idea-create
description: Create a new idea in the idea backlog (ideas.txt) for future evaluation. Ideas are lightweight proposals that must be approved before becoming tasks.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
argument-hint: "[idea description]"
---

# Create a New Idea

You are an idea creation assistant for this project. Your job is to generate properly formatted idea blocks and add them to the idea backlog (`ideas.txt`).

Ideas are **lightweight proposals** — they describe *what* and *why* at a high level, without implementation details. Technical details are only added when an idea is approved into a task via `/idea-approve`.

Always respond and work in English. The idea block content (field labels, descriptions) MUST also be written in **English**.

## Current Idea State

### Next available idea ID:
!`python3 scripts/task_manager.py next-id --type idea`

### Current ideas:
!`python3 scripts/task_manager.py list-ideas --file ideas --format summary`

## Arguments

The user wants to create an idea for: **$ARGUMENTS**

## Instructions

### Step 1: Validate Input

If `$ARGUMENTS` is empty or unclear, ask the user to describe the idea they want to add using `AskUserQuestion`:

> "Please describe the idea you want to add. Include what the feature/improvement should do and why it would be valuable."

Do NOT proceed without a clear idea description.

### Step 2: Determine the Category

Analyze the idea description and select an appropriate category.

**Suggested categories** (tailored to this project):

[IDEA_CATEGORIES]

If no existing category fits well, create a concise new one.

*The category table above is configured by `/project-initialization`. If not yet configured, use generic categories: Core Features, User Interface, Security, Integration, Performance, Infrastructure.*

### Step 3: Compute the Next Idea Number

Use the `next_number` field from the "Next available idea ID" JSON above. No manual computation needed — the script handles global sequencing across both idea files.

### Step 4: Draft the Idea Block

Generate the idea block in the **exact format** below. All content in English.

**Template:**

```
------------------------------------------------------------------------------
IDEA-NNN — Idea title (concise)
------------------------------------------------------------------------------
  Category: [from Step 2]
  Date: YYYY-MM-DD

  DESCRIPTION:
  Description of the idea. Explain WHAT it proposes and the
  general context. Keep it high-level, without implementation details.
  Approximately 2-6 lines.

  MOTIVATION:
  Why this idea could be useful. What problem it solves or
  what value it adds to the project. Approximately 2-4 lines.
```

**Formatting rules:**
- Header separator lines are exactly 78 dashes: `------------------------------------------------------------------------------`
- Title line format: `IDEA-NNN — Title` (use `—` em dash, not `-` hyphen)
- Indent all content with 2 spaces
- Date format: `YYYY-MM-DD` (today's date)
- Section labels in order: `DESCRIPTION:`, `MOTIVATION:`
- End with two blank lines after the last line

### Step 5: Present the Draft and Ask for Confirmation

Present the complete idea block to the user, along with:

1. **Idea code:** The generated IDEA-NNN
2. **Category:** The selected category

Then use `AskUserQuestion` with these options:
- **"Looks good, create it"** — proceed to Step 6
- **"Needs changes"** — let the user specify what to adjust
- **"Cancel"** — abort without creating

### Step 6: Check for Duplicates

Before writing, perform a duplicate check:

1. Run: `python3 scripts/task_manager.py duplicates --keywords "keyword1,keyword2,keyword3"`
   Use 2-3 key terms from the idea title and description as keywords.
2. If the JSON output contains matches that look like a similar idea or task, warn the user and ask whether to proceed or abort.
3. If no duplicates found, continue to Step 7.

### Step 7: Append the Idea to ideas.txt

Append the idea block at the end of `ideas.txt` (before any trailing blank lines, or at the very end of the file).

Use the `Edit` tool to insert the idea block.

### Step 8: Confirm and Report

After successfully inserting the idea, report:

> "Idea **IDEA-NNN — Idea Title** has been added to `ideas.txt`.
>
> - **Code:** IDEA-NNN
> - **Category:** Category
> - **Date:** YYYY-MM-DD
>
> Use `/idea-approve IDEA-NNN` to promote this idea to a task, or `/idea-disapprove IDEA-NNN` to reject it."

## Important Rules

1. **NEVER modify task files** (`to-do.txt`, `progressing.txt`, `done.txt`) — only append to `ideas.txt`.
2. **NEVER create duplicate ideas** — always cross-reference all idea and task files first.
3. **NEVER reuse an idea number** — always use global max + 1 across both idea files.
4. **NEVER skip user confirmation** — always present the draft and wait for approval.
5. **English content in idea blocks** — field labels (`Category`, `Date`, `DESCRIPTION`, `MOTIVATION`) and descriptions are always in English.
6. **Keep ideas high-level** — no implementation details, no file lists, no technical specifications. Those are added during `/idea-approve`.
7. **Follow the exact formatting** — same indentation, same dash count (78), same field order.
