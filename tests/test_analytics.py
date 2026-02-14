"""
Tests for team analytics module (Phase 5).
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from agentlog._analytics import (
    record_session_analytics,
    get_team_stats,
    get_error_trends,
    get_common_issues,
    get_agent_performance,
    compare_periods,
    generate_team_report,
    export_analytics,
    clear_analytics,
    _analytics,
    _ANALYTICS_FILE,
)


class TestRecordAnalytics:
    """Test analytics recording."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
        if os.path.exists(_ANALYTICS_FILE):
            os.remove(_ANALYTICS_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _analytics.clear()
        if os.path.exists(_ANALYTICS_FILE):
            os.remove(_ANALYTICS_FILE)
    
    def test_record_session(self):
        """Record a session."""
        record_session_analytics(
            "sess_123",
            "cursor",
            "fix bug",
            outcome="success",
            error_count=0,
            token_count=1000
        )
        
        assert len(_analytics["sessions"]) == 1
        assert _analytics["sessions"][0]["session_id"] == "sess_123"
    
    def test_record_updates_existing(self):
        """Recording updates existing session."""
        record_session_analytics("sess_123", "cursor", "task1")
        record_session_analytics("sess_123", "cursor", "task2")
        
        assert len(_analytics["sessions"]) == 1
        assert _analytics["sessions"][0]["task"] == "task2"


class TestTeamStats:
    """Test team statistics."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
    
    def test_empty_stats(self):
        """Stats with no data."""
        stats = get_team_stats(7)
        assert stats["total_sessions"] == 0
    
    def test_stats_with_sessions(self):
        """Stats with recorded sessions."""
        _analytics["sessions"] = [
            {
                "session_id": "s1",
                "agent_name": "cursor",
                "outcome": "success",
                "error_count": 0,
                "token_count": 1000,
                "recorded_at": datetime.now().isoformat()
            },
            {
                "session_id": "s2",
                "agent_name": "cursor",
                "outcome": "failure",
                "error_count": 2,
                "token_count": 500,
                "recorded_at": datetime.now().isoformat()
            }
        ]
        
        stats = get_team_stats(7)
        
        assert stats["total_sessions"] == 2
        assert stats["by_outcome"]["success"] == 1
        assert stats["by_outcome"]["failure"] == 1
        assert stats["success_rate"] == 0.5


class TestAgentPerformance:
    """Test agent performance metrics."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
    
    def test_performance_with_no_data(self):
        """Performance with no data."""
        perf = get_agent_performance("cursor", 7)
        assert perf == {}
    
    def test_all_agents_performance(self):
        """Get all agents performance."""
        _analytics["sessions"] = [
            {
                "session_id": "s1",
                "agent_name": "cursor",
                "outcome": "success",
                "error_count": 0,
                "token_count": 1000,
                "recorded_at": datetime.now().isoformat()
            }
        ]
        
        perf = get_agent_performance(days=7)
        
        assert "cursor" in perf
        assert perf["cursor"]["sessions"] == 1


class TestGenerateReport:
    """Test report generation."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
    
    def test_report_structure(self):
        """Report has expected structure."""
        report = generate_team_report(7)
        
        assert "generated_at" in report
        assert "period_days" in report
        assert "summary" in report
        assert "recommendations" in report


class TestExportAnalytics:
    """Test analytics export."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
    
    def test_export_json(self):
        """Export as JSON."""
        result = export_analytics("json", 7)
        
        # Should be valid JSON
        data = json.loads(result)
        assert "generated_at" in data
    
    def test_export_markdown(self):
        """Export as Markdown."""
        result = export_analytics("markdown", 7)
        
        assert "# Team Analytics Report" in result
        assert "## Summary" in result


class TestClearAnalytics:
    """Test analytics clearing."""
    
    def setup_method(self):
        """Clear analytics before each test."""
        _analytics.clear()
        _analytics["sessions"] = []
        _analytics["patterns"] = {}
    
    def test_clear_all(self):
        """Clear all analytics."""
        _analytics["sessions"] = [{"session_id": "s1"}]
        
        count = clear_analytics()
        
        assert count == 1
        assert len(_analytics["sessions"]) == 0
    
    def test_clear_older_than(self):
        """Clear older than days."""
        old_date = (datetime.now() - timedelta(days=30)).isoformat()
        new_date = datetime.now().isoformat()
        
        _analytics["sessions"] = [
            {"session_id": "old", "recorded_at": old_date},
            {"session_id": "new", "recorded_at": new_date}
        ]
        
        count = clear_analytics(older_than_days=7)
        
        assert count == 1
        assert len(_analytics["sessions"]) == 1
        assert _analytics["sessions"][0]["session_id"] == "new"
