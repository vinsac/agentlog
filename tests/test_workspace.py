"""
Tests for workspace snapshot module (Phase 2).
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from agentlog._workspace import (
    hash_file,
    hash_string,
    snapshot_workspace,
    compare_snapshots,
    save_snapshot,
    load_snapshot,
    delete_snapshot,
    list_snapshots,
    _snapshots,
    _SNAPSHOT_FILE,
)


class TestHashing:
    """Test file and string hashing."""
    
    def test_hash_file_exists(self, tmp_path):
        """Hash existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        h = hash_file(str(test_file))
        assert h is not None
        assert len(h) == 16  # Truncated MD5
    
    def test_hash_file_not_exists(self):
        """Hash non-existent file returns None."""
        h = hash_file("/nonexistent/path/file.txt")
        assert h is None
    
    def test_hash_string(self):
        """Hash string content."""
        h1 = hash_string("hello")
        h2 = hash_string("hello")
        h3 = hash_string("world")
        
        assert h1 == h2  # Same content, same hash
        assert h1 != h3  # Different content
        assert len(h1) == 16


class TestSnapshotWorkspace:
    """Test workspace snapshot creation."""
    
    def test_snapshot_empty_directory(self, tmp_path):
        """Snapshot empty directory."""
        os.chdir(tmp_path)
        snapshot = snapshot_workspace(paths=['.'])
        
        assert 'timestamp' in snapshot
        assert 'files' in snapshot
        assert snapshot['file_count'] >= 0
    
    def test_snapshot_with_files(self, tmp_path):
        """Snapshot with Python files."""
        os.chdir(tmp_path)
        
        # Create test files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        
        snapshot = snapshot_workspace(
            paths=['.'],
            include_patterns=['*.py']
        )
        
        assert snapshot['file_count'] == 2
        assert any('main.py' in k for k in snapshot['files'].keys())
        assert any('utils.py' in k for k in snapshot['files'].keys())
    
    def test_snapshot_excludes_pycache(self, tmp_path):
        """Snapshot excludes __pycache__."""
        os.chdir(tmp_path)
        
        # Create files
        (tmp_path / "main.py").write_text("print('hello')")
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "main.cpython-39.pyc").write_text("bytecode")
        
        snapshot = snapshot_workspace(paths=['.'])
        
        # Should not include pycache files
        assert not any('__pycache__' in k for k in snapshot['files'].keys())
    
    def test_snapshot_respects_include_patterns(self, tmp_path):
        """Snapshot respects include patterns."""
        os.chdir(tmp_path)
        
        (tmp_path / "script.py").write_text("python")
        (tmp_path / "readme.md").write_text("markdown")
        (tmp_path / "data.json").write_text('{"key": "value"}')
        
        snapshot = snapshot_workspace(
            paths=['.'],
            include_patterns=['*.py', '*.json']
        )
        
        # Should only include .py and .json
        files = list(snapshot['files'].keys())
        assert any('.py' in f for f in files)
        assert any('.json' in f for f in files)
        assert not any('.md' in f for f in files)


class TestCompareSnapshots:
    """Test snapshot comparison."""
    
    def test_compare_no_changes(self, tmp_path):
        """Compare identical snapshots."""
        os.chdir(tmp_path)
        
        (tmp_path / "file.txt").write_text("content")
        
        old = snapshot_workspace(paths=['.'])
        new = snapshot_workspace(paths=['.'])
        
        changes = compare_snapshots(old, new)
        
        assert changes['added'] == []
        assert changes['removed'] == []
        assert changes['modified'] == []
    
    def test_compare_added_files(self, tmp_path):
        """Detect added files."""
        os.chdir(tmp_path)
        
        (tmp_path / "old.txt").write_text("old content")
        old = snapshot_workspace(paths=['.'])
        
        (tmp_path / "new.txt").write_text("new content")
        new = snapshot_workspace(paths=['.'])
        
        changes = compare_snapshots(old, new)
        
        assert 'new.txt' in changes['added']
        assert changes['removed'] == []
    
    def test_compare_removed_files(self, tmp_path):
        """Detect removed files."""
        os.chdir(tmp_path)
        
        (tmp_path / "keep.txt").write_text("keep")
        (tmp_path / "remove.txt").write_text("remove")
        old = snapshot_workspace(paths=['.'])
        
        (tmp_path / "remove.txt").unlink()
        new = snapshot_workspace(paths=['.'])
        
        changes = compare_snapshots(old, new)
        
        assert 'remove.txt' in changes['removed']
        assert changes['added'] == []
    
    def test_compare_modified_files(self, tmp_path):
        """Detect modified files."""
        os.chdir(tmp_path)
        
        test_file = tmp_path / "file.txt"
        test_file.write_text("original")
        old = snapshot_workspace(paths=['.'])
        
        test_file.write_text("modified")
        new = snapshot_workspace(paths=['.'])
        
        changes = compare_snapshots(old, new)
        
        assert 'file.txt' in changes['modified']


class TestSnapshotStorage:
    """Test snapshot persistence."""
    
    def setup_method(self):
        """Clear snapshots before each test."""
        _snapshots.clear()
        if os.path.exists(_SNAPSHOT_FILE):
            os.remove(_SNAPSHOT_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _snapshots.clear()
        if os.path.exists(_SNAPSHOT_FILE):
            os.remove(_SNAPSHOT_FILE)
        # Clean up .agentlog dir if empty
        if os.path.exists(".agentlog") and not os.listdir(".agentlog"):
            os.rmdir(".agentlog")
    
    def test_save_and_load_snapshot(self, tmp_path):
        """Save and load snapshot."""
        os.chdir(tmp_path)
        
        snapshot = {"file_count": 5, "files": {}}
        save_snapshot("test_id", snapshot)
        
        loaded = load_snapshot("test_id")
        assert loaded == snapshot
    
    def test_load_nonexistent_snapshot(self, tmp_path):
        """Load non-existent snapshot returns None."""
        os.chdir(tmp_path)
        
        loaded = load_snapshot("nonexistent")
        assert loaded is None
    
    def test_delete_snapshot(self, tmp_path):
        """Delete saved snapshot."""
        os.chdir(tmp_path)
        
        save_snapshot("to_delete", {"files": {}})
        assert delete_snapshot("to_delete") is True
        
        loaded = load_snapshot("to_delete")
        assert loaded is None
    
    def test_delete_nonexistent(self, tmp_path):
        """Delete non-existent snapshot returns False."""
        os.chdir(tmp_path)
        
        result = delete_snapshot("nonexistent")
        assert result is False
    
    def test_list_snapshots(self, tmp_path):
        """List all saved snapshots."""
        os.chdir(tmp_path)
        
        save_snapshot("snap1", {"files": {}})
        save_snapshot("snap2", {"files": {}})
        
        ids = list_snapshots()
        assert "snap1" in ids
        assert "snap2" in ids
