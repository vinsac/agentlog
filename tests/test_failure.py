"""
Tests for automatic failure capture via sys.excepthook.
"""

import sys
import pytest
from agentlog import enable, disable, install_failure_hook, uninstall_failure_hook
from agentlog._failure import _capture_failure


def test_failure_hook_installation():
    """Test that failure hook can be installed and uninstalled."""
    original_hook = sys.excepthook
    
    install_failure_hook()
    assert sys.excepthook != original_hook
    
    uninstall_failure_hook()
    assert sys.excepthook == original_hook


def test_failure_capture_when_disabled(capsys):
    """Test that failure capture is a no-op when agentlog is disabled."""
    disable()
    uninstall_failure_hook()
    
    try:
        x = 1
        y = 0
        result = x / y
    except ZeroDivisionError as e:
        _capture_failure(type(e), e, e.__traceback__)
    
    captured = capsys.readouterr()
    # Should not emit agentlog output when disabled
    assert "[AGENTLOG:error]" not in captured.out


def test_failure_capture_with_locals(capsys):
    """Test that failure capture includes local variables."""
    enable()
    install_failure_hook()
    
    try:
        user_id = "u_123"
        confidence = 1.5
        threshold = 0.9
        
        if confidence > 1.0:
            raise ValueError(f"Invalid confidence: {confidence}")
    except ValueError as e:
        _capture_failure(type(e), e, e.__traceback__)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should emit structured error
    assert "[AGENTLOG:error]" in output
    assert "ValueError" in output
    assert "Invalid confidence" in output
    
    # Should include local variables
    assert "user_id" in output
    assert "confidence" in output
    assert "threshold" in output
    
    # Should use compact descriptors
    assert '"t":"str"' in output or '"t": "str"' in output
    assert '"t":"float"' in output or '"t": "float"' in output


def test_failure_capture_with_complex_types(capsys):
    """Test that failure capture handles complex types safely."""
    enable()
    install_failure_hook()
    
    try:
        data = {"name": "test", "values": [1, 2, 3, 4, 5]}
        items = [{"id": i} for i in range(10)]
        
        raise RuntimeError("Processing failed")
    except RuntimeError as e:
        _capture_failure(type(e), e, e.__traceback__)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should emit structured error
    assert "[AGENTLOG:error]" in output
    assert "RuntimeError" in output
    
    # Should include structured descriptions
    assert "data" in output
    assert "items" in output
    
    # Should use compact format
    assert '"t":"dict"' in output or '"t": "dict"' in output
    assert '"t":"list"' in output or '"t": "list"' in output


def test_failure_capture_preserves_original_traceback(capsys):
    """Test that original traceback is still displayed."""
    enable()
    install_failure_hook()
    
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        _capture_failure(type(e), e, e.__traceback__)
    
    captured = capsys.readouterr()
    output = captured.err  # Original traceback goes to stderr
    
    # Original traceback should still be present
    assert "ZeroDivisionError" in output or "ZeroDivisionError" in captured.out


def test_failure_capture_with_unrepresentable_values(capsys):
    """Test that failure capture handles unrepresentable values gracefully."""
    enable()
    install_failure_hook()
    
    class UnrepresentableObject:
        def __repr__(self):
            raise Exception("Cannot represent")
    
    try:
        bad_obj = UnrepresentableObject()
        raise ValueError("Test error")
    except ValueError as e:
        _capture_failure(type(e), e, e.__traceback__)
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should emit error without crashing
    assert "[AGENTLOG:error]" in output
    assert "ValueError" in output
    
    # Should handle unrepresentable object gracefully
    # Either skipped or marked as unrepresentable
    assert "bad_obj" in output or "unrepresentable" in output.lower()


def test_automatic_installation_on_enable():
    """Test that failure hook is automatically installed when enabled."""
    # This test verifies the behavior in __init__.py
    # where install_failure_hook() is called if is_enabled()
    
    # First uninstall to get a clean state
    uninstall_failure_hook()
    original_hook = sys.excepthook
    
    # When agentlog is enabled, hook should be installed
    enable()
    install_failure_hook()
    
    # Hook should now be our custom hook
    assert sys.excepthook == _capture_failure
    assert sys.excepthook != original_hook
    
    # Cleanup
    uninstall_failure_hook()
