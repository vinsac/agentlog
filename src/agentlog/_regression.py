"""
Regression detection for agentlog (Phase 3).

Compare current run to baseline sessions to catch introduced bugs.
Helps agents identify when their changes broke something.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ._correlation import hash_error, record_error_pattern


# ---------------------------------------------------------------------------
# Baseline Management
# ---------------------------------------------------------------------------

_BASELINE_FILE = ".agentlog/baselines.json"
_baselines: Dict[str, Dict[str, Any]] = {}
_baselines_loaded = False


def _load_baselines() -> Dict[str, Dict[str, Any]]:
    """Load baselines from disk."""
    global _baselines, _baselines_loaded
    
    if _baselines_loaded:
        return _baselines
    
    try:
        if os.path.exists(_BASELINE_FILE):
            with open(_BASELINE_FILE, 'r') as f:
                _baselines = json.load(f)
    except (json.JSONDecodeError, IOError):
        _baselines = {}
    
    _baselines_loaded = True
    return _baselines


def _save_baselines():
    """Save baselines to disk."""
    Path(".agentlog").mkdir(exist_ok=True)
    try:
        with open(_BASELINE_FILE, 'w') as f:
            json.dump(_baselines, f, indent=2)
    except IOError:
        pass


def set_baseline(
    baseline_id: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Set a baseline for regression detection.
    
    Args:
        baseline_id: Identifier for this baseline (e.g., 'stable', 'v1.0')
        session_id: Session to use as baseline (default: current session)
        metadata: Optional additional context
        
    Returns:
        True if baseline was set
        
    Example:
        >>> set_baseline('stable')  # Mark current session as baseline
        >>> set_baseline('v1.0', 'sess_abc123', {'version': '1.0.0'})
    """
    from ._session import get_session_id
    from ._outcome import get_outcome
    
    if session_id is None:
        session_id = get_session_id()
    
    if not session_id:
        return False
    
    _load_baselines()
    
    # Get outcome for this session if available
    outcome = get_outcome(session_id)
    
    _baselines[baseline_id] = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "outcome": outcome.get("outcome") if outcome else None,
        "metadata": metadata or {}
    }
    
    _save_baselines()
    return True


