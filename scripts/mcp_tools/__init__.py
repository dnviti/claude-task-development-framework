"""MCP tool handler implementations for the CTDF vector memory MCP server.

Each submodule exposes a ``register(server)`` function that adds its tool(s)
to the MCP ``Server`` instance.

Modules:
    index         — index_repository tool
    search        — semantic_search tool
    store         — store_memory tool
    task_context  — get_task_context tool
"""

import json
from pathlib import Path

# Common script directory reference (parent of mcp_tools/ = scripts/)
SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def is_enabled(root: str | Path = ".") -> bool:
    """Check whether vector memory is enabled in project configuration.

    Reads ``vector_memory.enabled`` from the project config file.  Returns
    ``True`` when the flag is explicitly ``true`` or when no config file
    exists (default-on behaviour).  Returns ``False`` only when the flag is
    explicitly set to ``false``, giving users an opt-out mechanism
    independent of installed dependencies.

    This utility is intended for defensive checks inside individual tool
    modules and the MCP server startup path.
    """
    root_path = Path(root).resolve()
    config_paths = [
        root_path / ".claude" / "project-config.json",
        root_path / "config" / "project-config.json",
    ]
    for cp in config_paths:
        if cp.exists():
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                vm_cfg = data.get("vector_memory", {})
                # Explicit False means disabled; anything else (True,
                # missing key, missing section) means enabled.
                return vm_cfg.get("enabled", True) is not False
            except (json.JSONDecodeError, OSError):
                pass
    # No config found — default to enabled
    return True
