"""
IO Capture utilities for isolation tool outputs.
"""

import sys
import io
from contextlib import contextmanager
from typing import Generator, Tuple

@contextmanager
def capture_io() -> Generator[Tuple[io.StringIO, io.StringIO], None, None]:
    """
    Capture stdout and stderr.
    
    Yields:
        (stdout_capture, stderr_capture) streams.
    """
    # Create new streams
    new_out = io.StringIO()
    new_err = io.StringIO()
    
    # Save original streams
    old_out = sys.stdout
    old_err = sys.stderr
    
    try:
        # Redirect
        sys.stdout = new_out
        sys.stderr = new_err
        yield new_out, new_err
    finally:
        # Restore
        sys.stdout = old_out
        sys.stderr = old_err
