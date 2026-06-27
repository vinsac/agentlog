"""Tests for durable handoff storage, CLI, and observability adapters."""

import json
import logging
import os

import agentlog
from agentlog.cli import main as cli_main


def test_incident_store_persists_and_exports_bundle(tmp_path):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path))

    agentlog.capture_decision(
        "route",
        "manual_review",
        candidates=["approve", "manual_review"],
        incident_id="inc_1",
        request_id="req_1",
    )
    agentlog.log_error("failed", RuntimeError("secret Bearer abcdefghijklmnop"), incident_id="inc_1")

    incidents = agentlog.list_incidents(str(path))
    assert incidents[0]["incident_id"] == "inc_1"
    assert incidents[0]["events"] == 2

    bundle = agentlog.export_debug_bundle(
        incident_id="inc_1",
        path=str(path),
        format="json",
        token_budget=1000,
    )
    parsed = json.loads(bundle)
    assert parsed["schema_version"] == agentlog.BUNDLE_SCHEMA_VERSION
    assert parsed["event_count"] == 2
    assert '"tag":"decision"' in parsed["context"]
    assert "Bearer abcdefghijklmnop" not in parsed["context"]
    assert "***BEARER_TOKEN***" in parsed["context"]


def test_cli_lists_and_exports_incidents(tmp_path, capsys):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path))
    agentlog.breadcrumb("seen", incident_id="inc_cli")

    assert cli_main(["--store", str(path), "incidents", "list"]) == 0
    listing = capsys.readouterr().out
    assert "inc_cli" in listing

    assert cli_main(["--store", str(path), "incidents", "export", "inc_cli", "--format", "markdown"]) == 0
    exported = capsys.readouterr().out
    assert "agentlog Debug Bundle" in exported
    assert "inc_cli" in exported


def test_stdlib_logging_handler_captures_errors():
    logger = logging.getLogger("agentlog-test-logger")
    logger.handlers.clear()
    logger.propagate = False
    handler = agentlog.install_logging_handler("agentlog-test-logger", level=logging.INFO)

    try:
        raise ValueError("bad token Bearer abcdefghijklmnop")
    except ValueError:
        logger.exception("stdlib failure", extra={"request_id": "req_1"})
    finally:
        logger.removeHandler(handler)

    context = agentlog.get_debug_context(token_budget=1000)
    assert "stdlib failure" in context
    assert "Bearer abcdefghijklmnop" not in context
    assert "***BEARER_TOKEN***" in context


def test_otel_export_includes_genai_attributes():
    agentlog.capture_llm_call(
        "gpt-test",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
        incident_id="inc_otel",
    )

    from agentlog._buffer import get_context
    from agentlog._otel import to_otlp_logs

    entries = [json.loads(line) for line in get_context().splitlines()]
    otlp = to_otlp_logs(entries)
    attrs = otlp["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["attributes"]
    keys = {attr["key"] for attr in attrs}

    assert "gen_ai.request.model" in keys
    assert "gen_ai.usage.input_tokens" in keys
