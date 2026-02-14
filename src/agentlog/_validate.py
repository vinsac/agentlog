"""
Regression validator for agentlog (Clear Winner Feature #3).

The 10X feature: Validate agent refactoring automatically.
Replaces manual review of 10K line diffs with opinionated safe/unsafe decision.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ---------------------------------------------------------------------------
# Scoring Algorithms
# ---------------------------------------------------------------------------

def _calculate_error_delta(baseline_errors: Dict, current_errors: Dict) -> Dict[str, Any]:
    """
    Calculate the delta between baseline and current error patterns.
    
    Returns:
        Delta analysis with scores
    """
    baseline_hashes = set(baseline_errors.keys())
    current_hashes = set(current_errors.keys())
    
    new_errors = current_hashes - baseline_hashes
    resolved_errors = baseline_hashes - current_hashes
    
    # Score based on severity
    new_severity = sum(
        current_errors[h].get('count', 1) 
        for h in new_errors
    )
    
    resolved_severity = sum(
        baseline_errors[h].get('count', 1)
        for h in resolved_errors
    )
    
    return {
        'new_count': len(new_errors),
        'resolved_count': len(resolved_errors),
        'new_hashes': list(new_errors),
        'resolved_hashes': list(resolved_errors),
        'new_severity': new_severity,
        'resolved_severity': resolved_severity,
        'net_change': len(new_errors) - len(resolved_errors),
        'net_severity': new_severity - resolved_severity
    }


def _calculate_outcome_score(baseline_outcome: Optional[str], current_outcome: Optional[str]) -> Tuple[int, str]:
    """
    Calculate outcome-based safety score.
    
    Returns:
        Tuple of (score 0-100, explanation)
    """
    if not baseline_outcome:
        return (50, "No baseline outcome recorded")
    
    if not current_outcome:
        return (50, "Current outcome not yet determined")
    
    # Success scores
    scores = {
        ('success', 'success'): (90, "Consistent success"),
        ('success', 'failure'): (10, "REGRESSION: Success → Failure"),
        ('success', 'partial'): (40, "PARTIAL: Success → Partial failure"),
        ('failure', 'success'): (95, "IMPROVEMENT: Failure → Success"),
        ('failure', 'failure'): (50, "Consistent failure (no improvement)"),
        ('failure', 'partial'): (60, "PARTIAL: Failure → Partial (improving)"),
        ('partial', 'success'): (90, "IMPROVEMENT: Partial → Success"),
        ('partial', 'failure'): (20, "REGRESSION: Partial → Failure"),
        ('partial', 'partial'): (60, "Consistent partial (stable)"),
    }
    
    return scores.get((baseline_outcome, current_outcome), (50, "Unknown outcome combination"))


def _calculate_behavior_score(baseline_ctx: Dict, current_ctx: Dict) -> Dict[str, Any]:
    """
    Compare behavior metrics between baseline and current.
    
    Looks at:
    - Token usage delta
    - Performance (duration)
    - Error rates
    """
    scores = {}
    
    # Token usage
    baseline_tokens = baseline_ctx.get('token_count', 0)
    current_tokens = current_ctx.get('token_count', 0)
    
    if baseline_tokens > 0:
        token_delta = (current_tokens - baseline_tokens) / baseline_tokens
        scores['token_delta_pct'] = round(token_delta * 100, 1)
        
        # Score: less tokens = better (more efficient)
        if token_delta < -0.2:
            scores['token_score'] = 95  # Much more efficient
        elif token_delta < 0:
            scores['token_score'] = 80  # Slightly more efficient
        elif token_delta < 0.2:
            scores['token_score'] = 70  # Similar efficiency
        elif token_delta < 0.5:
            scores['token_score'] = 50  # Less efficient
        else:
            scores['token_score'] = 30  # Much less efficient
    else:
        scores['token_score'] = 50
        scores['token_delta_pct'] = 0
    
    # Error count
    baseline_errors = baseline_ctx.get('error_count', 0)
    current_errors = current_ctx.get('error_count', 0)
    
    if baseline_errors > 0:
        error_delta = (current_errors - baseline_errors) / baseline_errors
        scores['error_delta_pct'] = round(error_delta * 100, 1)
        
        # Score: fewer errors = better
        if error_delta < -0.5:
            scores['error_score'] = 95  # Much fewer errors
        elif error_delta < 0:
            scores['error_score'] = 80  # Fewer errors
        elif error_delta == 0:
            scores['error_score'] = 70  # Same errors
        elif error_delta < 0.5:
            scores['error_score'] = 40  # More errors
        else:
            scores['error_score'] = 20  # Many more errors
    else:
        if current_errors == 0:
            scores['error_score'] = 90  # Still no errors
        else:
            scores['error_score'] = 20  # New errors introduced
        scores['error_delta_pct'] = 0 if baseline_errors == 0 else float('inf')
    
    return scores


def _compute_overall_safety(error_delta: Dict, outcome_score: int, behavior_scores: Dict) -> Dict[str, Any]:
    """
    Compute overall safety score and decision.
    
    Returns:
        Safety assessment
    """
    # Weight factors
    weights = {
        'error': 0.4,      # 40% - errors matter most
        'outcome': 0.35,   # 35% - did it succeed?
        'behavior': 0.25   # 25% - efficiency/regression
    }
    
    # Error score (inverse of severity)
    if error_delta['new_count'] == 0:
        error_score = 95
    elif error_delta['net_severity'] < 0:
        error_score = 80  # Net improvement
    elif error_delta['net_severity'] == 0:
        error_score = 60  # Neutral
    else:
        error_score = max(10, 50 - error_delta['net_severity'] * 10)
    
    # Behavior score
    behavior_score = (
        behavior_scores.get('token_score', 50) * 0.5 +
        behavior_scores.get('error_score', 50) * 0.5
    )
    
    # Weighted overall
    overall = (
        error_score * weights['error'] +
        outcome_score * weights['outcome'] +
        behavior_score * weights['behavior']
    )
    
    # Decision thresholds
    if overall >= 80:
        decision = 'safe'
        confidence = min(95, overall)
    elif overall >= 60:
        decision = 'caution'
        confidence = overall
    elif overall >= 40:
        decision = 'review_required'
        confidence = 100 - overall
    else:
        decision = 'unsafe'
        confidence = min(95, 100 - overall)
    
    return {
        'overall_score': round(overall, 1),
        'component_scores': {
            'error_score': round(error_score, 1),
            'outcome_score': outcome_score,
            'behavior_score': round(behavior_score, 1)
        },
        'weights_used': weights,
        'decision': decision,
        'confidence': round(confidence, 1),
        'is_safe': decision == 'safe'
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_refactoring(
    baseline_session: str,
    new_session: str,
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    Validate if a refactoring is safe to merge.
    
    The 10X feature: Opinionated safe/unsafe decision for agent refactoring.
    
    Args:
        baseline_session: Stable baseline session ID
        new_session: New refactored session ID
        strict_mode: If True, requires perfect match to be "safe"
        
    Returns:
        Validation result with:
        - safe_to_merge: bool
        - confidence_score: 0-100
        - blocking_issues: list of problems
        - detailed_analysis: full breakdown
        
    Example:
        >>> result = agentlog.validate_refactoring("sess_stable", "sess_new")
        >>> if result['safe_to_merge']:
        ...     print("Safe to merge!")
        ... else:
        ...     print(f"Issues: {result['blocking_issues']}")
    """
    from ._correlation import get_all_patterns
    from ._outcome import get_outcome
    from ._regression import get_baseline
    
    # Get error patterns for both sessions
    all_patterns = get_all_patterns()
    
    baseline_errors = {
        h: p for h, p in all_patterns.items()
        if baseline_session in p.get('sessions', [])
    }
    
    new_errors = {
        h: p for h, p in all_patterns.items()
        if new_session in p.get('sessions', [])
    }
    
    # Calculate error delta
    error_delta = _calculate_error_delta(baseline_errors, new_errors)
    
    # Get outcomes
    baseline_outcome_data = get_outcome(baseline_session)
    new_outcome_data = get_outcome(new_session)
    
    baseline_outcome = baseline_outcome_data.get('outcome') if baseline_outcome_data else None
    new_outcome = new_outcome_data.get('outcome') if new_outcome_data else None
    
    outcome_score, outcome_explanation = _calculate_outcome_score(
        baseline_outcome, new_outcome
    )
    
    # Build context for behavior comparison
    baseline_ctx = {
        'token_count': sum(p.get('token_count', 0) for p in baseline_errors.values()),
        'error_count': len(baseline_errors)
    }
    
    new_ctx = {
        'token_count': sum(p.get('token_count', 0) for p in new_errors.values()),
        'error_count': len(new_errors)
    }
    
    behavior_scores = _calculate_behavior_score(baseline_ctx, new_ctx)
    
    # Compute safety
    if strict_mode:
        # Stricter thresholds
        if error_delta['new_count'] > 0:
            safety = {
                'overall_score': 20,
                'decision': 'unsafe',
                'confidence': 90,
                'is_safe': False
            }
        elif new_outcome != 'success':
            safety = {
                'overall_score': 30,
                'decision': 'unsafe',
                'confidence': 85,
                'is_safe': False
            }
        else:
            safety = _compute_overall_safety(error_delta, outcome_score, behavior_scores)
    else:
        safety = _compute_overall_safety(error_delta, outcome_score, behavior_scores)
    
    # Build blocking issues list
    blocking_issues = []
    
    if error_delta['new_count'] > 0:
        blocking_issues.append(
            f"{error_delta['new_count']} new error patterns introduced"
        )
    
    if error_delta['net_severity'] > 0:
        blocking_issues.append(
            f"Error severity increased by {error_delta['net_severity']}"
        )
    
    if new_outcome == 'failure':
        blocking_issues.append("Session outcome is failure (was success in baseline)")
    
    if behavior_scores.get('error_score', 50) < 40:
        blocking_issues.append("Error rate significantly worse than baseline")
    
    # Build recommendations
    recommendations = []
    
    if safety['decision'] == 'safe':
        recommendations.append("✓ Safe to merge - no regressions detected")
    elif safety['decision'] == 'caution':
        recommendations.append("⚠ Caution advised - review minor changes before merge")
    elif safety['decision'] == 'review_required':
        recommendations.append("⚠ Manual review required - changes may affect stability")
    else:
        recommendations.append("✗ Do not merge - significant regressions detected")
    
    if error_delta['resolved_count'] > 0:
        recommendations.append(
            f"✓ Good: {error_delta['resolved_count']} previous errors resolved"
        )
    
    return {
        'safe_to_merge': safety['is_safe'],
        'confidence_score': safety['confidence'],
        'decision': safety['decision'],
        'blocking_issues': blocking_issues,
        'recommendations': recommendations,
        'detailed_analysis': {
            'overall_score': safety['overall_score'],
            'component_scores': safety.get('component_scores', {}),
            'error_delta': error_delta,
            'outcome_analysis': {
                'baseline': baseline_outcome,
                'current': new_outcome,
                'score': outcome_score,
                'explanation': outcome_explanation
            },
            'behavior_analysis': behavior_scores
        },
        'baseline_session': baseline_session,
        'new_session': new_session,
        'validated_at': datetime.now().isoformat()
    }


def quick_validate(
    baseline_session: Optional[str] = None,
    new_session: Optional[str] = None
) -> str:
    """
    Quick validation returning a simple yes/no/maybe string.
    
    Args:
        baseline_session: Baseline (default: "stable" baseline)
        new_session: Current session (default: current active)
        
    Returns:
        "SAFE", "CAUTION", "REVIEW", or "UNSAFE"
    """
    from ._regression import get_baseline, list_baselines
    from ._session import get_session_id
    
    # Get default sessions
    if baseline_session is None:
        baselines = list_baselines()
        if 'stable' in baselines:
            baseline_session = 'stable'
        elif baselines:
            baseline_session = baselines[0]
        else:
            return "NO_BASELINE"
    
    if new_session is None:
        new_session = get_session_id()
        if not new_session:
            return "NO_SESSION"
    
    result = validate_refactoring(baseline_session, new_session)
    
    decision_map = {
        'safe': 'SAFE',
        'caution': 'CAUTION',
        'review_required': 'REVIEW',
        'unsafe': 'UNSAFE'
    }
    
    return decision_map.get(result['decision'], 'UNKNOWN')
