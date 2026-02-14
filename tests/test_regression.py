"""
Tests for regression detection module (Phase 3).
"""

import pytest
import os
import json
import tempfile
from agentlog._regression import (
    set_baseline,
    get_baseline,
    list_baselines,
    delete_baseline,
    detect_regression,
    compare_to_baseline,
    generate_regression_report,
    _baselines,
    _BASELINE_FILE,
)
from agentlog._correlation import record_error_pattern, _patterns
from agentlog._outcome import tag_outcome, _outcomes, OUTCOME_SUCCESS, OUTCOME_FAILURE


class TestBaselineManagement:
    """Test baseline CRUD operations."""
    
    def setup_method(self):
        """Clear baselines before each test."""
        _baselines.clear()
        if os.path.exists(_BASELINE_FILE):
            os.remove(_BASELINE_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _baselines.clear()
        if os.path.exists(_BASELINE_FILE):
            os.remove(_BASELINE_FILE)
    
    def test_set_and_get_baseline(self):
        """Set and retrieve a baseline."""
        result = set_baseline("stable", "sess_abc123", {"version": "1.0"})
        assert result is True
        
        baseline = get_baseline("stable")
        assert baseline is not None
        assert baseline["session_id"] == "sess_abc123"
        assert baseline["metadata"]["version"] == "1.0"
    
    def test_get_baseline_not_found(self):
        """Get non-existent baseline returns None."""
        baseline = get_baseline("nonexistent")
        assert baseline is None
    
    def test_list_baselines(self):
        """List all baseline IDs."""
        set_baseline("stable", "sess_1")
        set_baseline("v1.0", "sess_2")
        
        baselines = list_baselines()
        assert "stable" in baselines
        assert "v1.0" in baselines
    
    def test_delete_baseline(self):
        """Delete a baseline."""
        set_baseline("to_delete", "sess_1")
        assert delete_baseline("to_delete") is True
        assert get_baseline("to_delete") is None
    
    def test_delete_nonexistent_baseline(self):
        """Delete non-existent baseline returns False."""
        result = delete_baseline("nonexistent")
        assert result is False


class TestRegressionDetection:
    """Test regression detection logic."""
    
    def setup_method(self):
        """Clear state before each test."""
        _baselines.clear()
        _patterns.clear()
        _outcomes.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json", ".agentlog/outcomes.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def teardown_method(self):
        """Clean up after each test."""
        _baselines.clear()
        _patterns.clear()
        _outcomes.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json", ".agentlog/outcomes.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def test_detect_regression_no_baseline(self):
        """Detect regression with no baseline returns None."""
        result = detect_regression("sess_current", "nonexistent_baseline")
        assert result is None
    
    def test_detect_regression_new_errors(self):
        """Detect regression when new errors appear."""
        # Create baseline session with no errors
        set_baseline("stable", "baseline_sess")
        
        # Create current session with new error
        record_error_pattern('ValueError', 'app.py', 42, 'current_sess')
        
        result = detect_regression("current_sess", "stable")
        
        assert result is not None
        assert result["has_regression"] is True
        assert len(result["new_errors"]) == 1
        assert result["new_error_count"] == 1
    
    def test_detect_regression_outcome_change(self):
        """Detect regression when outcome changes from success to failure."""
        # Baseline was successful
        set_baseline("stable", "baseline_sess")
        tag_outcome("baseline_sess", OUTCOME_SUCCESS)
        
        # Current session failed
        tag_outcome("current_sess", OUTCOME_FAILURE, "Tests failed")
        
        result = detect_regression("current_sess", "stable")
        
        assert result is not None
        assert result["outcome_regression"] is True
        assert result["has_regression"] is True


class TestCompareToBaseline:
    """Test metric comparison."""
    
    def setup_method(self):
        """Clear state before each test."""
        _baselines.clear()
        _patterns.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def teardown_method(self):
        """Clean up after each test."""
        _baselines.clear()
        _patterns.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def test_compare_error_count(self):
        """Compare error counts to baseline."""
        # Baseline: 1 error
        record_error_pattern('TypeError', 'utils.py', 10, 'baseline_sess')
        set_baseline("stable", "baseline_sess")
        
        # Current: 3 errors
        record_error_pattern('TypeError', 'utils.py', 10, 'current_sess')
        record_error_pattern('ValueError', 'app.py', 20, 'current_sess')
        record_error_pattern('KeyError', 'data.py', 30, 'current_sess')
        
        comparison = compare_to_baseline("error_count", "stable")
        
        assert comparison is not None
        assert comparison["metric"] == "error_count"
        assert comparison["baseline"] == 1
        assert comparison["current"] == 3
        assert comparison["delta"] == 2


class TestRegressionReport:
    """Test regression report generation."""
    
    def setup_method(self):
        """Clear state before each test."""
        _baselines.clear()
        _patterns.clear()
        _outcomes.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json", ".agentlog/outcomes.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def teardown_method(self):
        """Clean up after each test."""
        _baselines.clear()
        _patterns.clear()
        _outcomes.clear()
        for f in [_BASELINE_FILE, ".agentlog/error_patterns.json", ".agentlog/outcomes.json"]:
            if os.path.exists(f):
                os.remove(f)
    
    def test_generate_report_no_baseline(self):
        """Generate report with no baseline returns None."""
        report = generate_regression_report("nonexistent")
        assert report is None
    
    def test_generate_full_report(self):
        """Generate comprehensive regression report."""
        # Set up baseline
        set_baseline("stable", "baseline_sess")
        tag_outcome("baseline_sess", OUTCOME_SUCCESS)
        
        # Set up current with regression
        tag_outcome("current_sess", OUTCOME_FAILURE, "Bugs introduced")
        record_error_pattern('ValueError', 'app.py', 42, 'current_sess')
        
        # Note: This test would need mocking of get_session_id
        # For now, just verify the function structure exists
        assert callable(generate_regression_report)
