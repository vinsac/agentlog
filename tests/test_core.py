"""Tests for agentlog._core — configuration, enable/disable, levels."""

import os
import pytest
from agentlog import _core


def test_enable_disable():
    _core.disable()
    assert not _core.is_enabled()
    _core.enable()
    assert _core.is_enabled()


def test_configure_level():
    _core.configure(level="error")
    assert _core._level == _core.LEVEL_ERROR
    _core.configure(level="debug")
    assert _core._level == _core.LEVEL_DEBUG


def test_configure_tag_prefix():
    _core.configure(tag_prefix="MYAPP")
    assert _core.get_tag_prefix() == "MYAPP"
    _core.configure(tag_prefix="AGENTLOG")


def test_should_emit_respects_level():
    _core.enable()
    _core.configure(level="error")
    assert not _core.should_emit("info")
    assert not _core.should_emit("vars")
    assert _core.should_emit("error")
    _core.configure(level="debug")
    assert _core.should_emit("info")
    assert _core.should_emit("vars")


def test_should_emit_when_disabled():
    _core.disable()
    assert not _core.should_emit("info")
    assert not _core.should_emit("error")


def test_tag_levels_mapping():
    assert _core.TAG_LEVELS["vars"] == _core.LEVEL_DEBUG
    assert _core.TAG_LEVELS["info"] == _core.LEVEL_INFO
    assert _core.TAG_LEVELS["check"] == _core.LEVEL_WARN
    assert _core.TAG_LEVELS["error"] == _core.LEVEL_ERROR


def test_backward_compat_aliases():
    assert _core.enable_dev_logging is _core.enable
    assert _core.disable_dev_logging is _core.disable


def test_env_detection(monkeypatch):
    _core._enabled = None
    monkeypatch.setenv("AGENTLOG", "true")
    assert _core._detect_enabled() is True

    monkeypatch.delenv("AGENTLOG")
    monkeypatch.setenv("DEVLOG", "1")
    assert _core._detect_enabled() is True

    monkeypatch.delenv("DEVLOG")
    assert _core._detect_enabled() is False


def test_level_detection(monkeypatch):
    monkeypatch.setenv("AGENTLOG_LEVEL", "warn")
    assert _core._detect_level() == _core.LEVEL_WARN

    monkeypatch.setenv("AGENTLOG_LEVEL", "invalid")
    assert _core._detect_level() == _core.LEVEL_DEBUG

    monkeypatch.delenv("AGENTLOG_LEVEL")
    assert _core._detect_level() == _core.LEVEL_DEBUG
