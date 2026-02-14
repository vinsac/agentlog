"""
Automatic failure capture via sys.excepthook.

This is the foundational feature: zero-instrumentation runtime visibility
at failure boundaries. When any unhandled exception occurs, we automatically
capture the local variables and emit structured context for AI agents.
"""

import sys
import traceback
from typing import Any, Dict

from ._core import is_enabled
from ._describe import describe
from ._emit import emit


# Store original excepthook to call after our processing
_original_excepthook = sys.excepthook
_hook_installed = False


def _capture_failure(exc_type, exc_value, exc_traceback):
    """
    Capture structured failure context when unhandled exceptions occur.
    
    This function is installed as sys.excepthook to automatically capture
    runtime state at failure boundaries without requiring any instrumentation.
    """
    if not is_enabled():
        # Call original hook and return
        _original_excepthook(exc_type, exc_value, exc_traceback)
        return
    
    # Extract frame information from the traceback
    if exc_traceback is not None:
        # Walk to the bottom frame (where the error occurred)
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        # Capture local variables at failure point
        locals_dict = {}
        for name, value in frame.f_locals.items():
            try:
                locals_dict[name] = describe(value)
            except Exception:
                # If we can't describe a value, skip it
                locals_dict[name] = {"t": "object", "error": "unrepresentable"}
        
        # Build structured error context
        error_data = {
            "fn": frame.f_code.co_name,
            "file": frame.f_code.co_filename,
            "line": frame.f_lineno,
            "error": {
                "type": exc_type.__name__,
                "msg": str(exc_value),
            },
            "locals": locals_dict,
        }
        
        # Inject session_id if available
        from ._session import get_session_id
        session_id = get_session_id()
        if session_id:
            error_data["session_id"] = session_id
        
        # Record error pattern for cross-run correlation
        try:
            from ._correlation import record_error_pattern
            record_error_pattern(
                error_type=exc_type.__name__,
                filename=frame.f_code.co_filename,
                line=frame.f_lineno,
                session_id=session_id,
                context={"msg": str(exc_value)[:200]}
            )
        except Exception:
            pass  # Silent fail - correlation is optional
        
        # Emit the structured failure context
        # Use depth=0 since we're already at the right frame
        emit("error", error_data, depth=0)
    
    # Call original excepthook to display normal traceback
    _original_excepthook(exc_type, exc_value, exc_traceback)


def install_failure_hook():
    """
    Install the automatic failure capture hook.
    
    This should be called once when agentlog is imported and enabled.
    It's safe to call multiple times - it will only install once.
    """
    global _hook_installed
    if not _hook_installed:
        sys.excepthook = _capture_failure
        _hook_installed = True


def uninstall_failure_hook():
    """
    Restore the original excepthook.
    
    This is useful for testing or if users want to disable automatic capture.
    """
    global _hook_installed
    if _hook_installed:
        sys.excepthook = _original_excepthook
        _hook_installed = False
