"""
Intelligent context pruning for agentlog.

AI-powered log summarization to fit within token budgets.
Uses heuristics to identify and preserve the most important information.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter


# ---------------------------------------------------------------------------
# Importance Scoring
# ---------------------------------------------------------------------------

def score_entry_importance(entry: Dict[str, Any]) -> int:
    """
    Score an entry's importance for retention.
    
    Higher score = more important to keep.
    
    Args:
        entry: Log entry dict
        
    Returns:
        Importance score (0-100)
    """
    tag = entry.get("tag", "")
    score = 0
    
    # Base scores by tag
    tag_scores = {
        "error": 100,
        "session": 90,
        "check": 80,
        "llm": 70,
        "tool": 60,
        "decision": 50,
        "trace": 40,
        "query": 30,
        "http": 25,
        "func": 20,
        "perf": 15,
        "info": 10,
        "debug": 5,
    }
    score += tag_scores.get(tag, 10)
    
    # Boost for failed checks
    if tag == "check" and not entry.get("passed", True):
        score += 30
    
    # Boost for failed tools
    if tag == "tool" and not entry.get("success", True):
        score += 25
    
    # Boost for errors with context
    if tag == "error":
        if entry.get("locals"):
            score += 10
        if entry.get("session_id"):
            score += 5
    
    # Boost for recent entries (handled separately by time ordering)
    
    return min(score, 100)


# ---------------------------------------------------------------------------
# Entry Compression
# ---------------------------------------------------------------------------

def compress_entry(entry: Dict[str, Any], aggressiveness: str = "medium") -> Dict[str, Any]:
    """
    Compress an entry by removing less important fields.
    
    Args:
        entry: Original entry
        aggressiveness: "low", "medium", "high"
        
    Returns:
        Compressed entry
    """
    if aggressiveness == "low":
        return entry
    
    compressed = {
        "tag": entry.get("tag"),
        "ts": entry.get("ts"),
    }
    
    # Always keep seq if present
    if "seq" in entry:
        compressed["seq"] = entry["seq"]
    
    tag = entry.get("tag", "")
    
    # Tag-specific compression
    if tag == "error":
        compressed["error"] = entry.get("error")
        if "fn" in entry:
            compressed["fn"] = entry["fn"]
        if "file" in entry:
            compressed["file"] = entry["file"]
        if "line" in entry:
            compressed["line"] = entry["line"]
        # Include locals keys only for high compression
        if "locals" in entry:
            if aggressiveness == "high":
                compressed["locals_keys"] = list(entry["locals"].keys())[:10]
            else:
                compressed["locals"] = _truncate_locals(entry["locals"])
    
    elif tag == "llm":
        compressed["model"] = entry.get("model")
        compressed["tokens_in"] = entry.get("tokens_in")
        compressed["tokens_out"] = entry.get("tokens_out")
        if "ms" in entry:
            compressed["ms"] = entry["ms"]
        # Drop prompt/response for high compression
        if aggressiveness != "high":
            if "prompt" in entry:
                compressed["prompt"] = _truncate_value(entry["prompt"], 100)
    
    elif tag == "tool":
        compressed["tool"] = entry.get("tool")
        compressed["success"] = entry.get("success")
        if "ms" in entry:
            compressed["ms"] = entry["ms"]
        # Truncate stdout/stderr
        if "sys" in entry:
            sys = entry["sys"]
            compressed["sys"] = {
                k: _truncate_value(v, 200) if isinstance(v, str) else v
                for k, v in sys.items() if k in ["stdout", "stderr", "exit_code"]
            }
    
    elif tag == "session":
        compressed["action"] = entry.get("action")
        compressed["session_id"] = entry.get("session_id")
        if "agent" in entry:
            compressed["agent"] = entry["agent"]
        # Summarize git info
        if "git" in entry:
            git = entry["git"]
            compressed["git"] = {
                "commit": git.get("commit", "")[:7] if git.get("commit") else None,
                "branch": git.get("branch"),
                "dirty": git.get("dirty")
            }
    
    else:
        # Generic: keep msg and minimal context
        if "msg" in entry:
            compressed["msg"] = _truncate_value(entry["msg"], 100)
        if "ctx" in entry and aggressiveness != "high":
            compressed["ctx"] = _truncate_context(entry["ctx"])
    
    return compressed


def _truncate_locals(locals_dict: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
    """Truncate locals dict to most important entries."""
    if len(locals_dict) <= max_items:
        return locals_dict
    
    # Keep simple values, truncate complex ones
    result = {}
    for i, (k, v) in enumerate(locals_dict.items()):
        if i >= max_items:
            break
        if isinstance(v, dict) and "t" in v:
            # Already a value descriptor
            result[k] = {"t": v["t"]}
            if "v" in v and len(str(v["v"])) < 50:
                result[k]["v"] = v["v"]
        else:
            result[k] = _truncate_value(v, 50)
    
    return result


def _truncate_context(ctx: Dict[str, Any], max_items: int = 3) -> Dict[str, Any]:
    """Truncate context dict."""
    return {k: _truncate_value(v, 50) for i, (k, v) in enumerate(ctx.items()) if i < max_items}


def _truncate_value(value: Any, max_len: int = 100) -> Any:
    """Truncate a value to max length."""
    s = str(value)
    if len(s) > max_len:
        return s[:max_len] + f"...[{len(s)} chars]"
    return value


# ---------------------------------------------------------------------------
# Smart Summarization
# ---------------------------------------------------------------------------

def summarize_entries(
    entries: List[Dict[str, Any]],
    max_entries: int = 20,
    max_tokens: int = 4000
) -> Dict[str, Any]:
    """
    Create a smart summary of entries.
    
    Args:
        entries: List of log entries
        max_entries: Maximum entries to include
        max_tokens: Approximate token budget
        
    Returns:
        Summary dict with condensed information
    """
    if not entries:
        return {"summary": "No entries", "total": 0}
    
    # Score all entries
    scored = [(score_entry_importance(e), e) for e in entries]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Count by tag
    tag_counts = Counter(e.get("tag", "unknown") for e in entries)
    
    # Extract key errors
    errors = [
        e for e in entries
        if e.get("tag") == "error"
    ][:5]
    
    # Extract decisions
    decisions = [
        e for e in entries
        if e.get("tag") == "decision"
    ][:5]
    
    # Calculate total tokens (rough estimate)
    total_chars = sum(len(json.dumps(e, default=str)) for e in entries)
    estimated_tokens = total_chars // 4
    
    # Select top entries by importance
    selected = scored[:max_entries]
    selected.sort(key=lambda x: x[1].get("ts", 0))  # Re-sort by time
    
    summary = {
        "summary": f"{len(entries)} entries, {len(errors)} errors",
        "total": len(entries),
        "by_tag": dict(tag_counts),
        "estimated_tokens": estimated_tokens,
        "compressed_to": len(selected),
        "key_errors": [
            {
                "type": e.get("error", {}).get("type"),
                "msg": e.get("error", {}).get("msg", "")[:100],
                "file": e.get("file"),
                "line": e.get("line")
            }
            for e in errors
        ],
        "key_decisions": [
            {
                "question": e.get("question", "")[:100],
                "answer": e.get("answer")
            }
            for e in decisions
        ],
        "entries": [e for _, e in selected]
    }
    
    return summary


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def prune_context(
    entries: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 4000,
    strategy: str = "smart"
) -> str:
    """
    Prune context to fit within token budget.
    
    Args:
        entries: Log entries (default: from buffer)
        max_tokens: Target token budget
        strategy: "smart", "recent", "errors_only"
        
    Returns:
        JSON string of pruned context
        
    Example:
        >>> pruned = prune_context(max_tokens=2000, strategy="smart")
        >>> print(pruned)
    """
    from ._buffer import get_context
    
    if entries is None:
        raw = get_context(max_tokens=max_tokens * 2)  # Get more to work with
        entries = []
        for line in raw.strip().split('\n'):
            if line and not line.startswith('#'):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    if not entries:
        return json.dumps({"summary": "No entries to prune"})
    
    if strategy == "errors_only":
        # Keep only errors and session info
        filtered = [e for e in entries if e.get("tag") in ("error", "session", "check")]
        result = {
            "strategy": "errors_only",
            "total_pruned": len(entries) - len(filtered),
            "entries": filtered
        }
    
    elif strategy == "recent":
        # Keep most recent entries
        entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
        # Estimate how many fit
        total_chars = 0
        selected = []
        for e in entries:
            char_len = len(json.dumps(e, default=str))
            if total_chars + char_len < max_tokens * 4:
                selected.append(e)
                total_chars += char_len
            else:
                break
        result = {
            "strategy": "recent",
            "total_pruned": len(entries) - len(selected),
            "entries": list(reversed(selected))  # Oldest first
        }
    
    else:  # smart
        summary = summarize_entries(entries, max_tokens=max_tokens // 100)
        result = {
            "strategy": "smart",
            "summary": summary["summary"],
            "by_tag": summary["by_tag"],
            "key_errors": summary.get("key_errors", []),
            "key_decisions": summary.get("key_decisions", []),
            "entries": summary["entries"]
        }
    
    return json.dumps(result, default=str, separators=(',', ':'))


def compress_context(
    max_tokens: int = 4000,
    aggressiveness: str = "medium"
) -> str:
    """
    Compress context by removing less important fields.
    
    Args:
        max_tokens: Target token budget
        aggressiveness: "low", "medium", "high"
        
    Returns:
        JSONL string of compressed entries
    """
    from ._buffer import get_context
    
    raw = get_context(max_tokens=max_tokens * 3)
    entries = []
    for line in raw.strip().split('\n'):
        if line and not line.startswith('#'):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    # Score and sort by importance
    scored = [(score_entry_importance(e), e) for e in entries]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Select and compress until we hit budget
    total_chars = 0
    selected = []
    for score, entry in scored:
        compressed = compress_entry(entry, aggressiveness)
        char_len = len(json.dumps(compressed, default=str))
        
        if total_chars + char_len < max_tokens * 4:
            selected.append((entry.get("ts", 0), compressed))
            total_chars += char_len
    
    # Sort by time
    selected.sort(key=lambda x: x[0])
    
    # Output as JSONL
    lines = [json.dumps(e, default=str, separators=(',', ':')) for _, e in selected]
    return '\n'.join(lines)


def get_context_summary() -> Dict[str, Any]:
    """
    Get a quick summary of current context without full export.
    
    Returns:
        Summary dict
    """
    from ._buffer import get_context
    from ._session import get_session_id
    
    raw = get_context(max_tokens=10000)
    entries = []
    for line in raw.strip().split('\n'):
        if line and not line.startswith('#'):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    summary = summarize_entries(entries, max_entries=len(entries))
    summary["session_id"] = get_session_id()
    
    return summary
