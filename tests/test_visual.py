"""
Tests for visual diff rendering module.
"""

import pytest
from agentlog._visual import (
    parse_diff,
    render_diff_markdown,
    render_diff_html,
    summarize_diff,
    get_diff_summary,
)


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1234567..abcdefg 100644
--- a/app.py
+++ b/app.py
@@ -10,7 +10,7 @@ def process_data(data):
     if not data:
         return None
-    result = data * 2
+    result = data * 3
     return result
 
 def main():
"""


class TestParseDiff:
    """Test diff parsing."""
    
    def test_parse_file_header(self):
        """Parse file header from diff."""
        chunks = parse_diff(SAMPLE_DIFF)
        assert len(chunks) == 1
        assert chunks[0]["file"] == "app.py"
    
    def test_parse_hunk_header(self):
        """Parse hunk header."""
        chunks = parse_diff(SAMPLE_DIFF)
        lines = chunks[0]["lines"]
        
        hunk = [l for l in lines if l["type"] == "hunk"][0]
        assert hunk["old_start"] == 10
        assert hunk["new_start"] == 10
    
    def test_parse_additions(self):
        """Parse added lines."""
        chunks = parse_diff(SAMPLE_DIFF)
        lines = chunks[0]["lines"]
        
        adds = [l for l in lines if l["type"] == "add"]
        assert len(adds) == 1
        assert "result = data * 3" in adds[0]["content"]
    
    def test_parse_removals(self):
        """Parse removed lines."""
        chunks = parse_diff(SAMPLE_DIFF)
        lines = chunks[0]["lines"]
        
        removes = [l for l in lines if l["type"] == "remove"]
        assert len(removes) == 1
        assert "result = data * 2" in removes[0]["content"]


class TestRenderMarkdown:
    """Test markdown rendering."""
    
    def test_render_includes_header(self):
        """Markdown includes header."""
        result = render_diff_markdown(SAMPLE_DIFF)
        assert "## Code Changes" in result
    
    def test_render_includes_filename(self):
        """Markdown includes filename."""
        result = render_diff_markdown(SAMPLE_DIFF)
        assert "app.py" in result
    
    def test_render_includes_code_block(self):
        """Markdown includes diff code block."""
        result = render_diff_markdown(SAMPLE_DIFF)
        assert "```diff" in result


class TestRenderHTML:
    """Test HTML rendering."""
    
    def test_render_includes_container(self):
        """HTML includes container."""
        result = render_diff_html(SAMPLE_DIFF)
        assert '<div class="diff-review">' in result
    
    def test_render_includes_styles(self):
        """HTML includes styles."""
        result = render_diff_html(SAMPLE_DIFF)
        assert "<style>" in result
    
    def test_render_includes_spans(self):
        """HTML includes styled spans."""
        result = render_diff_html(SAMPLE_DIFF)
        assert '<span class="add">' in result
        assert '<span class="remove">' in result


class TestSummarizeDiff:
    """Test diff summarization."""
    
    def test_summary_counts(self):
        """Summary counts files and lines."""
        summary = summarize_diff(SAMPLE_DIFF)
        
        assert summary["files_changed"] == 1
        assert summary["lines_added"] >= 1
        assert summary["lines_removed"] >= 1
    
    def test_detects_modified_files(self):
        """Summary detects modified files."""
        summary = summarize_diff(SAMPLE_DIFF)
        
        assert summary["modified_files"] >= 1
        assert summary["new_files"] == 0
        assert summary["deleted_files"] == 0
    
    def test_file_changes_list(self):
        """Summary includes file changes list."""
        summary = summarize_diff(SAMPLE_DIFF)
        
        assert len(summary["file_changes"]) == 1
        assert summary["file_changes"][0]["file"] == "app.py"


class TestGetDiffSummary:
    """Test get_diff_summary function."""
    
    def test_summary_structure(self):
        """Summary has expected structure."""
        # This test may fail if not in a git repo, which is OK
        summary = get_diff_summary()
        
        assert "has_changes" in summary
        if summary["has_changes"]:
            assert "files_changed" in summary
            assert "lines_added" in summary
            assert "lines_removed" in summary
