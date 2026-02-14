"""
Structured output templates for agentlog (Phase 4).

Export formats optimized for specific agent tools' context windows and prompt styles.
"""

import json
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Template Definitions
# ---------------------------------------------------------------------------

def _cursor_template(entries: List[Dict[str, Any]], header: Dict[str, Any]) -> str:
    """
    Cursor-optimized format.
    
    Cursor prefers compact JSON with clear section headers.
    Optimized for their agent context window.
    """
    lines = ["# AgentLog Debug Context"]
    
    if header.get("session_id"):
        lines.append(f"Session: {header['session_id']}")
    
    if header.get("git"):
        git = header["git"]
        lines.append(f"Git: {git.get('branch', '?')}@{git.get('commit', '?')[:7]}")
    
    if header.get("tokens"):
        t = header["tokens"]
        lines.append(f"Tokens: {t.get('total', 0)} total")
    
    lines.append("")
    lines.append("## Events")
    
    for entry in entries:
        tag = entry.get("tag", "?")
        lines.append(f"\n[{tag.upper()}]")
        
        # Compact JSON for the entry
        entry_json = json.dumps(entry, default=str, separators=(',', ':'))
        lines.append(entry_json[:500])  # Limit per entry
    
    return "\n".join(lines)


def _claude_template(entries: List[Dict[str, Any]], header: Dict[str, Any]) -> str:
    """
    Claude-optimized format.
    
    Claude prefers XML-style tags with clear structure.
    Optimized for Claude Code context window.
    """
    lines = ["<debug_context>"]
    
    lines.append("  <metadata>")
    if header.get("session_id"):
        lines.append(f"    <session>{header['session_id']}</session>")
    if header.get("git"):
        git = header["git"]
        lines.append(f"    <git_branch>{git.get('branch', '?')}</git_branch>")
        lines.append(f"    <git_commit>{git.get('commit', '?')[:7]}</git_commit>")
    if header.get("tokens"):
        t = header["tokens"]
        lines.append(f"    <total_tokens>{t.get('total', 0)}</total_tokens>")
    lines.append("  </metadata>")
    
    lines.append("  <events>")
    for entry in entries:
        tag = entry.get("tag", "?")
        lines.append(f'    <event type="{tag}">')
        
        # Convert entry to XML-style attributes
        for key, value in entry.items():
            if key != "tag" and isinstance(value, (str, int, float, bool)):
                lines.append(f'      <{key}>{value}</{key}>')
        
        lines.append(f"    </event>")
    lines.append("  </events>")
    
    lines.append("</debug_context>")
    
    return "\n".join(lines)


def _codex_template(entries: List[Dict[str, Any]], header: Dict[str, Any]) -> str:
    """
    Codex-optimized format.
    
    Codex (OpenAI) prefers markdown with code blocks.
    Optimized for their agent context window.
    """
    lines = ["## Debug Context"]
    
    if header.get("session_id"):
        lines.append(f"**Session:** `{header['session_id']}`")
    
    if header.get("git"):
        git = header["git"]
        lines.append(f"**Git:** `{git.get('branch', '?')}@{git.get('commit', '?')[:7]}`")
    
    lines.append("")
    lines.append("### Events")
    lines.append("")
    
    for entry in entries:
        tag = entry.get("tag", "?")
        lines.append(f"**{tag.upper()}**:")
        lines.append("```json")
        entry_json = json.dumps(entry, default=str, indent=2)
        lines.append(entry_json[:800])  # Longer limit for Codex
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines)


