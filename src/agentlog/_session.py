"""
Session management for agentlog.

Tracks the current agent session context (ID, agent name, task).
"""

import uuid
from typing import Optional, Dict, Any

from . import _core
from ._emit import emit
from ._git import get_git_info


def start_session(agent_name: str, task: str, parent_session_id: Optional[str] = None) -> str:
    """
    Start a new logging session.
    
    Args:
        agent_name: Name of the agent (e.g., "coding-agent").
        task: Description of the task being performed.
        parent_session_id: Optional parent session for tracking related work (Phase 2).
        
    Returns:
        The generated session ID.
    """
    session_id = f"sess_{uuid.uuid4().hex}"
    _core._session_id = session_id
    _core._agent_name = agent_name
    _core._task = task
    _core._parent_session_id = parent_session_id
    
    # Capture and emit git state
    git_info = get_git_info()
    
    data: Dict[str, Any] = {
        "action": "start",
        "session_id": session_id,
        "agent": agent_name,
        "task": task,
        "git": git_info
    }
    
    if parent_session_id:
        data["parent_session_id"] = parent_session_id
    
    emit("session", data)
    
    return session_id


def end_session() -> None:
    """End the current logging session."""
    _core._session_id = None
    _core._agent_name = None
    _core._task = None
    _core._parent_session_id = None


def get_session_id() -> Optional[str]:
    """Get the current session ID, if any."""
    return _core._session_id


def get_parent_session_id() -> Optional[str]:
    """Get the parent session ID for linked sessions (Phase 2)."""
    return _core._parent_session_id


def get_agent_info() -> Dict[str, Any]:
    """Get information about the current agent session."""
    return {
        "agent_name": _core._agent_name,
        "task": _core._task
    }