def get_baseline(baseline_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a baseline by ID.
    
    Args:
        baseline_id: Baseline identifier
        
    Returns:
        Baseline data or None
    """
    _load_baselines()
    return _baselines.get(baseline_id)


def list_baselines() -> List[str]:
    """List all baseline IDs."""
    _load_baselines()
    return list(_baselines.keys())


def delete_baseline(baseline_id: str) -> bool:
    """
    Delete a baseline.
    
    Args:
        baseline_id: Baseline identifier
        
    Returns:
        True if deleted
    """
    _load_baselines()
    
    if baseline_id in _baselines:
        del _baselines[baseline_id]
        _save_baselines()
        return True
    
    return False


# ---------------------------------------------------------------------------
# Regression Detection
# ---------------------------------------------------------------------------

def detect_regression(
    session_id: Optional[str] = None,
    baseline_id: str = "stable"
) -> Optional[Dict[str, Any]]:
    """
    Detect regressions by comparing current session to baseline.
    
    Args:
        session_id: Session to compare (default: current)
        baseline_id: Baseline to compare against (default: 'stable')
        
    Returns:
        Regression report or None if no baseline
        
    Example:
        >>> result = detect_regression()
        >>> result['has_regression']
        True
        >>> result['new_errors']
        ['err_abc123', 'err_def456']
    """
    from ._session import get_session_id
    from ._correlation import get_all_patterns, hash_error
    from ._outcome import get_outcome
    from ._buffer import get_context
    
    if session_id is None:
        session_id = get_session_id()
    
    if not session_id:
        return None
    
    baseline = get_baseline(baseline_id)
    if not baseline:
        return None
    
    baseline_session = baseline.get("session_id")
    
    # Get current session patterns
    all_patterns = get_all_patterns()
    current_patterns = {
        h: p for h, p in all_patterns.items()
        if session_id in p.get("sessions", [])
    }
    
    # Get baseline patterns
    baseline_patterns = {
        h: p for h, p in all_patterns.items()
        if baseline_session in p.get("sessions", [])
    }
    
    # Find new errors (in current, not in baseline)
    current_hashes = set(current_patterns.keys())
    baseline_hashes = set(baseline_patterns.keys())
    
    new_errors = list(current_hashes - baseline_hashes)
    resolved_errors = list(baseline_hashes - current_hashes)
    
    # Get outcomes
    current_outcome = get_outcome(session_id)
    baseline_outcome = baseline.get("outcome")
    
    outcome_regression = False
    if baseline_outcome == "success" and current_outcome:
        if current_outcome.get("outcome") in ("failure", "partial"):
            outcome_regression = True
    
    has_regression = len(new_errors) > 0 or outcome_regression
    
    return {
        "has_regression": has_regression,
        "session_id": session_id,
        "baseline_id": baseline_id,
        "baseline_session": baseline_session,
        "new_errors": new_errors,
        "new_error_count": len(new_errors),
        "resolved_errors": resolved_errors,
        "resolved_error_count": len(resolved_errors),
        "outcome_regression": outcome_regression,
        "current_outcome": current_outcome.get("outcome") if current_outcome else None,
        "baseline_outcome": baseline_outcome
    }


def compare_to_baseline(
    metric: str = "error_count",
    baseline_id: str = "stable"
) -> Optional[Dict[str, Any]]:
    """
    Compare a specific metric to baseline.
    
    Args:
        metric: Metric to compare ('error_count', 'duration', 'outcome')
        baseline_id: Baseline identifier
        
    Returns:
        Comparison result with delta
    """
    from ._session import get_session_id
    from ._correlation import get_all_patterns
    from ._outcome import get_outcome
    
    current_session = get_session_id()
    baseline = get_baseline(baseline_id)
    
    if not baseline or not current_session:
        return None
    
    baseline_session = baseline.get("session_id")
    
    if metric == "error_count":
        all_patterns = get_all_patterns()
        
        current_count = sum(
            1 for h, p in all_patterns.items()
            if current_session in p.get("sessions", [])
        )
        baseline_count = sum(
            1 for h, p in all_patterns.items()
            if baseline_session in p.get("sessions", [])
        )
        
        return {
            "metric": "error_count",
            "current": current_count,
            "baseline": baseline_count,
            "delta": current_count - baseline_count,
            "delta_pct": ((current_count - baseline_count) / baseline_count * 100)
            if baseline_count > 0 else 0
        }
    
    elif metric == "outcome":
        current = get_outcome(current_session)
        baseline_outcome = baseline.get("outcome")
        
        return {
            "metric": "outcome",
            "current": current.get("outcome") if current else None,
            "baseline": baseline_outcome,
            "regressed": baseline_outcome == "success" and (
                current and current.get("outcome") in ("failure", "partial")
            )
        }
    
    return None


# ---------------------------------------------------------------------------
# Regression Report
# ---------------------------------------------------------------------------

def generate_regression_report(
    baseline_id: str = "stable"
) -> Optional[Dict[str, Any]]:
    """
    Generate a full regression report.
    
    Args:
        baseline_id: Baseline to compare against
        
    Returns:
        Full regression report or None
    """
    from ._session import get_session_id
    from ._correlation import get_pattern_stats
    from ._outcome import get_outcome_stats
    
    current_session = get_session_id()
    if not current_session:
        return None
    
    baseline = get_baseline(baseline_id)
    if not baseline:
        return None
    
    regression = detect_regression(current_session, baseline_id)
    error_comparison = compare_to_baseline("error_count", baseline_id)
    outcome_comparison = compare_to_baseline("outcome", baseline_id)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "session_id": current_session,
        "baseline_id": baseline_id,
        "regression": regression,
        "metrics": {
            "errors": error_comparison,
            "outcome": outcome_comparison
        },
        "summary": {
            "has_regression": regression.get("has_regression", False),
            "new_errors": regression.get("new_error_count", 0),
            "resolved_errors": regression.get("resolved_error_count", 0),
            "recommendation": "investigate" if regression.get("has_regression") else "continue"
        }
    }