def _raw_template(entries: List[Dict[str, Any]], header: Dict[str, Any]) -> str:
    """Raw JSONL format (default)."""
    lines = []
    
    # Header as comment
    header_line = f"# agentlog debug context"
    if header.get("session_id"):
        header_line += f" (session: {header['session_id']})"
    lines.append(header_line)
    
    # Git info
    if header.get("git"):
        git = header["git"]
        if git.get("commit"):
            branch = git.get("branch", "?")
            commit_short = git["commit"][:7]
            dirty = " dirty" if git.get("dirty") else ""
            lines.append(f"# git: {branch}@{commit_short}{dirty}")
    
    # Token summary
    if header.get("tokens"):
        t = header["tokens"]
        if t.get("total", 0) > 0:
            models = ", ".join(
                f"{m}: {d.get('in', 0)}in/{d.get('out', 0)}out"
                for m, d in t.get("by_model", {}).items()
            )
            lines.append(f"# tokens: {t['total']} total ({models})")
    
    # Entries as JSONL
    for entry in entries:
        line = json.dumps(entry, default=str, separators=(',', ':'))
        lines.append(line)
    
    return "\n".join(lines)


# Template registry
_TEMPLATES = {
    "cursor": _cursor_template,
    "claude": _claude_template,
    "codex": _codex_template,
    "raw": _raw_template,
    "jsonl": _raw_template,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_formatted_context(
    format: str = "raw",
    max_tokens: int = 4000,
    tags: Optional[List[str]] = None
) -> str:
    """
    Export context in a tool-specific format.
    
    Args:
        format: Output format - 'cursor', 'claude', 'codex', 'raw', 'jsonl'
        max_tokens: Approximate token budget
        tags: Optional filter by tags
        
    Returns:
        Formatted context string
        
    Example:
        >>> context = get_formatted_context("cursor", max_tokens=2000)
        >>> context = get_formatted_context("claude", tags=["error", "decision"])
    """
    from ._buffer import get_context, token_summary
    from ._session import get_session_id
    from ._git import get_git_info
    from ._tokens import estimate_tokens
    
    # Get raw context
    raw_context = get_context(max_tokens=max_tokens, tags=tags)
    
    if not raw_context:
        # Return empty template
        template_fn = _TEMPLATES.get(format, _raw_template)
        return template_fn([], {
            "session_id": get_session_id(),
            "git": get_git_info(),
            "tokens": token_summary()
        })
    
    # Parse entries
    entries = []
    for line in raw_context.strip().split('\n'):
        if line.startswith('#'):
            continue
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    # Build header
    header = {
        "session_id": get_session_id(),
        "git": get_git_info(),
        "tokens": token_summary()
    }
    
    # Apply template
    template_fn = _TEMPLATES.get(format, _raw_template)
    return template_fn(entries, header)


def list_formats() -> List[str]:
    """List available output formats."""
    return list(_TEMPLATES.keys())


def get_format_description(format: str) -> str:
    """Get description of a format."""
    descriptions = {
        "cursor": "Optimized for Cursor IDE agent context",
        "claude": "Optimized for Claude Code agent context (XML-style)",
        "codex": "Optimized for OpenAI Codex agent context (markdown)",
        "raw": "Raw JSONL format with comments",
        "jsonl": "Raw JSONL format (alias for raw)",
    }
    return descriptions.get(format, "Unknown format")


# ---------------------------------------------------------------------------
# MCP Server Integration Helpers
# ---------------------------------------------------------------------------

def to_mcp_resource() -> Dict[str, Any]:
    """
    Format current context as MCP resource.
    
    Returns:
        MCP resource structure for Claude Desktop
    """
    from ._buffer import get_context
    from ._session import get_session_id
    
    session_id = get_session_id() or "unknown"
    context = get_context(max_tokens=8000)
    
    return {
        "uri": f"agentlog://debug/{session_id}",
        "mimeType": "application/x-ndjson",
        "text": context
    }


def to_mcp_tool_result() -> Dict[str, Any]:
    """
    Format current context as MCP tool result.
    
    Returns:
        MCP tool result structure
    """
    from ._buffer import get_debug_context
    
    context = get_debug_context(max_tokens=8000)
    
    return {
        "content": [
            {
                "type": "text",
                "text": context
            }
        ]
    }
