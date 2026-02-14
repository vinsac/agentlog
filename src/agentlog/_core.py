"""
Core configuration for agentlog.

Handles enable/disable, environment variable detection, log levels,
and global state management.
"""

import os
from typing import Optional


# ---------------------------------------------------------------------------
# Log Levels
# ---------------------------------------------------------------------------
# debug < info < warn < error
# Each tag maps to a level. When AGENTLOG_LEVEL is set, only tags at or
# above that level are emitted.

LEVEL_DEBUG = 0
LEVEL_INFO = 1
LEVEL_WARN = 2
LEVEL_ERROR = 3

LEVEL_NAMES = {"debug": LEVEL_DEBUG, "info": LEVEL_INFO, "warn": LEVEL_WARN, "error": LEVEL_ERROR}

# Map each tag to its log level
TAG_LEVELS = {
    "vars": LEVEL_DEBUG,
    "state": LEVEL_DEBUG,
    "flow": LEVEL_DEBUG,
    "diff": LEVEL_DEBUG,
    "perf": LEVEL_DEBUG,
    "info": LEVEL_INFO,
    "http": LEVEL_INFO,
    "query": LEVEL_INFO,
    "func": LEVEL_INFO,
    "decision": LEVEL_INFO,
    "span": LEVEL_INFO,
    "trace": LEVEL_INFO,
    "llm": LEVEL_INFO,      # Phase 2: LLM calls
    "tool": LEVEL_INFO,     # Phase 2: Tool calls
    "prompt": LEVEL_INFO,   # Phase 2: Prompts
    "response": LEVEL_INFO, # Phase 2: Responses
    "check": LEVEL_WARN,
    "error": LEVEL_ERROR,
}


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

_enabled: Optional[bool] = None
_level: int = LEVEL_DEBUG
_tag_prefix: str = "AGENTLOG"


def _detect_enabled() -> bool:
    """Check environment variables to determine if agentlog is enabled."""
    for var in ("AGENTLOG", "DEVLOG", "CURIIOS_DEV_LOGGING"):
        val = os.getenv(var, "").lower()
        if val in ("true", "1", "yes", "on"):
            return True
    return False


def _detect_level() -> int:
    """Check AGENTLOG_LEVEL env var."""
    val = os.getenv("AGENTLOG_LEVEL", "").lower()
    return LEVEL_NAMES.get(val, LEVEL_DEBUG)


def is_enabled() -> bool:
    """Check if agentlog is enabled. Cached after first call."""
    global _enabled
    if _enabled is None:
        _enabled = _detect_enabled()
        global _level
        _level = _detect_level()
    return _enabled


def should_emit(tag: str) -> bool:
    """Check if a tag should be emitted based on current level."""
    if not is_enabled():
        return False
    tag_level = TAG_LEVELS.get(tag, LEVEL_INFO)
    return tag_level >= _level


def enable() -> None:
    """Programmatically enable agentlog (for tests, REPL, notebooks)."""
    global _enabled
    _enabled = True


def disable() -> None:
    """Programmatically disable agentlog."""
    global _enabled
    _enabled = False


def configure(
    level: Optional[str] = None,
    tag_prefix: Optional[str] = None,
) -> None:
    """
    Configure agentlog settings.

    Args:
        level: Minimum log level ("debug", "info", "warn", "error").
        tag_prefix: Prefix for log tags (default "AGENTLOG").
    """
    global _level, _tag_prefix
    if level is not None:
        _level = LEVEL_NAMES.get(level.lower(), LEVEL_DEBUG)
    if tag_prefix is not None:
        _tag_prefix = tag_prefix


def get_tag_prefix() -> str:
    """Get the current tag prefix."""
    return _tag_prefix
