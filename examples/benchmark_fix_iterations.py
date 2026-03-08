"""Reproducible benchmark harness for fix iterations and time-to-fix.

This benchmark exercises the one-shot crash workflow across deterministic
error scenarios and records:
- first-try success rate
- average iterations to fix
- average time to generate a fix

Run:
    python3 examples/benchmark_fix_iterations.py --repeat 3
"""

import argparse
import io
import json
import os
import sys
import time
from contextlib import redirect_stderr
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import agentlog
from agentlog._failure import _capture_failure


BASELINE_ITERATIONS_WITHOUT_AGENTLOG = 5
MANUAL_FALLBACK_ITERATIONS = 5


@dataclass
class Scenario:
    name: str
    description: str
    trigger: Callable[[], None]
    validate_fix: Callable[[str, str], bool]


def _trigger_valueerror_range() -> None:
    confidence = 1.5
    threshold = 0.7
    if confidence > threshold:
        raise ValueError(f"{confidence} out of valid range [0, 1]")


def _trigger_keyerror_missing_key() -> None:
    payload = {"name": "alice"}
    _ = payload["user_id"]


def _trigger_attributeerror_none() -> None:
    user = None
    _ = user.name


def _validate_valueerror_fix(fix_code: str, explanation: str) -> bool:
    text = f"{fix_code}\n{explanation}".lower()
    return "between" in text and "confidence" in text and "0.0" in text and "1.0" in text


def _validate_keyerror_fix(fix_code: str, explanation: str) -> bool:
    text = f"{fix_code}\n{explanation}".lower()
    return "user_id" in text and ".get(" in text and "missing key" in text


def _validate_attributeerror_fix(fix_code: str, explanation: str) -> bool:
    text = f"{fix_code}\n{explanation}".lower()
    return "is not none" in text and ".name" in text


def _build_scenarios() -> List[Scenario]:
    return [
        Scenario(
            name="valueerror_range_violation",
            description="ValueError range violation (confidence out of [0,1])",
            trigger=_trigger_valueerror_range,
            validate_fix=_validate_valueerror_fix,
        ),
        Scenario(
            name="keyerror_missing_key",
            description="KeyError for missing dictionary key",
            trigger=_trigger_keyerror_missing_key,
            validate_fix=_validate_keyerror_fix,
        ),
        Scenario(
            name="attributeerror_none_access",
            description="AttributeError on NoneType attribute access",
            trigger=_trigger_attributeerror_none,
            validate_fix=_validate_attributeerror_fix,
        ),
    ]


def _capture_error_for_scenario(scenario: Scenario) -> Exception:
    try:
        scenario.trigger()
    except Exception as exc:  # noqa: BLE001 - benchmark intentionally captures all scenario errors
        # _capture_failure calls the original excepthook; silence stderr noise for benchmark output.
        with redirect_stderr(io.StringIO()):
            _capture_failure(type(exc), exc, exc.__traceback__)
        return exc
    raise RuntimeError(f"Scenario '{scenario.name}' did not raise an exception")


def _run_single_scenario(scenario: Scenario, run_index: int) -> Dict[str, Any]:
    session_id = agentlog.start_session("benchmark", f"{scenario.name} run {run_index}")

    started = time.perf_counter()
    captured_error = _capture_error_for_scenario(scenario)
    fix_code, explanation = agentlog.fix_this_crash()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    first_try_success = scenario.validate_fix(fix_code, explanation)
    iterations_to_fix = 1 if first_try_success else MANUAL_FALLBACK_ITERATIONS

    agentlog.end_session()

    return {
        "scenario": scenario.name,
        "description": scenario.description,
        "run_index": run_index,
        "session_id": session_id,
        "error_type": type(captured_error).__name__,
        "error_message": str(captured_error),
        "first_try_success": first_try_success,
        "iterations_to_fix": iterations_to_fix,
        "time_to_fix_ms": elapsed_ms,
        "fix_preview": fix_code[:240],
        "explanation": explanation,
    }


def _aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    first_try_count = sum(1 for r in results if r["first_try_success"])
    avg_iterations = round(sum(r["iterations_to_fix"] for r in results) / max(total, 1), 2)
    avg_time_ms = round(sum(r["time_to_fix_ms"] for r in results) / max(total, 1), 2)
    improvement_vs_baseline = round(
        BASELINE_ITERATIONS_WITHOUT_AGENTLOG / avg_iterations,
        2,
    ) if avg_iterations > 0 else None

    return {
        "total_runs": total,
        "first_try_success_count": first_try_count,
        "first_try_success_rate": round(first_try_count / max(total, 1), 4),
        "average_iterations_to_fix": avg_iterations,
        "average_time_to_fix_ms": avg_time_ms,
        "assumed_baseline_iterations_without_agentlog": BASELINE_ITERATIONS_WITHOUT_AGENTLOG,
        "improvement_vs_baseline_iterations_x": improvement_vs_baseline,
    }


def run_benchmark(repeat: int) -> Dict[str, Any]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")

    scenarios = _build_scenarios()
    results: List[Dict[str, Any]] = []

    for run_index in range(1, repeat + 1):
        for scenario in scenarios:
            results.append(_run_single_scenario(scenario, run_index))

    summary = _aggregate(results)
    return {
        "meta": {
            "benchmark": "agentlog_fix_iterations",
            "generated_at_unix": time.time(),
            "repeat": repeat,
            "scenario_count": len(scenarios),
            "notes": [
                "Scenarios are deterministic and synthetic for reproducibility.",
                "If first-try validation fails, iterations are set to manual fallback value.",
            ],
        },
        "summary": summary,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark fix iterations and time-to-fix")
    parser.add_argument("--repeat", type=int, default=1, help="How many times to run each scenario")
    parser.add_argument(
        "--output",
        type=str,
        default="./agentlog_benchmark_report.json",
        help="Path to JSON report output",
    )
    args = parser.parse_args()

    agentlog.enable()
    agentlog.configure(level="error")
    agentlog.install_failure_hook()

    report = run_benchmark(args.repeat)

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=" * 72)
    print("AgentLog Benchmark Complete")
    print("=" * 72)
    print(f"Report: {output_path}")
    print(f"Total runs: {report['summary']['total_runs']}")
    print(f"First-try success rate: {report['summary']['first_try_success_rate'] * 100:.1f}%")
    print(f"Average iterations to fix: {report['summary']['average_iterations_to_fix']}")
    print(f"Average time to fix: {report['summary']['average_time_to_fix_ms']} ms")
    print(
        "Improvement vs baseline (iterations): "
        f"{report['summary']['improvement_vs_baseline_iterations_x']}x"
    )


if __name__ == "__main__":
    main()
