"""Tests for agentlog._session — session context behavior."""

from agentlog import start_session, end_session, get_parent_session_id


def test_start_session_uses_explicit_parent_id():
    session_id = start_session("test-agent", "test-task", parent_session_id="sess_parent_explicit")

    assert session_id.startswith("sess_")
    assert get_parent_session_id() == "sess_parent_explicit"

    end_session()


def test_start_session_uses_env_parent_id_when_missing(monkeypatch):
    monkeypatch.setenv("AGENTLOG_PARENT_SESSION", "sess_parent_from_env")

    start_session("test-agent", "test-task")
    assert get_parent_session_id() == "sess_parent_from_env"

    end_session()


def test_start_session_explicit_parent_overrides_env(monkeypatch):
    monkeypatch.setenv("AGENTLOG_PARENT_SESSION", "sess_parent_from_env")

    start_session("test-agent", "test-task", parent_session_id="sess_parent_explicit")
    assert get_parent_session_id() == "sess_parent_explicit"

    end_session()
