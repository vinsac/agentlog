"""
JSONL file sink for persistent log replay.

AI agents can be pointed at the file for full session replay,
surviving terminal scroll-back limits.
"""

import os

from . import _emit


def to_file(path: str) -> None:
    """
    Enable writing all agentlog output to a JSONL file.
    Each line is a valid JSON object for easy parsing.

    Example:
        to_file(".agentlog/session.jsonl")
        # ... run your code ...
        close_file()
    """
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    f = open(path, "a", encoding="utf-8")
    _emit.set_jsonl_file(f)


def close_file() -> None:
    """Close the JSONL file sink."""
    f = _emit.get_jsonl_file()
    if f is not None:
        lock = _emit.get_jsonl_lock()
        with lock:
            f.close()
            _emit.set_jsonl_file(None)
