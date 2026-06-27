"""Tests for the v2 context/capture/redaction base."""

import json

import agentlog
from agentlog._describe import describe


def _json_lines(context):
    return [
        json.loads(line)
        for line in context.splitlines()
        if line and not line.startswith("#")
    ]


def test_nested_dict_secrets_are_redacted():
    descriptor = describe(
        {
            "username": "vinay",
            "password": "super-secret",
            "profile": {"email": "person@example.com"},
        }
    )

    assert descriptor["v"]["username"] == "vinay"
    assert descriptor["v"]["password"] == "***REDACTED_FIELD***"
    assert descriptor["v"]["profile"]["email"] == "***REDACTED_PII***"


def test_configurable_redaction_policy_on_context(capsys):
    agentlog.configure_redaction(deny_fields=["customer_id"])
    agentlog.log("received payload", customer_id="cust_123", safe_id="ok")

    out = capsys.readouterr().out
    entry = json.loads(out.strip().split("] ", 1)[1])

    assert entry["ctx"]["customer_id"]["v"] == "***REDACTED_FIELD***"
    assert entry["ctx"]["safe_id"]["v"] == "ok"


def test_v2_capture_and_incident_filtering():
    agentlog.capture_decision(
        "route_payment",
        "manual_review",
        candidates=["approve", "manual_review"],
        score=0.62,
        incident_id="inc_keep",
    )
    agentlog.capture_tool_call(
        "validate_payment",
        input={"api_key": "sk-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
        output={"ok": True},
        incident_id="inc_drop",
    )

    context = agentlog.get_debug_context(
        token_budget=1200,
        incident_id="inc_keep",
        include_metadata=True,
        explain=True,
    )
    lines = _json_lines(context)

    assert "# redaction:" in context
    assert "# filter: incident_id=inc_keep" in context
    assert len(lines) == 1
    assert lines[0]["tag"] == "decision"
    assert lines[0]["incident_id"] == "inc_keep"
    assert "validate_payment" not in context


def test_explain_mode_reports_budget_drops():
    for index in range(20):
        agentlog.log("large", index=index, payload="x" * 500)
    agentlog.log_error("important failure")

    context = agentlog.get_debug_context(token_budget=120, explain=True)

    assert "# budget:" in context
    assert "# selection:" in context
    assert "important failure" in context


def test_exception_messages_and_tracebacks_are_redacted():
    try:
        raise RuntimeError("failed with Bearer abcdefghijklmnop")
    except RuntimeError as error:
        agentlog.capture_tool_call("charge_card", error=error, incident_id="inc_secret")
        agentlog.log_error("charge failed", error, incident_id="inc_secret")

    context = agentlog.get_debug_context(token_budget=1200, incident_id="inc_secret")

    assert "Bearer abcdefghijklmnop" not in context
    assert "***BEARER_TOKEN***" in context
