"""
Tests for outcome tagging module (Phase 3).
"""

import pytest
import os
import json
import tempfile
from agentlog._outcome import (
    tag_outcome,
    tag_session_outcome,
    get_outcome,
    get_all_outcomes,
    get_outcome_stats,
    detect_outcome_from_logs,
    auto_tag_session,
    OUTCOME_SUCCESS,
    OUTCOME_FAILURE,
    OUTCOME_PARTIAL,
    OUTCOME_UNKNOWN,
    VALID_OUTCOMES,
    _outcomes,
    _OUTCOME_FILE,
)
from agentlog import start_session, end_session


class TestOutcomeConstants:
    """Test outcome constants."""
    
    def test_valid_outcomes(self):
        """Valid outcome constants are defined."""
        assert OUTCOME_SUCCESS == "success"
        assert OUTCOME_FAILURE == "failure"
        assert OUTCOME_PARTIAL == "partial"
        assert OUTCOME_UNKNOWN == "unknown"
        assert VALID_OUTCOMES == {"success", "failure", "partial", "unknown"}


class TestTagOutcome:
    """Test outcome tagging."""
    
    def setup_method(self):
        """Clear outcomes before each test."""
        _outcomes.clear()
        if os.path.exists(_OUTCOME_FILE):
            os.remove(_OUTCOME_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _outcomes.clear()
        if os.path.exists(_OUTCOME_FILE):
            os.remove(_OUTCOME_FILE)
    
    def test_tag_valid_outcomes(self):
        """Tag with valid outcomes."""
        for outcome in VALID_OUTCOMES:
            result = tag_outcome(f"target_{outcome}", outcome, f"Test {outcome}")
            assert result is True
    
    def test_tag_invalid_outcome(self):
        """Tag with invalid outcome returns False."""
        result = tag_outcome("target1", "invalid", "Test")
        assert result is False
    
    def test_tag_with_metadata(self):
        """Tag with additional metadata."""
        result = tag_outcome(
            "sess_test",
            OUTCOME_SUCCESS,
            "All passed",
            tags=["regression_test"],
            metadata={"tests_passed": 10, "tests_failed": 0}
        )
        assert result is True
        
        outcome = get_outcome("sess_test")
        assert outcome["outcome"] == OUTCOME_SUCCESS
        assert outcome["reason"] == "All passed"
        assert outcome["tags"] == ["regression_test"]
        assert outcome["metadata"]["tests_passed"] == 10
    
    def test_get_outcome_not_found(self):
        """Get non-existent outcome returns None."""
        outcome = get_outcome("nonexistent")
        assert outcome is None
    
    def test_get_all_outcomes(self):
        """Get all outcomes."""
        tag_outcome("t1", OUTCOME_SUCCESS)
        tag_outcome("t2", OUTCOME_FAILURE)
        tag_outcome("t3", OUTCOME_SUCCESS)
        
        outcomes = get_all_outcomes()
        assert len(outcomes) == 3
        assert outcomes["t1"]["outcome"] == OUTCOME_SUCCESS
        assert outcomes["t2"]["outcome"] == OUTCOME_FAILURE
    
    def test_get_all_outcomes_filtered(self):
        """Get outcomes filtered by type."""
        tag_outcome("t1", OUTCOME_SUCCESS)
        tag_outcome("t2", OUTCOME_FAILURE)
        tag_outcome("t3", OUTCOME_SUCCESS)
        
        successes = get_all_outcomes(OUTCOME_SUCCESS)
        assert len(successes) == 2
        assert all(o["outcome"] == OUTCOME_SUCCESS for o in successes.values())


class TestOutcomeStats:
    """Test outcome statistics."""
    
    def setup_method(self):
        """Clear outcomes before each test."""
        _outcomes.clear()
        if os.path.exists(_OUTCOME_FILE):
            os.remove(_OUTCOME_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _outcomes.clear()
        if os.path.exists(_OUTCOME_FILE):
            os.remove(_OUTCOME_FILE)
    
    def test_empty_stats(self):
        """Stats with no outcomes."""
        stats = get_outcome_stats()
        assert stats["total"] == 0
        assert stats["by_outcome"] == {}
        assert stats["success_rate"] == 0
    
    def test_stats_with_outcomes(self):
        """Stats with recorded outcomes."""
        tag_outcome("t1", OUTCOME_SUCCESS)
        tag_outcome("t2", OUTCOME_SUCCESS)
        tag_outcome("t3", OUTCOME_FAILURE)
        
        stats = get_outcome_stats()
        assert stats["total"] == 3
        assert stats["by_outcome"][OUTCOME_SUCCESS] == 2
        assert stats["by_outcome"][OUTCOME_FAILURE] == 1
        assert stats["success_rate"] == 2/3


class TestOutcomeDetection:
    """Test heuristic outcome detection."""
    
    def test_detect_success_no_errors(self):
        """Detect success when no errors."""
        logs = [
            {"tag": "info", "msg": "Started"},
            {"tag": "info", "msg": "Finished"}
        ]
        outcome = detect_outcome_from_logs(logs)
        assert outcome == OUTCOME_SUCCESS
    
    def test_detect_failure_with_error(self):
        """Detect failure when errors present."""
        logs = [
            {"tag": "info", "msg": "Started"},
            {"tag": "error", "msg": "Something failed"},
            {"tag": "info", "msg": "Finished"}
        ]
        outcome = detect_outcome_from_logs(logs)
        assert outcome == OUTCOME_FAILURE
    
    def test_detect_partial_with_check_failure(self):
        """Detect partial when checks fail but no errors."""
        logs = [
            {"tag": "info", "msg": "Started"},
            {"tag": "check", "msg": "Validation", "passed": False},
            {"tag": "info", "msg": "Finished"}
        ]
        outcome = detect_outcome_from_logs(logs)
        assert outcome == OUTCOME_PARTIAL
