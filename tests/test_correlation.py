"""
Tests for error correlation module (Phase 2).
"""

import pytest
import os
import json
import tempfile
from agentlog._correlation import (
    hash_error,
    record_error_pattern,
    get_error_pattern,
    get_all_patterns,
    find_similar_errors,
    correlate_error,
    get_pattern_stats,
    _patterns,
    _PATTERN_FILE,
)


class TestErrorHashing:
    """Test error pattern hashing."""
    
    def test_hash_error_consistency(self):
        """Same error should produce same hash."""
        h1 = hash_error('ValueError', 'app.py', 42)
        h2 = hash_error('ValueError', 'app.py', 42)
        assert h1 == h2
        assert h1.startswith('err_')
    
    def test_hash_error_different_lines(self):
        """Different lines produce different hashes."""
        h1 = hash_error('ValueError', 'app.py', 42)
        h2 = hash_error('ValueError', 'app.py', 43)
        assert h1 != h2
    
    def test_hash_error_different_files(self):
        """Different files produce different hashes."""
        h1 = hash_error('ValueError', 'app.py', 42)
        h2 = hash_error('ValueError', 'utils.py', 42)
        assert h1 != h2
    
    def test_hash_error_different_types(self):
        """Different error types produce different hashes."""
        h1 = hash_error('ValueError', 'app.py', 42)
        h2 = hash_error('TypeError', 'app.py', 42)
        assert h1 != h2


class TestPatternRecording:
    """Test error pattern recording and retrieval."""
    
    def setup_method(self):
        """Clear patterns before each test."""
        _patterns.clear()
        # Clean up pattern file if it exists
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def test_record_new_pattern(self):
        """Recording a new error creates a pattern."""
        h = record_error_pattern('ValueError', 'app.py', 42)
        
        pattern = get_error_pattern(h)
        assert pattern is not None
        assert pattern['error_type'] == 'ValueError'
        assert pattern['location']['file'] == 'app.py'
        assert pattern['location']['line'] == 42
        assert pattern['count'] == 1
    
    def test_record_existing_pattern_increments_count(self):
        """Recording same error increments count."""
        h1 = record_error_pattern('ValueError', 'app.py', 42)
        h2 = record_error_pattern('ValueError', 'app.py', 42)
        
        assert h1 == h2
        pattern = get_error_pattern(h1)
        assert pattern['count'] == 2
    
    def test_record_with_session_id(self):
        """Recording with session tracks sessions."""
        h = record_error_pattern(
            'ValueError', 'app.py', 42,
            session_id='sess_abc123'
        )
        
        pattern = get_error_pattern(h)
        assert 'sess_abc123' in pattern['sessions']
    
    def test_record_with_context(self):
        """Recording with context stores context."""
        h = record_error_pattern(
            'ValueError', 'app.py', 42,
            context={'msg': 'test error'}
        )
        
        pattern = get_error_pattern(h)
        assert len(pattern['contexts']) == 1
        assert pattern['contexts'][0]['ctx']['msg'] == 'test error'


class TestPatternCorrelation:
    """Test error correlation features."""
    
    def setup_method(self):
        """Clear patterns before each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def test_correlate_new_error(self):
        """Correlating new error shows is_new=True."""
        result = correlate_error('ValueError', 'app.py', 42)
        
        assert result['is_new'] is True
        assert result['times_seen_before'] == 0
    
    def test_correlate_existing_error(self):
        """Correlating existing error shows history."""
        # Record error twice
        record_error_pattern('ValueError', 'app.py', 42)
        record_error_pattern('ValueError', 'app.py', 42)
        
        result = correlate_error('ValueError', 'app.py', 42)
        
        assert result['is_new'] is False
        assert result['times_seen_before'] == 1
    
    def test_correlate_finds_similar_same_file(self):
        """Correlation finds similar errors in same file."""
        record_error_pattern('ValueError', 'app.py', 10)
        record_error_pattern('TypeError', 'app.py', 20)
        
        result = correlate_error('AttributeError', 'app.py', 30)
        
        # Should find the other errors in same file
        assert len(result['similar_errors']) > 0


class TestPatternStats:
    """Test pattern statistics."""
    
    def setup_method(self):
        """Clear patterns before each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def test_empty_stats(self):
        """Stats with no patterns."""
        stats = get_pattern_stats()
        assert stats['total_unique'] == 0
        assert stats['total_occurrences'] == 0
    
    def test_stats_with_patterns(self):
        """Stats with recorded patterns."""
        record_error_pattern('ValueError', 'app.py', 42)
        record_error_pattern('ValueError', 'app.py', 42)  # Same, count=2
        record_error_pattern('TypeError', 'utils.py', 10)  # New pattern
        
        stats = get_pattern_stats()
        
        assert stats['total_unique'] == 2
        assert stats['total_occurrences'] == 3
        assert stats['files_affected'] == 2


class TestFindSimilarErrors:
    """Test finding similar errors."""
    
    def setup_method(self):
        """Clear patterns before each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def teardown_method(self):
        """Clean up after each test."""
        _patterns.clear()
        if os.path.exists(_PATTERN_FILE):
            os.remove(_PATTERN_FILE)
    
    def test_find_same_file_errors(self):
        """Find errors in same file."""
        record_error_pattern('ValueError', 'app.py', 10)
        record_error_pattern('TypeError', 'app.py', 20)
        record_error_pattern('KeyError', 'other.py', 5)
        
        similar = find_similar_errors('AttributeError', 'app.py', 30)
        
        # Should find app.py errors, not other.py
        files = [s['location']['file'] for s in similar]
        assert 'app.py' in files
        assert 'other.py' not in files
    
    def test_find_same_type_errors(self):
        """Find errors of same type."""
        record_error_pattern('ValueError', 'app.py', 10)
        record_error_pattern('ValueError', 'utils.py', 20)
        
        similar = find_similar_errors('ValueError', 'main.py', 5)
        
        # Should find ValueErrors regardless of file
        types = [s['error_type'] for s in similar]
        assert all(t == 'ValueError' for t in types)
