---
title: CTDF Documentation
description: Complete technical documentation for the Claude Task Development Framework
generated-by: ctdf-docs
generated-at: 2026-03-18T18:00:00Z
source-files:
  - README.md
  - .claude-plugin/plugin.json
---

# CTDF — Claude Task Development Framework

A project-agnostic task and release management framework with 8 streamlined skills: `/task`, `/idea`, `/release`, `/docs`, `/setup`, `/update`, `/tests`, `/help`. Features a gated release pipeline with automatic subagent orchestration — all through plain-text files and slash commands.

## Table of Contents

| Section | Description |
|---------|-------------|
| [Architecture](architecture.md) | System architecture, component diagrams, data flow |
| [Getting Started](getting-started.md) | Installation, prerequisites, first run |
| [Configuration](configuration.md) | Config files, environment variables, feature flags |
| [API Reference](api-reference.md) | Skills, script CLIs, hooks |
| [Deployment](deployment.md) | CI/CD pipelines, Docker, agentic fleet |
| [Development](development.md) | Contributing, local dev, testing, conventions |
| [Troubleshooting](troubleshooting.md) | Common errors, debugging, FAQ |
| [MCP Vector Memory](mcp-vector-memory.md) | Semantic search, MCP server, embedding providers, multi-agent coordination |
| [LLM Context](llm-context.md) | Consolidated reference for LLM/bot consumption |

## Quick Start

```bash
# Install the plugin
/plugin marketplace add https://github.com/dnviti/claude-task-development-framework
/plugin install ctdf@dnviti-claude-task-development-framework

# Set up your project
/setup "My Project"

# Start working
/idea create "Add user authentication"
/idea approve IDEA-AUTH-0001
/task pick AUTH-0001
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3 (stdlib only, zero dependencies) |
| Host | Claude Code CLI |
| Version Control | Git (worktrees, branches, tags) |
| Platform | GitHub Actions / GitLab CI/CD |
| AI Providers | Claude, OpenAI Codex, OpenClaw |
| MCP Server | Vector memory semantic search (stdio transport) |
| Data Format | Plain-text files (`.txt`) + JSON configs |

## Supported Platforms

| Platform | Status |
|----------|--------|
| Claude Code | Supported |
| OpenCode | Supported |
| OpenClaw | Supported |
| Cursor | Supported |
| Windsurf | Supported |
| Continue.dev | Supported |
| GitHub Copilot | Supported |
| Aider | Supported |

## Skills Overview

| Skill | Purpose |
|-------|---------|
| `/task` | Task lifecycle: pick, create, continue, schedule, status |
| `/idea` | Idea lifecycle: create, approve, disapprove, refactor, scout |
| `/release` | Release pipeline: create, generate, continue, close |
| `/docs` | Documentation: generate, sync, reset, publish |
| `/setup` | Project initialization and configuration |
| `/update` | Update CTDF-managed files |
| `/tests` | Test discovery, gaps, coverage, execution |
| `/help` | Usage guide |

## Key Design Principles

1. **Project-agnostic** — Works with any language, framework, or tech stack
2. **Zero dependencies** — All scripts use Python 3 stdlib only
3. **Human-in-the-loop** — AI assists, but users decide at every gate
4. **Plain-text first** — Tasks and ideas in simple `.txt` files
5. **Cross-platform** — Linux, macOS, Windows with auto OS detection

## Version

Current plugin version: **3.5.2**

Repository: [github.com/dnviti/claude-task-development-framework](https://github.com/dnviti/claude-task-development-framework)

License: MIT
