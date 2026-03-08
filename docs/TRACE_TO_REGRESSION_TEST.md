# Trace-to-Regression-Test Workflow

This workflow turns an incident trace into a persistent regression test.

## Why

When an issue is fixed once, the team should never pay for it again.

## Step 1: Replay incident and generate fix context

```bash
python3 examples/incident_replay_workflow.py \
  --input .agentlog/sessions.jsonl \
  --output ./agentlog_incident_replay_report.json
```

## Step 2: Generate regression test scaffold from replay report

```bash
python3 examples/trace_to_regression_test.py \
  --incident-report ./agentlog_incident_replay_report.json \
  --output ./tests/generated/test_trace_regression.py
```

## Step 3: Replace scaffold with real reproduction

In generated test file:

1. Add real invocation inputs from the incident.
2. Add assertions for corrected behavior.
3. Remove skip marker.

## Step 4: Gate with validation

After implementing the fix and regression test:

```python
import agentlog

combined = agentlog.analyze_and_validate_refactoring()
print(combined["recommendation"])
```

## Artifacts

- Incident report JSON
- Regression test file in `tests/generated/`
- Validation output for merge gate
