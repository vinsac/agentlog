"""
Team analytics for agentlog.

Aggregate debugging patterns across team sessions.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict


# ---------------------------------------------------------------------------
# Analytics Storage
# ---------------------------------------------------------------------------

_ANALYTICS_FILE = ".agentlog/team_analytics.json"
_analytics: Dict[str, Any] = {}
_analytics_loaded = False


def _load_analytics() -> Dict[str, Any]:
    """Load analytics from disk."""
    global _analytics, _analytics_loaded
    
    if _analytics_loaded:
        return _analytics
    
    try:
        if os.path.exists(_ANALYTICS_FILE):
            with open(_ANALYTICS_FILE, 'r') as f:
                _analytics = json.load(f)
    except (json.JSONDecodeError, IOError):
        _analytics = {
            "sessions": [],
            "patterns": {},
            "aggregated_at": None
        }
    
    _analytics_loaded = True
    return _analytics


def _save_analytics():
    """Save analytics to disk."""
    Path(".agentlog").mkdir(exist_ok=True)
    try:
        with open(_ANALYTICS_FILE, 'w') as f:
            json.dump(_analytics, f, indent=2)
    except IOError:
        pass


# ---------------------------------------------------------------------------
# Session Aggregation
# ---------------------------------------------------------------------------

def record_session_analytics(
    session_id: str,
    agent_name: str,
    task: str,
    outcome: Optional[str] = None,
    error_count: int = 0,
    token_count: int = 0,
    duration_seconds: Optional[float] = None,
    tags: Optional[List[str]] = None
) -> None:
    """
    Record analytics for a completed session.
    
    Args:
        session_id: Session identifier
        agent_name: Agent that ran the session
        task: Task description
        outcome: Session outcome
        error_count: Number of errors
        token_count: Total tokens used
        duration_seconds: Session duration
        tags: Additional tags
    """
    _load_analytics()
    
    session_record = {
        "session_id": session_id,
        "agent_name": agent_name,
        "task": task,
        "outcome": outcome,
        "error_count": error_count,
        "token_count": token_count,
        "duration_seconds": duration_seconds,
        "tags": tags or [],
        "recorded_at": datetime.now().isoformat()
    }
    
    # Update or add
    existing = [s for s in _analytics["sessions"] if s["session_id"] == session_id]
    if existing:
        idx = _analytics["sessions"].index(existing[0])
        _analytics["sessions"][idx] = session_record
    else:
        _analytics["sessions"].append(session_record)
    
    _analytics["aggregated_at"] = datetime.now().isoformat()
    _save_analytics()


# ---------------------------------------------------------------------------
# Analytics Queries
# ---------------------------------------------------------------------------

def get_team_stats(days: int = 7) -> Dict[str, Any]:
    """
    Get aggregate team statistics.
    
    Args:
        days: Lookback period in days
        
    Returns:
        Team statistics dict
    """
    _load_analytics()
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent_sessions = [
        s for s in _analytics["sessions"]
        if s.get("recorded_at", "") > cutoff
    ]
    
    if not recent_sessions:
        return {
            "period_days": days,
            "total_sessions": 0,
            "summary": "No data for period"
        }
    
    # Count by agent
    by_agent = Counter(s["agent_name"] for s in recent_sessions)
    
    # Count by outcome
    by_outcome = Counter(s.get("outcome") for s in recent_sessions if s.get("outcome"))
    
    # Error rates
    total_errors = sum(s.get("error_count", 0) for s in recent_sessions)
    
    # Token usage
    total_tokens = sum(s.get("token_count", 0) for s in recent_sessions)
    
    # Success rate
    outcomes = [s.get("outcome") for s in recent_sessions]
    success_rate = outcomes.count("success") / len(outcomes) if outcomes else 0
    
    return {
        "period_days": days,
        "total_sessions": len(recent_sessions),
        "by_agent": dict(by_agent),
        "by_outcome": dict(by_outcome),
        "total_errors": total_errors,
        "total_tokens": total_tokens,
        "success_rate": round(success_rate, 2),
        "avg_errors_per_session": round(total_errors / len(recent_sessions), 2),
        "avg_tokens_per_session": round(total_tokens / len(recent_sessions), 2)
    }


def get_error_trends(days: int = 30) -> List[Dict[str, Any]]:
    """
    Get error trends over time.
    
    Args:
        days: Lookback period
        
    Returns:
        List of daily error counts
    """
    _load_analytics()
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent = [s for s in _analytics["sessions"] if s.get("recorded_at", "") > cutoff]
    
    # Group by day
    by_day = defaultdict(lambda: {"errors": 0, "sessions": 0, "outcomes": []})
    
    for session in recent:
        day = session.get("recorded_at", "")[:10]  # YYYY-MM-DD
        by_day[day]["errors"] += session.get("error_count", 0)
        by_day[day]["sessions"] += 1
        if session.get("outcome"):
            by_day[day]["outcomes"].append(session["outcome"])
    
    # Convert to list
    trends = []
    for day in sorted(by_day.keys()):
        data = by_day[day]
        success_rate = data["outcomes"].count("success") / len(data["outcomes"]) if data["outcomes"] else 0
        trends.append({
            "date": day,
            "error_count": data["errors"],
            "session_count": data["sessions"],
            "success_rate": round(success_rate, 2)
        })
    
    return trends


def get_common_issues(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most common issues across all sessions.
    
    Args:
        limit: Maximum issues to return
        
    Returns:
        List of common issues
    """
    from ._correlation import get_all_patterns
    
    patterns = get_all_patterns()
    
    issues = []
    for pattern_hash, pattern in patterns.items():
        issues.append({
            "pattern_hash": pattern_hash,
            "error_type": pattern.get("error_type"),
            "location": pattern.get("location"),
            "count": pattern.get("count", 0),
            "sessions_affected": len(pattern.get("sessions", [])),
            "first_seen": pattern.get("first_seen")
        })
    
    # Sort by count
    issues.sort(key=lambda x: x["count"], reverse=True)
    
    return issues[:limit]


