"""Tests for agentlog._sink — JSONL file sink."""

import json
import os
import tempfile
import pytest
from agentlog import log, to_file, close_file


def test_jsonl_file_sink():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.jsonl")
        to_file(path)
        log("file test 1")
        log("file test 2", x=42)
        close_file()

        with open(path) as f:
            lines = f.readlines()

        assert len(lines) == 2
        entry1 = json.loads(lines[0])
        assert entry1["msg"] == "file test 1"
        entry2 = json.loads(lines[1])
        assert entry2["msg"] == "file test 2"
        assert entry2["ctx"]["x"]["v"] == 42


def test_jsonl_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "subdir", "nested", "test.jsonl")
        to_file(path)
        log("nested test")
        close_file()

        assert os.path.exists(path)
        with open(path) as f:
            entry = json.loads(f.readline())
        assert entry["msg"] == "nested test"


def test_close_file_is_safe_when_no_file():
    # Should not raise
    close_file()


def test_jsonl_appends():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "append.jsonl")
        to_file(path)
        log("first")
        close_file()

        to_file(path)
        log("second")
        close_file()

        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 2
