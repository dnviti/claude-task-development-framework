"""Social media platform adapters for CTDF release announcements.

Each module provides a concrete SocialPlatform subclass that handles
posting release announcements to a specific social media platform.

Available platforms:
    bluesky   -- AT Protocol posting (app password auth)
    mastodon  -- Mastodon API posting (OAuth token auth)
    discord   -- Discord webhook posting
    slack     -- Slack webhook posting
    clipboard -- Cross-platform clipboard copy for manual-post platforms

Zero external dependencies -- stdlib only.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class SocialPlatform(ABC):
    """Base class for social media platform adapters."""

    name: str = ""
    env_vars: list[str] = []
    max_length: int = 0  # 0 = unlimited

    @abstractmethod
    def post(self, message: str) -> dict[str, Any]:
        """Post a message to this platform.

        Returns:
            dict with keys: success (bool), platform (str), message (str),
            and optionally url (str) or error (str).
        """

    def check_credentials(self) -> dict[str, str]:
        """Check credential status for this platform.

        Returns:
            dict mapping env var names to 'set' or 'missing'.
        """
        status = {}
        for var in self.env_vars:
            status[var] = "set" if os.environ.get(var) else "missing"
        return status

    def is_configured(self) -> bool:
        """Return True if all required credentials are available."""
        return all(os.environ.get(var) for var in self.env_vars)


# ── Platform registry ────────────────────────────────────────────────────

_REGISTRY: dict[str, type[SocialPlatform]] = {}


def register(cls: type[SocialPlatform]) -> type[SocialPlatform]:
    """Decorator to register a platform class."""
    _REGISTRY[cls.name] = cls
    return cls


def get_platform(name: str) -> SocialPlatform:
    """Instantiate and return a platform by name."""
    if name not in _REGISTRY:
        raise ValueError(f"Unknown platform: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]()


def list_platforms() -> list[dict[str, Any]]:
    """Return info about all registered platforms."""
    platforms = []
    for name, cls in sorted(_REGISTRY.items()):
        instance = cls()
        platforms.append({
            "name": name,
            "max_length": instance.max_length,
            "env_vars": instance.env_vars,
            "credentials": instance.check_credentials(),
            "configured": instance.is_configured(),
        })
    return platforms


# ── Import platform modules to trigger registration ──────────────────────

from . import bluesky   # noqa: E402, F401
from . import mastodon  # noqa: E402, F401
from . import discord   # noqa: E402, F401
from . import slack     # noqa: E402, F401
from . import clipboard # noqa: E402, F401
