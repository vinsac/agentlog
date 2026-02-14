"""
Git integration for agentlog.
Captures commit hash and diffs to provide code context.
"""

import subprocess
from typing import Dict, Any, Optional

from ._core import is_enabled
from ._emit import emit

_MAX_DIFF_LINES = 50


def get_git_info(cwd: Optional[str] = None) -> Dict[str, Any]:
    """Get current git state (commit, branch, diff)."""
    info: Dict[str, Any] = {
        "commit": None,
        "branch": None,
        "diff": None,
        "cached_diff": None,
        "dirty": False
    }

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        info["commit"] = commit

        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=cwd,
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            info["branch"] = branch
        except subprocess.CalledProcessError:
            pass

        diff = subprocess.check_output(
            ["git", "diff"],
            cwd=cwd,
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if diff:
            lines = diff.split("\n")
            info["diff"] = "\n".join(lines[:_MAX_DIFF_LINES])
            info["dirty"] = True
            if len(lines) > _MAX_DIFF_LINES:
                info["diff_truncated"] = len(lines)

        cached_diff = subprocess.check_output(
            ["git", "diff", "--cached"],
            cwd=cwd,
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if cached_diff:
            lines = cached_diff.split("\n")
            info["cached_diff"] = "\n".join(lines[:_MAX_DIFF_LINES])
            info["dirty"] = True
            if len(lines) > _MAX_DIFF_LINES:
                info["cached_diff_truncated"] = len(lines)

    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return info


def log_git_diff(turn_number: int, cwd: Optional[str] = None) -> None:
    """Log git diff between agent turns. First 50 lines only."""
    if not is_enabled():
        return

    info = get_git_info(cwd=cwd)
    if not info["commit"]:
        return

    diff_text = info.get("diff", "")
    lines = diff_text.split("\n") if diff_text else []
    lines_added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    lines_removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))

    data: Dict[str, Any] = {
        "turn_number": turn_number,
        "commit": info["commit"],
        "dirty": info["dirty"],
    }

    if diff_text:
        data["diff"] = diff_text
        data["lines_added"] = lines_added
        data["lines_removed"] = lines_removed

    if info.get("diff_truncated"):
        data["truncated"] = True

    emit("git_diff", data)
