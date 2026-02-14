"""
Outcome tagging system for agentlog (Phase 3).

Enables manual or heuristic success/failure tagging to build evaluation datasets.
Helps agents track what worked and what didn't.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Outcome Types
# ---------------------------------------------------------------------------

OUTCOME_SUCCESS = "success"
OUTCOME_FAILURE = "failure"
OUTCOME_PARTIAL = "partial"
OUTCOME_UNKNOWN = "unknown"

VALID_OUTCOMES = {OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_PARTIAL, OUTCOME_UNKNOWN}


# ---------------------------------------------------------------------------
# Outcome Storage
# ---------------------------------------------------------------------------

_OUTCOME_FILE = ".agentlog/outcomes.json"
_outcomes: Dict[str, Dict[str, Any]] = {}
_outcomes_loaded = False


def _load_outcomes() -> Dict[str, Dict[str, Any]]:
    """Load outcomes from disk."""
    global _outcomes, _outcomes_loaded
    
    if _outcomes_loaded:
        return _outcomes
    
    try:
        if os.path.exists(_OUTCOME_FILE):
            with open(_OUTCOME_FILE, 'r') as f:
                _outcomes = json.load(f)
    except (json.JSONDecodeError, IOError):
        _outcomes = {}
    
    _outcomes_loaded = True
    return _outcomes


def _save_outcomes():
    """Save outcomes to disk."""
    Path(".agentlog").mkdir(exist_ok=True)
    try:
        with open(_OUTCOME_FILE, 'w') as f:
            json.dump(_outcomes, f, indent=2)
    except IOError:
        pass  # Silent fail


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tag_outcome(
    target_id: str,
    outcome: str,
    reason: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Tag a session, run, or task with an outcome.
    
    Args:
        target_id: Session ID, run ID, or task identifier
        outcome: One of 'success', 'failure', 'partial', 'unknown'
        reason: Explanation for the outcome
        tags: Optional list of tags (e.g., ['regression', 'performance'])
        metadata: Optional additional context
        
    Returns:
        True if tagged successfully
        
    Example:
        >>> tag_outcome('sess_abc123', 'success', 'All tests passed')
        >>> tag_outcome('sess_def456', 'failure', 'Introduced new bug', 
        ...             tags=['regression'], metadata={'error_count': 3})
    """
    if outcome not in VALID_OUTCOMES:
        return False
    
    _load_outcomes()
    
    _outcomes[target_id] = {
        "outcome": outcome,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "tags": tags or [],
        "metadata": metadata or {}
    }
    
    _save_outcomes()
    return True


def tag_session_outcome(
    outcome: str,
    reason: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Tag the current session with an outcome.
    
    Args:
        outcome: One of 'success', 'failure', 'partial', 'unknown'
        reason: Explanation for the outcome
        tags: Optional list of tags
        metadata: Optional additional context
        
    Returns:
        True if tagged successfully
    """
    from ._session import get_session_id
    
    session_id = get_session_id()
    if not session_id:
        return False
    
    return tag_outcome(session_id, outcome, reason, tags, metadata)


def get_outcome(target_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the outcome for a target.
    
    Args:
        target_id: Session ID or target identifier
        
    Returns:
        Outcome dict or None if not found
    """
    _load_outcomes()
    return _outcomes.get(target_id)


def get_all_outcomes(outcome_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get all recorded outcomes, optionally filtered.
    
    Args:
        outcome_filter: Optional filter by outcome type
        
    Returns:
        Dictionary of target_id -> outcome data
    """
    _load_outcomes()
    
    if outcome_filter:
        return {
            k: v for k, v in _outcomes.items()
            if v.get("outcome") == outcome_filter
        }
    
    return _outcomes.copy()


def get_outcome_stats() -> Dict[str, Any]:
    """
    Get aggregate statistics about outcomes.
    
    Returns:
        Statistics dict with counts by outcome type
    """
    _load_outcomes()
    
    if not _outcomes:
        return {"total": 0, "by_outcome": {}}
    
    by_outcome: Dict[str, int] = {}
    for outcome_data in _outcomes.values():
        o = outcome_data.get("outcome", "unknown")
        by_outcome[o] = by_outcome.get(o, 0) + 1
    
    return {
        "total": len(_outcomes),
        "by_outcome": by_outcome,
        "success_rate": by_outcome.get(OUTCOME_SUCCESS, 0) / len(_outcomes) if _outcomes else 0
    }


def delete_outcome(target_id: str) -> bool:
    """
    Delete an outcome record.
    
    Args:
        target_id: Target identifier
        
    Returns:
        True if deleted, False if not found
    """
    _load_outcomes()
    
    if target_id in _outcomes:
        del _outcomes[target_id]
        _save_outcomes()
        return True
    
    return False


# ---------------------------------------------------------------------------
# Heuristic Outcome Detection
# ---------------------------------------------------------------------------

def detect_outcome_from_logs(logs: List[Dict[str, Any]]) -> str:
    """
    Heuristic: Detect outcome from log entries.
    
    Args:
        logs: List of log entries
        
    Returns:
        Detected outcome ('success', 'failure', 'partial', 'unknown')
    """
    error_count = 0
    check_failures = 0
    
    for log in logs:
        tag = log.get("tag", "")
        
        if tag == "error":
            error_count += 1
        elif tag == "check" and not log.get("passed", True):
            check_failures += 1
    
    if error_count > 0:
        return OUTCOME_FAILURE
    elif check_failures > 0:
        return OUTCOME_PARTIAL
    else:
        return OUTCOME_SUCCESS


def auto_tag_session() -> bool:
    """
    Automatically tag current session based on logs.
    
    Returns:
        True if tagged, False if no session or no logs
    """
    from ._session import get_session_id
    from ._buffer import get_context
    
    session_id = get_session_id()
    if not session_id:
        return False
    
    # Get session logs
    context = get_context(tags=["error", "check"])
    if not context:
        return tag_outcome(session_id, OUTCOME_UNKNOWN, "No logs captured")
    
    import json
    logs = [json.loads(line) for line in context.strip().split('\n') if line]
    
    outcome = detect_outcome_from_logs(logs)
    reason = f"Auto-detected: {len([l for l in logs if l.get('tag') == 'error'])} errors"
    
    return tag_outcome(session_id, outcome, reason, tags=["auto"])
