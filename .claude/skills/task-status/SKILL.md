---
name: task-status
description: Show the current status of all project tasks, including summary counts, in-progress tasks, and next recommended tasks.
disable-model-invocation: true
---

# Task Status Report

You are a task status reporter. Analyze the data below and present a clear, well-formatted status report in English.

## Mode Detection

Determine the operating mode first:

```bash
TRACKER_CFG=".claude/issues-tracker.json"; [ ! -f "$TRACKER_CFG" ] && TRACKER_CFG=".claude/github-issues.json"
PLATFORM="$(jq -r '.platform // "github"' "$TRACKER_CFG" 2>/dev/null)"
TRACKER_ENABLED="$(jq -r '.enabled // false' "$TRACKER_CFG" 2>/dev/null)"
TRACKER_SYNC="$(jq -r '.sync // false' "$TRACKER_CFG" 2>/dev/null)"
TRACKER_REPO="$(jq -r '.repo' "$TRACKER_CFG" 2>/dev/null)"
```

- **Platform-only mode** (`TRACKER_ENABLED=true` AND `TRACKER_SYNC != true`): Use platform issues as the sole data source. Skip all local file reads.
- **Dual sync mode** (`TRACKER_ENABLED=true` AND `TRACKER_SYNC=true`): Use local files as primary, platform as secondary.
- **Local only mode** (`TRACKER_ENABLED=false` or config missing): Use local files only.

## Platform Commands

| Operation | GitHub | GitLab |
|-----------|--------|--------|
| List issues (JSON) | `gh issue list --repo "$TRACKER_REPO" --label L --state open --json f --jq 'e'` | `glab issue list -R "$TRACKER_REPO" -l L --state opened --output json \| jq 'e'` |
| List issues (state) | `--state open` / `--state closed` | `--state opened` / `--state closed` |

---

## Platform-Only Mode

If in platform-only mode, gather all data from platform issues:

### Task Summary

```bash
TODO_COUNT=$(gh issue list --repo "$TRACKER_REPO" --label "task,status:todo" --state open --json number --jq 'length' 2>/dev/null)
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:todo" --state opened --output json | jq 'length'
PROGRESS_COUNT=$(gh issue list --repo "$TRACKER_REPO" --label "task,status:in-progress" --state open --json number --jq 'length' 2>/dev/null)
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:in-progress" --state opened --output json | jq 'length'
DONE_COUNT=$(gh issue list --repo "$TRACKER_REPO" --label "task,status:done" --state closed --json number --jq 'length' 2>/dev/null)
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:done" --state closed --output json | jq 'length'
```

### In-Progress Tasks

```bash
gh issue list --repo "$TRACKER_REPO" --label "task,status:in-progress" --state open --json number,title,labels --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:in-progress" --state opened --output json | jq '.[] | "#\(.iid) \(.title)"'
```

### Completed Tasks

```bash
gh issue list --repo "$TRACKER_REPO" --label "task,status:done" --state closed --limit 20 --json number,title --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:done" --state closed --per-page 20 --output json | jq '.[] | "#\(.iid) \(.title)"'
```

### Pending Tasks (by priority)

```bash
# High priority
gh issue list --repo "$TRACKER_REPO" --label "task,status:todo,priority:high" --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:todo,priority:high" --state opened --output json | jq '.[] | "#\(.iid) \(.title)"'
# Medium priority
gh issue list --repo "$TRACKER_REPO" --label "task,status:todo,priority:medium" --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:todo,priority:medium" --state opened --output json | jq '.[] | "#\(.iid) \(.title)"'
# Low priority
gh issue list --repo "$TRACKER_REPO" --label "task,status:todo,priority:low" --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "task,status:todo,priority:low" --state opened --output json | jq '.[] | "#\(.iid) \(.title)"'
```

### Ideas (open)

```bash
gh issue list --repo "$TRACKER_REPO" --label "idea" --state open --json number,title --jq '.[] | "#\(.number) \(.title)"'
# GitLab: glab issue list -R "$TRACKER_REPO" -l "idea" --state opened --output json | jq '.[] | "#\(.iid) \(.title)"'
```

Present the report following the same format as below (Instructions section).

---

## Local/Dual Mode Data

These sections are used in local-only or dual-sync mode:

### Summary (JSON):
!`python3 scripts/task_manager.py summary`

### In-Progress Tasks:
!`python3 scripts/task_manager.py list --status progressing --format summary`

### Completed Tasks:
!`python3 scripts/task_manager.py list --status done --format summary`

### Blocked Tasks:
!`python3 scripts/task_manager.py list --status blocked --format summary`

### Pending Tasks:
!`python3 scripts/task_manager.py list --status todo --format summary`

### Recommended Implementation Order:
!`sed -n '/RECOMMENDED IMPLEMENTATION ORDER/,/^====/p' to-do.txt | tr -d '\r'`

---

## Instructions

Present the information above as a structured English-language report with these sections:

1. **Summary** — A table with task counts by status (completed, in-progress, todo, blocked) and overall progress percentage.

2. **In-Progress Tasks** — For each task marked `[~]` (local) or with `status:in-progress` label (platform), show:
   - Task code and title
   - Priority
   - What remains to be done
   - Files involved

3. **Next Recommended Tasks** — Based on the recommended implementation order (local mode) or priority labels (platform-only mode), identify the next 2-3 tasks that should be picked up. For each show:
   - Task code and title
   - Priority
   - Dependencies and whether they are satisfied
   - Brief scope description

4. **Blocked Tasks** — If any, list them with the blocking reason.

Do NOT modify any files. This is a read-only status report.
