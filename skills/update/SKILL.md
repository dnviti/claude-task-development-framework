---
name: update
description: Update CTDF-managed files (pipelines, scripts, prompts, skills, CLAUDE.md) to the latest plugin version. Detects outdated files and preserves user customizations.
disable-model-invocation: true
argument-hint: "[all | pipelines | agentic | scripts | prompts | skills | claude-md]"
---

# Update CTDF-Managed Files

You are an update assistant for the CTDF plugin. Your job is to detect which CTDF-managed files in the target repository are outdated compared to the current plugin version, show a summary, and selectively update them while preserving user customizations.

## CRITICAL: User Interaction Rules

This skill requires user decisions. At each `AskUserQuestion` call, you MUST:

1. **STOP completely** after calling `AskUserQuestion` — do NOT generate any further text or tool calls in the same turn
2. **WAIT for the user's actual response** before proceeding to the next step
3. **Never assume an answer** — if the response is empty or unclear, ask again with the same options
4. **Never batch multiple questions** — ask ONE question at a time and wait for each answer
5. **Only use the exact options specified** in each step — do not invent additional options or rephrase them

## Arguments

The user invoked with: **$ARGUMENTS**

Supported arguments:
- Empty or `all` — scan all categories
- `pipelines` — core CI/CD pipelines only
- `agentic` — agentic fleet pipelines only
- `scripts` — `.claude/scripts/` files only
- `prompts` — `.claude/prompts/` files only
- `skills` — `.claude/skills/` files only
- `claude-md` — CLAUDE.md CTDF section only

## CTDF-Managed File Manifest

