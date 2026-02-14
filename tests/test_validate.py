"""
Tests for Clear Winner Feature 3: validate_refactoring() - Regression Validator
"""

import pytest
from agentlog._validate import (
    _calculate_error_delta,
    _calculate_outcome_score,
    _calculate_behavior_score,
    _compute_overall_safety,
    validate_refactoring,
    quick_validate,
)


class TestErrorDeltaCalculation:
    """Test error delta calculation."""
    
    def test_no_changes(self):
        """No errors in either baseline or current."""
        baseline = {}
        current = {}
        
        delta = _calculate_error_delta(baseline, current)
        
        assert delta['new_count'] == 0
        assert delta['resolved_count'] == 0
        assert delta['net_change'] == 0
    
    def test_new_errors(self):
        """New errors introduced."""
        baseline = {}
        current = {
            'err_1': {'count': 3}
        }
        
        delta = _calculate_error_delta(baseline, current)
        
        assert delta['new_count'] == 1
        assert delta['resolved_count'] == 0
        assert delta['net_change'] == 1
    
    def test_resolved_errors(self):
        """Errors resolved."""
        baseline = {
            'err_1': {'count': 2}
        }
        current = {}
        
        delta = _calculate_error_delta(baseline, current)
        
        assert delta['new_count'] == 0
        assert delta['resolved_count'] == 1
        assert delta['net_change'] == -1
    
    def test_mixed_changes(self):
        """Some new, some resolved."""
        baseline = {
            'err_1': {'count': 1}
        }
        current = {
            'err_2': {'count': 1}
        }
        
        delta = _calculate_error_delta(baseline, current)
        
        assert delta['new_count'] == 1
        assert delta['resolved_count'] == 1
        assert delta['net_change'] == 0


class TestOutcomeScoreCalculation:
    """Test outcome score calculation."""
    
    def test_success_to_success(self):
        """Success → Success is good."""
        score, explanation = _calculate_outcome_score('success', 'success')
        assert score >= 80
        assert 'Consistent success' in explanation
    
    def test_success_to_failure(self):
        """Success → Failure is regression."""
        score, explanation = _calculate_outcome_score('success', 'failure')
        assert score < 20
        assert 'REGRESSION' in explanation
    
    def test_failure_to_success(self):
        """Failure → Success is improvement."""
        score, explanation = _calculate_outcome_score('failure', 'success')
        assert score >= 90
        assert 'IMPROVEMENT' in explanation
    
    def test_partial_to_success(self):
        """Partial → Success is improvement."""
        score, explanation = _calculate_outcome_score('partial', 'success')
        assert score >= 80
    
    def test_no_baseline(self):
        """No baseline outcome."""
        score, explanation = _calculate_outcome_score(None, 'success')
        assert score == 50


class TestBehaviorScoreCalculation:
    """Test behavior score calculation."""
    
    def test_token_improvement(self):
        """Fewer tokens is better."""
        baseline = {'token_count': 1000, 'error_count': 0}
        current = {'token_count': 800, 'error_count': 0}
        
        scores = _calculate_behavior_score(baseline, current)
        
        assert scores['token_score'] >= 80
        assert scores['token_delta_pct'] == -20.0
    
    def test_token_regression(self):
        """More tokens is worse."""
        baseline = {'token_count': 1000, 'error_count': 0}
        current = {'token_count': 1500, 'error_count': 0}
        
        scores = _calculate_behavior_score(baseline, current)
        
        assert scores['token_score'] < 70
        assert scores['token_delta_pct'] == 50.0
    
    def test_error_improvement(self):
        """Fewer errors is better."""
        baseline = {'token_count': 1000, 'error_count': 5}
        current = {'token_count': 1000, 'error_count': 2}
        
        scores = _calculate_behavior_score(baseline, current)
        
        assert scores['error_score'] >= 80
    
    def test_new_errors(self):
        """New errors introduced."""
        baseline = {'token_count': 1000, 'error_count': 0}
        current = {'token_count': 1000, 'error_count': 3}
        
        scores = _calculate_behavior_score(baseline, current)
        
        assert scores['error_score'] < 30


class TestOverallSafety:
    """Test overall safety computation."""
    
    def test_safe_scenario(self):
        """Scenario with no regressions."""
        error_delta = {
            'new_count': 0,
            'resolved_count': 2,
            'net_severity': -2
        }
        outcome_score = 90
        behavior_scores = {'token_score': 85, 'error_score': 90}
        
        safety = _compute_overall_safety(error_delta, outcome_score, behavior_scores)
        
        assert safety['is_safe'] is True
        assert safety['decision'] == 'safe'
        assert safety['overall_score'] >= 80
    
    def test_unsafe_scenario(self):
        """Scenario with regressions."""
        error_delta = {
            'new_count': 3,
            'resolved_count': 0,
            'net_severity': 5
        }
        outcome_score = 10
        behavior_scores = {'token_score': 40, 'error_score': 20}
        
        safety = _compute_overall_safety(error_delta, outcome_score, behavior_scores)
        
        assert safety['is_safe'] is False
        assert safety['decision'] == 'unsafe'
    
    def test_caution_scenario(self):
        """Scenario needing caution."""
        error_delta = {
            'new_count': 1,
            'resolved_count': 1,
            'net_severity': 0
        }
        outcome_score = 70
        behavior_scores = {'token_score': 70, 'error_score': 70}
        
        safety = _compute_overall_safety(error_delta, outcome_score, behavior_scores)
        
        assert safety['decision'] in ['caution', 'review_required']


class TestValidateRefactoring:
    """Test public API."""
    
    def test_returns_dict(self):
        """Returns proper dict structure."""
        result = validate_refactoring('baseline_1', 'new_1')
        
        assert isinstance(result, dict)
        assert 'safe_to_merge' in result
        assert 'confidence_score' in result
        assert 'decision' in result
        assert 'blocking_issues' in result
        assert 'recommendations' in result
    
    def test_boolean_safe_to_merge(self):
        """safe_to_merge is boolean."""
        result = validate_refactoring('baseline_1', 'new_1')
        assert isinstance(result['safe_to_merge'], bool)
    
    def test_score_range(self):
        """confidence_score is 0-100."""
        result = validate_refactoring('baseline_1', 'new_1')
        score = result['confidence_score']
        assert 0 <= score <= 100
    
    def test_blocking_issues_list(self):
        """blocking_issues is a list."""
        result = validate_refactoring('baseline_1', 'new_1')
        assert isinstance(result['blocking_issues'], list)
    
    def test_recommendations_list(self):
        """recommendations is a list."""
        result = validate_refactoring('baseline_1', 'new_1')
        assert isinstance(result['recommendations'], list)


class TestQuickValidate:
    """Test quick validate API."""
    
    def test_returns_string(self):
        """Returns string result."""
        result = quick_validate()
        assert isinstance(result, str)
    
    def test_valid_decisions(self):
        """Returns valid decision strings."""
        result = quick_validate()
        valid_decisions = ['SAFE', 'CAUTION', 'REVIEW', 'UNSAFE', 'NO_BASELINE', 'NO_SESSION', 'UNKNOWN']
        assert result in valid_decisions
