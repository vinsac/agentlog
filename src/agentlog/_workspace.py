"""
Workspace state snapshots for agentlog.

Lightweight file hash tracking for cross-run correlation.
Helps agents know what files existed when an error occurred.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime


# ---------------------------------------------------------------------------
# File Hashing
# ---------------------------------------------------------------------------

def hash_file(filepath: str) -> Optional[str]:
    """
    Compute MD5 hash of file contents.
    
    Args:
        filepath: Path to file
        
    Returns:
        Hex digest or None if file cannot be read
    """
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:16]
    except (IOError, OSError):
        return None


def hash_string(content: str) -> str:
    """Compute hash of string content."""
    return hashlib.md5(content.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Workspace Snapshot
# ---------------------------------------------------------------------------

def snapshot_workspace(
    paths: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create lightweight snapshot of workspace state using file hashes.
    
    Args:
        paths: Directories/files to scan (default: current directory)
        include_patterns: Glob patterns to include (e.g., ['*.py', '*.json'])
        exclude_patterns: Glob patterns to exclude (e.g., ['*.pyc', '__pycache__/*'])
        
    Returns:
        Snapshot dict with file hashes and metadata
        
    Example:
        >>> snapshot = snapshot_workspace(
        ...     paths=['src/', 'tests/'],
        ...     include_patterns=['*.py']
        ... )
        >>> snapshot['files']['src/main.py']
        'a3f7b2c1d5e8f9a0'
    """
    if paths is None:
        paths = ['.']
    
    if include_patterns is None:
        include_patterns = ['*']
    
    if exclude_patterns is None:
        exclude_patterns = [
            '*.pyc', '__pycache__/*', '*.pyo', '.git/*', 
            '.agentlog/*', '*.egg-info/*', '.pytest_cache/*',
            'node_modules/*', '.venv/*', 'venv/*'
        ]
    
    files: Dict[str, str] = {}
    dirs: Set[str] = set()
    
    for path in paths:
        p = Path(path)
        if p.is_file():
            file_hash = hash_file(str(p))
            if file_hash:
                files[str(p)] = file_hash
        elif p.is_dir():
            try:
                for item in p.rglob('*'):
                    # Check exclude patterns
                    excluded = any(
                        item.match(pattern) or str(item).startswith('.')
                        for pattern in exclude_patterns
                    )
                    if excluded:
                        continue
                    
                    # Check include patterns
                    included = any(item.match(pattern) for pattern in include_patterns)
                    
                    if item.is_file() and included:
                        rel_path = str(item.relative_to(p.parent if p != Path('.') else p))
                        file_hash = hash_file(str(item))
                        if file_hash:
                            files[rel_path] = file_hash
                    elif item.is_dir():
                        dirs.add(str(item))
            except (OSError, PermissionError):
                pass  # Skip inaccessible directories
    
    return {
        "timestamp": datetime.now().isoformat(),
        "file_count": len(files),
        "dir_count": len(dirs),
        "files": files
    }


def compare_snapshots(
    old: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare two workspace snapshots to find changes.
    
    Args:
        old: Previous snapshot
        new: Current snapshot
        
    Returns:
        Dict with added, removed, and modified files
        
    Example:
        >>> changes = compare_snapshots(old_snap, new_snap)
        >>> changes['modified']
        ['src/main.py']
    """
    old_files = old.get('files', {})
    new_files = new.get('files', {})
    
    old_keys = set(old_files.keys())
    new_keys = set(new_files.keys())
    
    added = list(new_keys - old_keys)
    removed = list(old_keys - new_keys)
    
    modified = []
    for path in old_keys & new_keys:
        if old_files[path] != new_files[path]:
            modified.append(path)
    
    return {
        "added": sorted(added),
        "removed": sorted(removed),
        "modified": sorted(modified),
        "unchanged": len(old_keys & new_keys) - len(modified)
    }


# ---------------------------------------------------------------------------
# Snapshot Storage
# ---------------------------------------------------------------------------

_SNAPSHOT_FILE = ".agentlog/workspace_snapshots.json"
_snapshots: Dict[str, Dict[str, Any]] = {}
_snapshots_loaded = False


def _load_snapshots() -> Dict[str, Dict[str, Any]]:
    """Load snapshots from disk."""
    global _snapshots, _snapshots_loaded
    
    if _snapshots_loaded:
        return _snapshots
    
    try:
        if os.path.exists(_SNAPSHOT_FILE):
            with open(_SNAPSHOT_FILE, 'r') as f:
                _snapshots = json.load(f)
    except (json.JSONDecodeError, IOError):
        _snapshots = {}
    
    _snapshots_loaded = True
    return _snapshots


def _save_snapshots():
    """Save snapshots to disk."""
    Path(".agentlog").mkdir(exist_ok=True)
    try:
        with open(_SNAPSHOT_FILE, 'w') as f:
            json.dump(_snapshots, f, indent=2)
    except IOError:
        pass  # Silent fail - disk storage is optional


def save_snapshot(
    snapshot_id: str,
    snapshot: Dict[str, Any]
) -> None:
    """
    Save a named snapshot for later comparison.
    
    Args:
        snapshot_id: Unique identifier for this snapshot
        snapshot: Snapshot data from snapshot_workspace()
    """
    _load_snapshots()
    _snapshots[snapshot_id] = snapshot
    _save_snapshots()


def load_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a previously saved snapshot.
    
    Args:
        snapshot_id: Snapshot identifier
        
    Returns:
        Snapshot data or None if not found
    """
    _load_snapshots()
    return _snapshots.get(snapshot_id)


def delete_snapshot(snapshot_id: str) -> bool:
    """
    Delete a saved snapshot.
    
    Args:
        snapshot_id: Snapshot identifier
        
    Returns:
        True if deleted, False if not found
    """
    _load_snapshots()
    if snapshot_id in _snapshots:
        del _snapshots[snapshot_id]
        _save_snapshots()
        return True
    return False


def list_snapshots() -> List[str]:
    """List all saved snapshot IDs."""
    _load_snapshots()
    return list(_snapshots.keys())


# ---------------------------------------------------------------------------
# Integration with Sessions
# ---------------------------------------------------------------------------

def snapshot_session(
    session_id: Optional[str] = None,
    paths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create and save a snapshot associated with a session.
    
    Args:
        session_id: Session ID to associate with (default: current session)
        paths: Paths to include in snapshot
        
    Returns:
        Snapshot data
    """
    from ._session import get_session_id
    
    if session_id is None:
        session_id = get_session_id()
    
    if session_id is None:
        session_id = "unknown"
    
    snapshot = snapshot_workspace(paths)
    snapshot["session_id"] = session_id
    
    save_snapshot(f"session_{session_id}", snapshot)
    
    return snapshot


def compare_to_session_baseline(
    session_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Compare current workspace to session's baseline snapshot.
    
    Args:
        session_id: Session to compare against (default: current session)
        
    Returns:
        Comparison results or None if no baseline exists
    """
    from ._session import get_session_id
    
    if session_id is None:
        session_id = get_session_id()
    
    if session_id is None:
        return None
    
    baseline = load_snapshot(f"session_{session_id}")
    if baseline is None:
        return None
    
    current = snapshot_workspace()
    changes = compare_snapshots(baseline, current)
    changes["session_id"] = session_id
    
    return changes