Below is the complete manifest of files that CTDF deploys into target repositories. Each file has a **source** (in the plugin) and a **target** (in the user's repo).

### Core Pipelines (GitHub)
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/ci.yml` | `.github/workflows/ci.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/release.yml` | `.github/workflows/release.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/security.yml` | `.github/workflows/security.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/issue-triage.yml` | `.github/workflows/issue-triage.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/status-guard.yml` | `.github/workflows/status-guard.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/CODEOWNERS` | `.github/CODEOWNERS` |

### Core Pipeline (GitLab)
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/templates/gitlab/.gitlab-ci.yml` | `.gitlab-ci.yml` |

### Agentic Pipelines (GitHub)
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/agentic-fleet.yml` | `.github/workflows/agentic-fleet.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/agentic-task.yml` | `.github/workflows/agentic-task.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/agentic-docs.yml` | `.github/workflows/agentic-docs.yml` |

### Agentic Pipelines (GitLab)
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/templates/gitlab/agentic-fleet.gitlab-ci.yml` | `agentic-fleet.gitlab-ci.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/gitlab/agentic-task.gitlab-ci.yml` | `agentic-task.gitlab-ci.yml` |
| `${CLAUDE_PLUGIN_ROOT}/templates/gitlab/agentic-docs.gitlab-ci.yml` | `agentic-docs.gitlab-ci.yml` |

### Scripts
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/scripts/memory_builder.py` | `.claude/scripts/memory_builder.py` |
| `${CLAUDE_PLUGIN_ROOT}/scripts/codebase_analyzer.py` | `.claude/scripts/codebase_analyzer.py` |
| `${CLAUDE_PLUGIN_ROOT}/scripts/agent_runner.py` | `.claude/scripts/agent_runner.py` |

### Prompts
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/templates/prompts/agentic-task-prompt.md` | `.claude/prompts/agentic-task-prompt.md` |
| `${CLAUDE_PLUGIN_ROOT}/templates/prompts/agentic-docs-prompt.md` | `.claude/prompts/agentic-docs-prompt.md` |

### Skills
| Source | Target |
|--------|--------|
| `${CLAUDE_PLUGIN_ROOT}/skills/idea-scout/SKILL.md` | `.claude/skills/idea-scout/SKILL.md` |
| `${CLAUDE_PLUGIN_ROOT}/skills/docs/SKILL.md` | `.claude/skills/docs/SKILL.md` |

### CLAUDE.md
The `<!-- CTDF:START -->` to `<!-- CTDF:END -->` section in `CLAUDE.md`. The canonical content is defined in `${CLAUDE_PLUGIN_ROOT}/skills/setup/SKILL.md`.

## Customizable Files

These files require special handling because they contain user-specific values:

| File | Customized Value | Handling |
|------|-----------------|----------|
| `.github/workflows/agentic-task.yml` | `cron:` schedule expression | Extract before update, re-inject after |
| `.github/workflows/ci.yml` | `[CI_RUNTIME_SETUP]` replaced with real steps | Warn user — always mark as "customized" |
| `.gitlab-ci.yml` | Stages, includes, variables | Warn user — always mark as "customized" |
| `.github/CODEOWNERS` | Team names and paths | Warn user — always mark as "customized" |
| `CLAUDE.md` | Everything outside CTDF markers | Only replace content between `<!-- CTDF:START -->` and `<!-- CTDF:END -->` |

## Instructions

### Step 1: Detect Platform

Determine the platform:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/task_manager.py platform-config
```

Use the `platform` field (`github` or `gitlab`). If no config exists, infer from the presence of `.github/` (→ github) or `.gitlab-ci.yml` (→ gitlab). If neither exists, default to `github`.

### Step 2: Read Plugin Version

```bash
python3 -c "import json; print(json.load(open('${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json'))['version'])"
```

Display this as the source version in the summary.

### Step 3: Determine Scope

If `$ARGUMENTS` specifies a category (`pipelines`, `agentic`, `scripts`, `prompts`, `skills`, `claude-md`), limit the scan to that category only. Otherwise scan all categories.

Filter pipeline categories by the detected platform — only scan GitHub pipeline files for GitHub repos and GitLab pipeline files for GitLab repos.

### Step 4: Scan and Compare Files

For each file in the scoped manifest, run this comparison:

```bash
python3 -c "
import hashlib, sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
name = sys.argv[3]

if not target.exists():
    print(f'{name}|not_installed|')
    sys.exit(0)

if not source.exists():
    print(f'{name}|source_missing|')
    sys.exit(0)

s_hash = hashlib.sha256(source.read_bytes()).hexdigest()
t_hash = hashlib.sha256(target.read_bytes()).hexdigest()

if s_hash == t_hash:
    print(f'{name}|current|')
else:
    print(f'{name}|outdated|')
" "${CLAUDE_PLUGIN_ROOT}/[source-path]" "[target-path]" "[display-name]"
```

Run the above for every file in scope. Collect all results.

**Override statuses for customizable files:**
- If `ci.yml` (GitHub) or `.gitlab-ci.yml` (GitLab) or `CODEOWNERS` shows as `outdated`, change status to `customized`
- If `.github/workflows/agentic-task.yml` shows as `outdated`, keep it as `outdated` but flag it for cron preservation

**For CLAUDE.md**, use this specialized comparison instead:

```bash
python3 -c "
from pathlib import Path
import re, hashlib

claude_md = Path('CLAUDE.md')
if not claude_md.exists():
    print('CLAUDE.md|not_installed|')
    exit(0)

content = claude_md.read_text()
local_match = re.search(r'<!-- CTDF:START -->(.+?)<!-- CTDF:END -->', content, re.DOTALL)
if not local_match:
    print('CLAUDE.md (CTDF section)|not_installed|')
    exit(0)

setup_skill = Path('${CLAUDE_PLUGIN_ROOT}/skills/setup/SKILL.md').read_text()
# Extract the CTDF section from the setup skill template (it appears in a markdown code block)
template_match = re.search(r'<!-- CTDF:START -->(.+?)<!-- CTDF:END -->', setup_skill, re.DOTALL)
if not template_match:
    print('CLAUDE.md (CTDF section)|source_missing|')
    exit(0)

local_hash = hashlib.sha256(local_match.group(0).encode()).hexdigest()
template_hash = hashlib.sha256(template_match.group(0).encode()).hexdigest()

if local_hash == template_hash:
    print('CLAUDE.md (CTDF section)|current|')
else:
    print('CLAUDE.md (CTDF section)|outdated|')
"
```

### Step 5: Present Summary

Display the scan results as a categorized table. Only show categories where at least one file is installed.

```
## CTDF Update Check

**Plugin version:** [version from Step 2]

### [Category Name]
| File | Status |
|------|--------|
| [file path] | Current / Outdated / Customized (has user edits) / Not installed |
...

[Repeat for each category with installed files]

### Summary
- **X** file(s) up to date
- **Y** file(s) outdated (safe to update)
- **Z** file(s) customized (update will require re-applying edits)
- **W** file(s) not installed (available via /setup or /setup agentic-fleet)
```

**If all files are current**, report that everything is up to date and stop — no further steps needed.

**If `$ARGUMENTS` specifies a category**, skip Step 6 (user choice) and go directly to Step 7 to update all outdated files in that category. Still warn about customized files before updating them.

### Step 6: User Choice

Use `AskUserQuestion` with these options:
- **"Update all outdated files"** — update only files with status "outdated" (safe updates)
- **"Update all including customized (preserving custom values)"** — update everything that differs, preserving known custom values (cron expressions, CTDF-only CLAUDE.md replacement)
- **"Choose by category"** — follow up with per-category selection
- **"Cancel"** — abort update

STOP HERE after calling `AskUserQuestion`. Do NOT proceed until the user responds.

**If "Choose by category"** was selected, present a second `AskUserQuestion` listing each category that has outdated or customized files as options, plus "All listed" and "Cancel". STOP and wait for the response.

### Step 7: Execute Updates

For each file selected for update, apply the appropriate update strategy:

#### Direct-Copy Files (scripts, prompts, skills, most workflows)

```bash
cp ${CLAUDE_PLUGIN_ROOT}/[source-path] [target-path]
```

#### agentic-task.yml (GitHub) — Cron Preservation

1. Extract the current cron expression:
```bash
python3 -c "
import re
from pathlib import Path
content = Path('.github/workflows/agentic-task.yml').read_text()
m = re.search(r\"cron:\s*'([^']+)'\", content)
print(m.group(1) if m else '0 */6 * * *')
"
```

2. Copy the template:
```bash
cp ${CLAUDE_PLUGIN_ROOT}/templates/github/workflows/agentic-task.yml .github/workflows/agentic-task.yml
```

3. Re-inject the extracted cron expression:
```bash
python3 -c "
import sys
from pathlib import Path
cron = sys.argv[1]
p = Path('.github/workflows/agentic-task.yml')
content = p.read_text()
p.write_text(content.replace(\"cron: '0 */6 * * *'\", f\"cron: '{cron}'\"))
" "<extracted-cron-value>"
```

#### CLAUDE.md — CTDF Section Only

```bash
python3 -c "
import re
from pathlib import Path

# Read the latest CTDF section from the setup skill template
setup_skill = Path('${CLAUDE_PLUGIN_ROOT}/skills/setup/SKILL.md').read_text()
template_match = re.search(r'(<!-- CTDF:START -->.*?<!-- CTDF:END -->)', setup_skill, re.DOTALL)
if not template_match:
    print('ERROR: Could not find CTDF section in setup skill template')
    exit(1)
new_section = template_match.group(1)

# Replace in the local CLAUDE.md
claude_md = Path('CLAUDE.md')
content = claude_md.read_text()
updated = re.sub(
    r'<!-- CTDF:START -->.*?<!-- CTDF:END -->',
    new_section,
    content,
    flags=re.DOTALL
)
claude_md.write_text(updated)
print('CLAUDE.md CTDF section updated successfully')
"
```

#### Customized Files (ci.yml, CODEOWNERS, .gitlab-ci.yml)

Before updating these files, display a warning:

```
⚠️  **[file-name]** contains user customizations that will be overwritten.
The template version will replace the current file. You will need to re-apply
your project-specific changes (CI runtime steps, team names, etc.) after the update.
```

Then copy the template:
```bash
cp ${CLAUDE_PLUGIN_ROOT}/[source-path] [target-path]
```

### Step 8: Verify

After all updates, confirm each updated file exists and is non-empty:

```bash
python3 -c "
from pathlib import Path
files = [
    # list of updated file paths
]
for f in files:
    p = Path(f)
    if p.exists() and p.stat().st_size > 0:
        print(f'  ✓ {f}')
    else:
        print(f'  ✗ {f} — MISSING or empty')
"
```

For `agentic-task.yml`, verify the cron was properly injected:
```bash
python3 -c "
import re
from pathlib import Path
content = Path('.github/workflows/agentic-task.yml').read_text()
m = re.search(r\"cron:\s*'([^']+)'\", content)
print(f'  Cron preserved: {m.group(1)}' if m else '  ✗ Cron injection failed')
"
```

For `CLAUDE.md`, verify markers are intact:
```bash
python3 -c "
from pathlib import Path
content = Path('CLAUDE.md').read_text()
has_start = '<!-- CTDF:START -->' in content
has_end = '<!-- CTDF:END -->' in content
if has_start and has_end:
    print('  ✓ CLAUDE.md CTDF markers intact')
else:
    print('  ✗ CLAUDE.md CTDF markers broken')
"
```

### Step 9: Report

Present a final summary:

```
## CTDF Update Complete

**Plugin version:** [version]

### Files Updated
| File | Action |
|------|--------|
| [file path] | Updated to latest template |
| .github/workflows/agentic-task.yml | Updated (cron preserved: [cron]) |
| CLAUDE.md | CTDF section updated |
...

### Files Skipped
| File | Reason |
|------|--------|
| [file path] | Already current |
...

### Not Installed
These files are available but were never deployed. Use the indicated command to install them:
| File | Install With |
|------|-------------|
| [file path] | `/setup agentic-fleet` |
...

### Next Steps
1. Review the changes: `git diff`
2. Commit the updates
3. Push to apply updated pipelines
```

---

## Important Rules

1. **NEVER create files that weren't already installed** — only update existing files. For new installations, suggest `/setup` or `/setup agentic-fleet`
2. **Always preserve cron expressions** in `agentic-task.yml` (GitHub) during updates
3. **Only touch the CTDF:START/END section** in CLAUDE.md — never modify content outside those markers
4. **Warn before overwriting customizable files** (`ci.yml`, `CODEOWNERS`, `.gitlab-ci.yml`) — these contain user-specific values
5. **Idempotent** — running the skill twice with no plugin changes should report everything as current
6. **Cross-platform** — use `python3` for all file operations (no Unix-only commands like `diff`)
7. **All output in English**
8. **Read files before modifying them** — never blindly overwrite
