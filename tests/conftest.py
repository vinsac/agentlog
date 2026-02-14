"""Shared test fixtures for agentlog tests."""

import sys
import os
import logging
import pytest

# Add src to path for testing without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(autouse=True)
def reset_agentlog():
    """Reset agentlog state before each test."""
    import agentlog
    from agentlog import _core, _emit, _buffer

    # Enable for tests
    _core._enabled = True
    _core._level = _core.LEVEL_DEBUG
    _core._tag_prefix = "AGENTLOG"

    # Reset sequence
    _emit._sequence = 0

    # Reset trace context
    _emit._trace_id = None
    _emit._span_stack.clear()

    # Reset JSONL file
    _emit._jsonl_file = None

    # Reset handler so it gets re-created fresh
    _emit._handler_installed = False
    _emit._logger.handlers.clear()

    # Reset ringbuffer
    from collections import deque
    _buffer._ringbuffer = deque(maxlen=500)

    yield

    # Cleanup
    _core._enabled = None
