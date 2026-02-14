"""
Error pattern detection and cross-run correlation for agentlog.

Enables agents to recognize recurring failures by hashing error signatures
and correlating across sessions.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path


# ---------------------------------------------------------------------------
# Error Pattern Hashing
# ---------------------------------------------------------------------------

def hash_error(error_type: str, filename: str, line: int) -> str:
    """
    Generate a unique hash for an error pattern.
    
    Args:
        error_type: Exception type name (e.g., 'ValueError')
        filename: File where error occurred
        line: Line number
        
    Returns:
        Short hash string identifying this error pattern
        
    Example:
        >>> hash_error('ValueError', 'app.py', 42)
        'err_a3f7b2c1'
    """
    key = f"{error_type}:{filename}:{line}"
    hash_val = hashlib.md5(key.encode()).hexdigest()[:8]
    return f"err_{hash_val}"


# ---------------------------------------------------------------------------
# Pattern Storage
# ---------------------------------------------------------------------------

_PATTERN_FILE = ".agentlog/error_patterns.json"
_patterns: Dict[str, Dict[str, Any]] = {}
_patterns_loaded = False


def _ensure_dir():
    """Ensure .agentlog directory exists."""
    Path(".agentlog").mkdir(exist_ok=True)


def _load_patterns() -> Dict[str, Dict[str, Any]]:
    """Load error patterns from disk."""
    global _patterns, _patterns_loaded
    
    if _patterns_loaded:
        return _patterns
        
    try:
        if os.path.exists(_PATTERN_FILE):
            with open(_PATTERN_FILE, 'r') as f:
                _patterns = json.load(f)
    except (json.JSONDecodeError, IOError):
        _patterns = {}
    
    _patterns_loaded = True
    return _patterns


def _save_patterns():
    """Save error patterns to disk."""
    _ensure_dir()
    try:
        with open(_PATTERN_FILE, 'w') as f:
            json.dump(_patterns, f, indent=2)
    except IOError:
        pass  # Silent fail - disk storage is optional


def record_error_pattern(
    error_type: str,
    filename: str,
    line: int,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Record an error occurrence for pattern tracking.
    
    Args:
        error_type: Exception type name
        filename: File where error occurred
        line: Line number
        session_id: Optional session ID
        context: Optional additional context
        
    Returns:
        Error pattern hash
        
    Example:
        >>> record_error_pattern('ValueError', 'app.py', 42, 'sess_abc123')
        'err_a3f7b2c1'
    """
    _load_patterns()
    
    pattern_hash = hash_error(error_type, filename, line)
    
    if pattern_hash not in _patterns:
        _patterns[pattern_hash] = {
            "error_type": error_type,
            "location": {"file": filename, "line": line},
            "count": 0,
            "first_seen": None,
            "sessions": [],
            "contexts": []
        }
    
    pattern = _patterns[pattern_hash]
    pattern["count"] += 1
    
    import time
    if pattern["first_seen"] is None:
        pattern["first_seen"] = time.time()
    
    if session_id and session_id not in pattern["sessions"]:
        pattern["sessions"].append(session_id)
    
    if context:
        # Store limited context history (max 5)
        pattern["contexts"].append({
            "ts": time.time(),
            "session_id": session_id,
            "ctx": context
        })
        pattern["contexts"] = pattern["contexts"][-5:]
    
    _save_patterns()
    return pattern_hash


def get_error_pattern(pattern_hash: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an error pattern by its hash.
    
    Args:
        pattern_hash: Error pattern hash
        
    Returns:
        Pattern details or None if not found
    """
    _load_patterns()
    return _patterns.get(pattern_hash)


def get_all_patterns() -> Dict[str, Dict[str, Any]]:
    """
    Get all recorded error patterns.
    
    Returns:
        Dictionary mapping pattern hashes to pattern data
    """
    _load_patterns()
    return _patterns.copy()


def find_similar_errors(error_type: str, filename: str, line: int) -> List[Dict[str, Any]]:
    """
    Find similar errors based on type and location.
    
    Args:
        error_type: Exception type
        filename: File path
        line: Line number
        
    Returns:
        List of similar error patterns
    """
    _load_patterns()
    
    matches = []
    for hash_val, pattern in _patterns.items():
        # Same file, any line
        if pattern["location"]["file"] == filename:
            matches.append({"hash": hash_val, **pattern})
        # Same error type, different file
        elif pattern["error_type"] == error_type:
            matches.append({"hash": hash_val, **pattern})
    
    return sorted(matches, key=lambda x: x["count"], reverse=True)


def get_pattern_stats() -> Dict[str, Any]:
    """
    Get aggregate statistics about error patterns.
    
    Returns:
        Statistics dict with counts, top errors, etc.
    """
    _load_patterns()
    
    if not _patterns:
        return {"total_unique": 0, "total_occurrences": 0}
    
    total_occurrences = sum(p["count"] for p in _patterns.values())
    top_errors = sorted(
        [{"hash": h, **p} for h, p in _patterns.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    return {
        "total_unique": len(_patterns),
        "total_occurrences": total_occurrences,
        "top_errors": top_errors,
        "files_affected": len(set(p["location"]["file"] for p in _patterns.values()))
    }


# ---------------------------------------------------------------------------
# Correlation API
# ---------------------------------------------------------------------------

def correlate_error(error_type: str, filename: str, line: int) -> Dict[str, Any]:
    """
    Correlate a current error with historical patterns.
    
    Args:
        error_type: Current exception type
        filename: Current file
        line: Current line number
        
    Returns:
        Correlation results with history and similar errors
        
    Example:
        >>> result = correlate_error('ValueError', 'app.py', 42)
        >>> result['pattern_hash']
        'err_a3f7b2c1'
        >>> result['times_seen_before']
        3
        >>> result['previous_fixes']
        [...]
    """
    _load_patterns()
    
    pattern_hash = hash_error(error_type, filename, line)
    pattern = _patterns.get(pattern_hash)
    
    result = {
        "pattern_hash": pattern_hash,
        "is_new": pattern is None,
        "times_seen_before": 0,
        "previous_sessions": [],
        "similar_errors": []
    }
    
    if pattern:
        result["times_seen_before"] = pattern["count"] - 1
        result["previous_sessions"] = pattern.get("sessions", [])
        result["contexts"] = pattern.get("contexts", [])
    
    # Find similar errors in same file
    similar = find_similar_errors(error_type, filename, line)
    # Exclude exact match
    similar = [s for s in similar if s["hash"] != pattern_hash][:3]
    result["similar_errors"] = similar
    
    return result