def get_agent_performance(agent_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """
    Get performance metrics for agents.
    
    Args:
        agent_name: Specific agent (default: all)
        days: Lookback period
        
    Returns:
        Performance metrics
    """
    _load_analytics()
    
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    sessions = [
        s for s in _analytics["sessions"]
        if s.get("recorded_at", "") > cutoff
        and (agent_name is None or s.get("agent_name") == agent_name)
    ]
    
    if not sessions:
        return {"agent": agent_name or "all", "sessions": 0}
    
    by_agent = defaultdict(lambda: {"sessions": 0, "errors": 0, "successes": 0, "tokens": 0})
    
    for session in sessions:
        name = session.get("agent_name", "unknown")
        by_agent[name]["sessions"] += 1
        by_agent[name]["errors"] += session.get("error_count", 0)
        by_agent[name]["tokens"] += session.get("token_count", 0)
        if session.get("outcome") == "success":
            by_agent[name]["successes"] += 1
    
    result = {}
    for name, data in by_agent.items():
        result[name] = {
            "sessions": data["sessions"],
            "total_errors": data["errors"],
            "total_tokens": data["tokens"],
            "success_rate": round(data["successes"] / data["sessions"], 2),
            "avg_errors": round(data["errors"] / data["sessions"], 2)
        }
    
    if agent_name:
        return result.get(agent_name, {})
    
    return result


# ---------------------------------------------------------------------------
# Comparison & Benchmarking
# ---------------------------------------------------------------------------

def compare_periods(
    current_days: int = 7,
    previous_days: int = 7
) -> Dict[str, Any]:
    """
    Compare current period to previous period.
    
    Args:
        current_days: Current period length
        previous_days: Previous period length
        
    Returns:
        Comparison results
    """
    now = datetime.now()
    
    current_end = now
    current_start = now - timedelta(days=current_days)
    
    previous_end = current_start
    previous_start = previous_end - timedelta(days=previous_days)
    
    _load_analytics()
    
    def get_period_stats(start, end):
        sessions = [
            s for s in _analytics["sessions"]
            if start.isoformat() <= s.get("recorded_at", "") < end.isoformat()
        ]
        
        if not sessions:
            return None
        
        return {
            "sessions": len(sessions),
            "errors": sum(s.get("error_count", 0) for s in sessions),
            "tokens": sum(s.get("token_count", 0) for s in sessions),
            "successes": sum(1 for s in sessions if s.get("outcome") == "success")
        }
    
    current = get_period_stats(current_start, current_end)
    previous = get_period_stats(previous_start, previous_end)
    
    if not current or not previous:
        return {"error": "Insufficient data for comparison"}
    
    return {
        "current_period": {
            "days": current_days,
            **current,
            "success_rate": round(current["successes"] / current["sessions"], 2)
        },
        "previous_period": {
            "days": previous_days,
            **previous,
            "success_rate": round(previous["successes"] / previous["sessions"], 2)
        },
        "change": {
            "sessions": current["sessions"] - previous["sessions"],
            "errors": current["errors"] - previous["errors"],
            "success_rate": round(current["successes"] / current["sessions"] - previous["successes"] / previous["sessions"], 2)
        }
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def generate_team_report(days: int = 7) -> Dict[str, Any]:
    """
    Generate comprehensive team report.
    
    Args:
        days: Report period
        
    Returns:
        Full team report
    """
    stats = get_team_stats(days)
    trends = get_error_trends(days)
    issues = get_common_issues(10)
    agents = get_agent_performance(days=days)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "period_days": days,
        "summary": stats,
        "trends": trends,
        "top_issues": issues,
        "agent_performance": agents,
        "recommendations": _generate_recommendations(stats, issues)
    }


def _generate_recommendations(stats: Dict, issues: List[Dict]) -> List[str]:
    """Generate recommendations based on analytics."""
    recommendations = []
    
    if stats.get("success_rate", 1.0) < 0.5:
        recommendations.append("Success rate is below 50%. Consider reviewing common failure patterns.")
    
    if stats.get("avg_errors_per_session", 0) > 5:
        recommendations.append("High error rate detected. Investigate recurring issues.")
    
    if issues and issues[0]["count"] > 10:
        recommendations.append(f"Issue '{issues[0]['error_type']}' occurred {issues[0]['count']} times. Prioritize fix.")
    
    if not recommendations:
        recommendations.append("No major issues detected. Continue monitoring.")
    
    return recommendations


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_analytics(format: str = "json", days: int = 30) -> str:
    """
    Export analytics to string or file.
    
    Args:
        format: "json", "markdown", "csv"
        days: Period to export
        
    Returns:
        Exported analytics
    """
    report = generate_team_report(days)
    
    if format == "json":
        return json.dumps(report, indent=2, default=str)
    
    elif format == "markdown":
        lines = [
            f"# Team Analytics Report ({days} days)",
            "",
            f"Generated: {report['generated_at']}",
            "",
            "## Summary",
            f"- Total Sessions: {report['summary'].get('total_sessions', 0)}",
            f"- Success Rate: {report['summary'].get('success_rate', 0):.0%}",
            f"- Total Errors: {report['summary'].get('total_errors', 0)}",
            f"- Total Tokens: {report['summary'].get('total_tokens', 0):,}",
            "",
            "## Top Issues",
        ]
        
        for issue in report.get("top_issues", [])[:5]:
            lines.append(f"- **{issue['error_type']}**: {issue['count']} occurrences")
        
        lines.append("")
        lines.append("## Recommendations")
        for rec in report.get("recommendations", []):
            lines.append(f"- {rec}")
        
        return '\n'.join(lines)
    
    return json.dumps(report, default=str)


def clear_analytics(older_than_days: Optional[int] = None) -> int:
    """
    Clear analytics data.
    
    Args:
        older_than_days: Only clear records older than this (default: all)
        
    Returns:
        Number of records cleared
    """
    _load_analytics()
    
    if older_than_days is None:
        count = len(_analytics["sessions"])
        _analytics["sessions"] = []
    else:
        cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
        original_count = len(_analytics["sessions"])
        _analytics["sessions"] = [
            s for s in _analytics["sessions"]
            if s.get("recorded_at", "") > cutoff
        ]
        count = original_count - len(_analytics["sessions"])
    
    _save_analytics()
    return count
