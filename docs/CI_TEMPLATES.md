# CI Templates for Session Outcome Tagging + Baseline Comparison

This doc includes copy-ready templates to operationalize AgentLog checks in CI.

## Template 1: Benchmark + beta metrics gate

Use `templates/ci/agentlog_benchmark_gate.yml` as a starter.

What it does:

1. Runs benchmark harness
2. Aggregates report with beta metrics collector
3. Fails pipeline if thresholds are not met

## Template 2: Incident replay + regression scaffold

Use `templates/ci/agentlog_replay_gate.yml` to:

1. Replay latest JSONL incident
2. Generate regression test scaffold
3. Upload artifacts for review

## Outcome tagging recommendation

In your CI test driver, tag outcomes so trend analysis is consistent:

```python
import agentlog

agentlog.start_session("ci", "pull-request-validation")
# run tests ...
agentlog.tag_outcome("success", 1.0, "all checks passed")
agentlog.end_session()
```

## Baseline comparison recommendation

Set/update baseline after a green main branch run:

```python
import agentlog

agentlog.set_baseline("stable", agentlog.get_session_id())
```

Then on PR runs:

```python
result = agentlog.analyze_and_validate_refactoring()
if result["regression_validation"] and not result["regression_validation"]["safe_to_merge"]:
    raise SystemExit("AgentLog regression gate failed")
```
