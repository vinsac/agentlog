"""Incident replay workflow: JSONL -> analysis -> suggested fix -> validation.

This script replays persisted AgentLog JSONL traces, extracts the latest error,
produces a suggested fix, and optionally runs regression validation.

Run:
    python3 examples/incident_replay_workflow.py --input .agentlog/sessions.jsonl
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import agentlog
from agentlog._fixer import (
    _detect_attributeerror_pattern,
    _detect_indexerror_pattern,
    _detect_keyerror_pattern,
    _detect_typeerror_pattern,
    _detect_valueerror_pattern,
    _generate_fix,
)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    entries.append(parsed)
            except json.JSONDecodeError:
                continue
    return entries


def _latest_error_entry(entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for entry in reversed(entries):
        if entry.get("tag") == "error":
            return entry
    return None


def _detect_fix(error_entry: Dict[str, Any]) -> Tuple[str, str, Optional[Dict[str, Any]]]:
    error_info = error_entry.get("error", {})
    error_type = error_info.get("type", "")
    error_msg = error_info.get("msg", "")
    locals_dict = error_entry.get("locals", {})

    detection = None
    if error_type == "ValueError":
        detection = _detect_valueerror_pattern(error_msg, locals_dict)
    elif error_type == "KeyError":
        detection = _detect_keyerror_pattern(error_msg, locals_dict)
    elif error_type == "AttributeError":
        detection = _detect_attributeerror_pattern(error_msg, locals_dict)
    elif error_type == "IndexError":
        detection = _detect_indexerror_pattern(error_msg, locals_dict)
    elif error_type == "TypeError":
        detection = _detect_typeerror_pattern(error_msg, locals_dict)

    if not detection:
        return (
            "# No known pattern detected from replayed incident.",
            f"Manual review required for {error_type}: {error_msg}",
            None,
        )

    fix_code, explanation = _generate_fix(detection, error_entry)
    full_fix = (
        f"# Replay fix for {error_type}: {error_msg[:80]}\n"
        f"# Location: {error_entry.get('file', 'unknown')}:{error_entry.get('line', '?')}\n"
        f"# Root cause: {explanation}\n"
        f"{fix_code}"
    )
    return full_fix, explanation, detection


def _validate_if_requested(
    baseline_session: Optional[str],
    new_session: Optional[str],
    strict_mode: bool,
) -> Optional[Dict[str, Any]]:
    if not baseline_session or not new_session:
        return None
    return agentlog.validate_refactoring(
        baseline_session=baseline_session,
        new_session=new_session,
        strict_mode=strict_mode,
    )


def replay_incident(
    input_path: str,
    baseline_session: Optional[str] = None,
    new_session: Optional[str] = None,
    strict_mode: bool = False,
) -> Dict[str, Any]:
    entries = _read_jsonl(input_path)
    if not entries:
        return {
            "ok": False,
            "message": "No JSON entries found in input file.",
            "input": os.path.abspath(input_path),
        }

    error_entry = _latest_error_entry(entries)
    if not error_entry:
        return {
            "ok": False,
            "message": "No error entries found in JSONL.",
            "input": os.path.abspath(input_path),
            "total_entries": len(entries),
        }

    fix_code, explanation, detection = _detect_fix(error_entry)
    validation = _validate_if_requested(baseline_session, new_session, strict_mode)

    return {
        "ok": True,
        "input": os.path.abspath(input_path),
        "total_entries": len(entries),
        "error": {
            "type": error_entry.get("error", {}).get("type"),
            "message": error_entry.get("error", {}).get("msg"),
            "file": error_entry.get("file"),
            "line": error_entry.get("line"),
            "function": error_entry.get("fn"),
        },
        "detection": detection,
        "suggested_fix": {
            "code": fix_code,
            "explanation": explanation,
        },
        "validation": validation,
        "generated_at_unix": time.time(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay AgentLog incidents from JSONL and generate fix guidance")
    parser.add_argument(
        "--input",
        type=str,
        default=os.getenv("AGENTLOG_FILE", "").strip(),
        help="Path to AgentLog JSONL session file (defaults to AGENTLOG_FILE)",
    )
    parser.add_argument("--baseline-session", type=str, default="", help="Baseline session ID for validation")
    parser.add_argument("--new-session", type=str, default="", help="New session ID for validation")
    parser.add_argument("--strict", action="store_true", help="Use strict regression validation")
    parser.add_argument(
        "--output",
        type=str,
        default="./agentlog_incident_replay_report.json",
        help="Output path for replay report JSON",
    )
    args = parser.parse_args()

    if not args.input:
        raise SystemExit("Missing --input and AGENTLOG_FILE is not set")

    report = replay_incident(
        input_path=args.input,
        baseline_session=args.baseline_session or None,
        new_session=args.new_session or None,
        strict_mode=args.strict,
    )

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 72)
    print("AgentLog Incident Replay")
    print("=" * 72)
    print(f"Input: {os.path.abspath(args.input)}")
    print(f"Output: {output_path}")
    print(f"Status: {'OK' if report.get('ok') else 'FAILED'}")

    if report.get("ok"):
        print(f"Error: {report['error']['type']} - {report['error']['message']}")
        print("Suggested fix preview:")
        print(report["suggested_fix"]["code"][:220])
        if report.get("validation"):
            print(f"Validation decision: {report['validation'].get('decision')}")
    else:
        print(f"Reason: {report.get('message')}")


if __name__ == "__main__":
    main()
