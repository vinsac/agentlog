"""
Context filtering by importance/priority.

Helps AI agents focus on the most relevant logs by assigning
importance scores and filtering accordingly.
"""

from typing import Any, Dict, List, Optional


# Priority levels for different tags
TAG_PRIORITY = {
    "error": 10,      # Highest priority - failures
    "check": 9,       # Failed assertions
    "llm": 8,         # LLM calls (expensive, important)
    "tool": 8,        # Tool calls (agent actions)
    "decision": 7,    # Control flow decisions
    "diff": 6,        # State changes
    "flow": 5,        # Data transformations
    "func": 4,        # Function tracing
    "query": 4,       # Database queries
    "http": 4,        # HTTP requests
    "span": 3,        # Named spans
    "prompt": 7,      # Prompts (important for agent context)
    "response": 7,    # Responses (important for agent context)
    "info": 2,        # General info
    "vars": 1,        # Variable inspection
    "state": 1,       # State snapshots
    "perf": 1,        # Performance metrics
}


def get_entry_priority(entry: Dict[str, Any]) -> int:
    """
    Calculate priority score for a log entry.
    
    Higher score = more important for AI agents.
    
    Args:
        entry: Log entry dictionary
        
    Returns:
        Priority score (0-10)
    """
    tag = entry.get("tag", "info")
    base_priority = TAG_PRIORITY.get(tag, 2)
    
    # Boost priority for certain conditions
    boost = 0
    
    # Errors always highest priority
    if "error" in entry:
        boost += 3
    
    # Failed checks are important
    if tag == "check" and not entry.get("passed", True):
        boost += 2
    
    # Slow operations are important
    if "ms" in entry and entry["ms"] > 1000:
        boost += 1
    
    # Large token usage is important (expensive LLM calls)
    if "tokens_out" in entry and entry["tokens_out"] > 1000:
        boost += 1
    
    return min(10, base_priority + boost)


def filter_by_priority(
    entries: List[Dict[str, Any]],
    min_priority: int = 5
) -> List[Dict[str, Any]]:
    """
    Filter entries by minimum priority level.
    
    Args:
        entries: List of log entries
        min_priority: Minimum priority (0-10)
        
    Returns:
        Filtered list of entries
        
    Example:
        # Get only high-priority entries (errors, decisions, LLM calls)
        important = filter_by_priority(entries, min_priority=7)
    """
    return [e for e in entries if get_entry_priority(e) >= min_priority]


def filter_by_importance(
    entries: List[Dict[str, Any]],
    importance: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Filter entries by importance level.
    
    Args:
        entries: List of log entries
        importance: "low", "medium", "high", or "critical"
        
    Returns:
        Filtered list of entries
        
    Example:
        # Get only critical entries (errors, failed checks)
        critical = filter_by_importance(entries, "critical")
    """
    thresholds = {
        "low": 0,       # All entries
        "medium": 4,    # Skip vars, state, perf
        "high": 7,      # Only errors, checks, decisions, LLM/tool calls
        "critical": 9,  # Only errors and failed checks
    }
    
    min_priority = thresholds.get(importance, 4)
    return filter_by_priority(entries, min_priority)


def get_top_entries(
    entries: List[Dict[str, Any]],
    n: int = 50
) -> List[Dict[str, Any]]:
    """
    Get the top N most important entries.
    
    Sorts by priority and returns the most important entries.
    Maintains chronological order within the result.
    
    Args:
        entries: List of log entries
        n: Number of entries to return
        
    Returns:
        Top N entries in chronological order
        
    Example:
        # Get 20 most important entries
        top = get_top_entries(entries, n=20)
    """
    # Add priority scores
    scored = [(get_entry_priority(e), e) for e in entries]
    
    # Sort by priority (descending), then by sequence (ascending)
    scored.sort(key=lambda x: (-x[0], x[1].get("seq", 0)))
    
    # Take top N
    top = [e for _, e in scored[:n]]
    
    # Restore chronological order
    top.sort(key=lambda e: e.get("seq", 0))
    
    return top


def compress_entry(entry: Dict[str, Any], max_value_length: int = 100) -> Dict[str, Any]:
    """
    Compress a log entry by truncating large values.
    
    Reduces token usage while preserving structure and type information.
    
    Args:
        entry: Log entry to compress
        max_value_length: Maximum length for string values
        
    Returns:
        Compressed entry
    """
    compressed = entry.copy()
    
    def compress_value(val: Any) -> Any:
        """Recursively compress values."""
        if isinstance(val, dict):
            # Check if it's a value descriptor
            if "t" in val and "v" in val:
                # Keep type, truncate value if string
                if val["t"] == "str" and isinstance(val.get("v"), str):
                    v = val["v"]
                    if len(v) > max_value_length:
                        return {
                            "t": "str",
                            "v": v[:max_value_length],
                            "truncated": len(v)
                        }
                # Truncate list values
                elif val["t"] == "list" and isinstance(val.get("v"), list):
                    v = val["v"]
                    if len(v) > 10:
                        return {
                            "t": "list",
                            "v": v[:10],
                            "n": len(v),
                            "truncated": len(v)
                        }
                return val
            else:
                # Regular dict, compress recursively
                return {k: compress_value(v) for k, v in val.items()}
        elif isinstance(val, list):
            # Compress list items
            return [compress_value(item) for item in val[:10]]  # Max 10 items
        elif isinstance(val, str) and len(val) > max_value_length:
            return val[:max_value_length] + "..."
        else:
            return val
    
    # Compress context fields
    for key in ["ctx", "locals", "args"]:
        if key in compressed:
            compressed[key] = compress_value(compressed[key])
    
    return compressed


def smart_filter(
    entries: List[Dict[str, Any]],
    max_tokens: int = 4000,
    importance: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Smart filtering that combines importance and token budget.
    
    1. Filter by importance
    2. Compress entries
    3. Fit within token budget
    
    Args:
        entries: List of log entries
        max_tokens: Token budget
        importance: Importance level
        
    Returns:
        Filtered and compressed entries
        
    Example:
        # Get important entries within budget
        filtered = smart_filter(entries, max_tokens=2000, importance="high")
    """
    from ._tokens import fit_entries_to_budget
    
    # Step 1: Filter by importance
    important = filter_by_importance(entries, importance)
    
    # Step 2: Compress entries
    compressed = [compress_entry(e, max_value_length=100) for e in important]
    
    # Step 3: Fit within token budget
    return fit_entries_to_budget(compressed, max_tokens)
