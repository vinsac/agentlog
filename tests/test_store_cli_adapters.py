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
    assert parsed["selected_count"] == 2
    assert parsed["dropped_count"] == 0
    assert '"tag":"decision"' in parsed["context"]
    assert "Bearer abcdefghijklmnop" not in parsed["context"]
    assert "***BEARER_TOKEN***" in parsed["context"]


def test_incident_store_preserves_redacted_descriptor_shape(tmp_path):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path))

    agentlog.capture_tool_call(
        "charge",
        input={"api_key": "sk-" + "a" * 48, "amount": 10},
        incident_id="inc_secret",
    )

    entry = agentlog.load_incident_entries("inc_secret", path=str(path))[0]

    assert entry["args"]["api_key"]["t"] == "str"
    assert entry["args"]["api_key"]["v"] == "***REDACTED_FIELD***"
    assert entry["input"]["v"]["api_key"] == "***REDACTED_FIELD***"


def test_incident_store_rotates_when_max_bytes_exceeded(tmp_path):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path), max_bytes=260)

    agentlog.breadcrumb("first", incident_id="inc_rotate", payload="x" * 120)
    agentlog.breadcrumb("second", incident_id="inc_rotate", payload="y" * 120)

    assert path.exists()
    assert path.with_name(path.name + ".1").exists()
    assert agentlog.get_incident_store_max_bytes() == 260


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


def test_cli_exports_latest_and_scope_filtered_bundle(tmp_path, capsys):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path))
    agentlog.breadcrumb("drop", incident_id="inc_old", request_id="req_old")
    agentlog.breadcrumb("keep", incident_id="inc_new", request_id="req_keep")
    agentlog.breadcrumb("drop same incident", incident_id="inc_new", request_id="req_drop")
    capsys.readouterr()

    assert cli_main(
        [
            "--store",
            str(path),
            "incidents",
            "export",
            "--latest",
            "--format",
            "json",
            "--scope",
            "request_id=req_keep",
        ]
    ) == 0
    exported = json.loads(capsys.readouterr().out)

    assert exported["incident_id"] == "inc_new"
    assert exported["event_count"] == 2
    assert exported["filtered_count"] == 1
    assert "keep" in exported["context"]
    assert "drop same incident" not in exported["context"]


def test_cli_exports_session_without_incident(tmp_path, capsys):
    path = tmp_path / "incidents.jsonl"
    agentlog.configure_incident_store(str(path))
    session_id = agentlog.start_session("worker", "session export")
    agentlog.breadcrumb("session only")
    capsys.readouterr()

    assert cli_main(
        [
            "--store",
            str(path),
            "incidents",
            "export",
            "--session-id",
            session_id,
            "--format",
            "json",
        ]
    ) == 0
    exported = json.loads(capsys.readouterr().out)

    assert exported["session_id"] == session_id
    assert exported["event_count"] >= 1
    assert "session only" in exported["context"]


def test_cli_missing_incident_returns_nonzero(tmp_path, capsys):
    path = tmp_path / "incidents.jsonl"

    assert cli_main(["--store", str(path), "incidents", "export", "missing"]) == 1

    assert "no stored entries" in capsys.readouterr().err


def test_cli_export_creates_output_parent_directory(tmp_path):
    path = tmp_path / "incidents.jsonl"
    output = tmp_path / "nested" / "bundle.md"
    agentlog.configure_incident_store(str(path))
    agentlog.breadcrumb("write me", incident_id="inc_out")

    assert cli_main(
        [
            "--store",
            str(path),
            "incidents",
            "export",
            "inc_out",
            "--format",
            "markdown",
            "--out",
            str(output),
        ]
    ) == 0

    assert output.exists()
    assert "write me" in output.read_text()


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
    assert "gen_ai.operation.name" in keys


def test_otel_tool_export_includes_genai_tool_attributes():
    call_id = agentlog.capture_tool_call("lookup_customer", input={"id": "cust_1"})

    from agentlog._buffer import get_context
    from agentlog._otel import to_otlp_logs

    entries = [json.loads(line) for line in get_context().splitlines()]
    otlp = to_otlp_logs(entries)
    attrs = otlp["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]["attributes"]
    values = {attr["key"]: attr["value"] for attr in attrs}

    assert values["gen_ai.operation.name"]["stringValue"] == "execute_tool"
    assert values["gen_ai.tool.name"]["stringValue"] == "lookup_customer"
    assert values["gen_ai.tool.call.id"]["stringValue"] == call_id
