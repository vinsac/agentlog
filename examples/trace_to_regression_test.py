"""Generate a regression test scaffold from a replayed incident report.

Input is typically the JSON output produced by:
    examples/incident_replay_workflow.py

Run:
    python3 examples/trace_to_regression_test.py \
      --incident-report ./agentlog_incident_replay_report.json \
      --output ./tests/generated/test_trace_regression.py
"""

import argparse
import json
import os
import re
import time
from typing import Any, Dict


def _slugify(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered)
    return cleaned.strip("_") or "incident"


def _load_incident_report(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_test_source(incident: Dict[str, Any], test_name_prefix: str) -> str:
    error = incident.get("error", {})
    error_type = error.get("type", "UnknownError")
    error_message = error.get("message", "")
    file_hint = error.get("file", "unknown_file")
    line_hint = error.get("line", "?")

    test_name = f"test_{_slugify(test_name_prefix)}_{_slugify(error_type)}"

    return f'''"""Regression test scaffold generated from AgentLog incident replay.

Generated at: {time.time():.3f}
Source report: {incident.get("input", "unknown")}
"""

import pytest


def {test_name}():
    """Protect against replayed incident: {error_type}."""
    # Incident context:
    # - Error: {error_type}: {error_message}
    # - Location hint: {file_hint}:{line_hint}
    #
    # TODO 1: Replace placeholder with real repro steps.
    # TODO 2: Assert expected behavior after fix.
    # TODO 3: Keep this test failing on regression.

    # Example skeleton:
    # result = target_function(...)
    # assert result == expected

    pytest.skip("Replace scaffold with concrete reproduction/assertions")
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate regression test scaffold from incident report")
    parser.add_argument("--incident-report", type=str, required=True, help="Path to incident replay report JSON")
    parser.add_argument(
        "--output",
        type=str,
        default="./tests/generated/test_trace_regression.py",
        help="Output test file path",
    )
    parser.add_argument(
        "--test-name-prefix",
        type=str,
        default="trace_replay",
        help="Prefix for generated test function name",
    )
    args = parser.parse_args()

    report_path = os.path.abspath(args.incident_report)
    incident = _load_incident_report(report_path)

    if not incident.get("ok"):
        raise SystemExit(f"Incident report is not OK: {incident.get('message', 'unknown failure')}")

    output_path = os.path.abspath(args.output)
    source = _build_test_source(incident, args.test_name_prefix)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(source)

    print("=" * 72)
    print("Trace -> Regression Test Scaffold")
    print("=" * 72)
    print(f"Incident report: {report_path}")
    print(f"Generated test: {output_path}")


if __name__ == "__main__":
    main()
