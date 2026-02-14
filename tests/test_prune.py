"""
Tests for intelligent context pruning module (Phase 5).
"""

import pytest
import json
from agentlog._prune import (
    score_entry_importance,
    compress_entry,
    summarize_entries,
    prune_context,
    compress_context,
    get_context_summary,
)


class TestScoreEntryImportance:
    """Test importance scoring."""
    
    def test_error_entry_high_score(self):
        """Errors get highest score."""
        entry = {"tag": "error", "error": {"type": "ValueError"}}
        score = score_entry_importance(entry)
        assert score >= 100
    
    def test_session_entry_high_score(self):
        """Session entries get high score."""
        entry = {"tag": "session", "action": "start"}
        score = score_entry_importance(entry)
        assert score >= 90
    
    def test_info_entry_low_score(self):
        """Info entries get low score."""
        entry = {"tag": "info", "msg": "test"}
        score = score_entry_importance(entry)
        assert score < 50
    
    def test_failed_check_boost(self):
        """Failed checks get score boost."""
        passed = {"tag": "check", "passed": True}
        failed = {"tag": "check", "passed": False}
        
        passed_score = score_entry_importance(passed)
        failed_score = score_entry_importance(failed)
        
        assert failed_score > passed_score
    
    def test_failed_tool_boost(self):
        """Failed tools get score boost."""
        success = {"tag": "tool", "success": True}
        failure = {"tag": "tool", "success": False}
        
        success_score = score_entry_importance(success)
        failure_score = score_entry_importance(failure)
        
        assert failure_score > success_score


class TestCompressEntry:
    """Test entry compression."""
    
    def test_low_aggressiveness_no_compression(self):
        """Low aggressiveness keeps everything."""
        entry = {"tag": "error", "msg": "test", "extra": "data"}
        compressed = compress_entry(entry, "low")
        assert compressed == entry
    
    def test_medium_aggressiveness_keeps_essentials(self):
        """Medium aggressiveness keeps essential fields."""
        entry = {
            "tag": "error",
            "error": {"type": "ValueError", "msg": "test"},
            "fn": "process",
            "locals": {"x": 1, "y": 2}
        }
        compressed = compress_entry(entry, "medium")
        
        assert "tag" in compressed
        assert "error" in compressed
        assert "fn" in compressed
    
    def test_high_aggressiveness_removes_locals(self):
        """High aggressiveness removes locals."""
        entry = {
            "tag": "error",
            "error": {"type": "ValueError"},
            "locals": {"x": 1, "y": 2, "z": 3}
        }
        compressed = compress_entry(entry, "high")
        
        assert "locals" not in compressed
        assert "locals_keys" in compressed


class TestSummarizeEntries:
    """Test entry summarization."""
    
    def test_empty_entries(self):
        """Summarize empty list."""
        summary = summarize_entries([])
        assert summary["total"] == 0
    
    def test_counts_by_tag(self):
        """Summary counts by tag."""
        entries = [
            {"tag": "error", "error": {"type": "ValueError"}},
            {"tag": "error", "error": {"type": "TypeError"}},
            {"tag": "info", "msg": "test"}
        ]
        summary = summarize_entries(entries)
        
        assert summary["by_tag"]["error"] == 2
        assert summary["by_tag"]["info"] == 1
    
    def test_key_errors_extracted(self):
        """Key errors are extracted."""
        entries = [
            {"tag": "error", "error": {"type": "ValueError", "msg": "test error"}, "file": "app.py", "line": 42}
        ]
        summary = summarize_entries(entries)
        
        assert len(summary["key_errors"]) == 1
        assert summary["key_errors"][0]["type"] == "ValueError"


class TestPruneContext:
    """Test context pruning."""
    
    def test_prune_errors_only(self):
        """Errors only strategy."""
        result = prune_context([], max_tokens=1000, strategy="errors_only")
        data = json.loads(result)
        assert data["strategy"] == "errors_only"
    
    def test_prune_smart(self):
        """Smart pruning strategy."""
        result = prune_context([], max_tokens=1000, strategy="smart")
        data = json.loads(result)
        assert data["strategy"] == "smart"
    
    def test_prune_recent(self):
        """Recent pruning strategy."""
        result = prune_context([], max_tokens=1000, strategy="recent")
        data = json.loads(result)
        assert data["strategy"] == "recent"


class TestGetContextSummary:
    """Test context summary."""
    
    def test_summary_structure(self):
        """Summary has expected structure."""
        summary = get_context_summary()
        
        assert "session_id" in summary
        assert "total" in summary
        assert "by_tag" in summary
