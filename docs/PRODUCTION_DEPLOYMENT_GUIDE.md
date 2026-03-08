# AgentLog Production Deployment Guide

This guide is for running AgentLog safely and reliably in production.

## 1) Deployment goals

In production, AgentLog should provide:

- structured incident traces for replay and postmortems
- low overhead, predictable logging volume
- safe handling of sensitive data
- operational hooks for alerting and regression gates

## 2) Minimum production bootstrap

Use env-driven bootstrap for zero-config startup:

```bash
export AGENTLOG=true
export AGENTLOG_LEVEL=error
export AGENTLOG_FILE=/var/log/agentlog/sessions.jsonl
export AGENTLOG_BUFFER_SIZE=2000
```

Why this baseline:

- `AGENTLOG=true` enables runtime capture
- `AGENTLOG_LEVEL=error` minimizes noise and cost
- `AGENTLOG_FILE` creates replayable JSONL traces
- `AGENTLOG_BUFFER_SIZE` controls in-memory context budget

## 3) Throughput control and sampling strategy

AgentLog does not enforce centralized sampling for you; choose one of these patterns:

1. **Severity-based control (recommended start):** keep `AGENTLOG_LEVEL=error`.
2. **Route-level/session-level sampling:** start sessions only for high-value paths.
3. **Dual-mode deployment:** keep full trace in staging, error-focused trace in prod.

Example session sampling wrapper:

```python
import os
import random
import agentlog

SAMPLE_RATE = float(os.getenv("AGENTLOG_SESSION_SAMPLE_RATE", "0.1"))

def maybe_start_session(agent: str, task: str) -> bool:
    if random.random() <= SAMPLE_RATE:
        agentlog.start_session(agent, task)
        return True
    return False
```

## 4) Sensitive data and redaction

AgentLog includes inline redaction patterns for common secrets (API keys, bearer tokens, password-like fields).

Still treat this as **defense-in-depth**, not absolute protection:

- avoid logging raw request bodies with credentials/PII
- avoid calling `log_vars()` on large untrusted payloads by default
- sanitize user identifiers where possible (hash or tokenized IDs)

Recommended policy:

1. Classify fields into allowed/forbidden logging categories.
2. Add an application-level scrubber before `log(...)` calls.
3. Restrict file permissions on log path (`chmod 640`, owner/group service account).
4. Apply retention and deletion policy aligned to compliance requirements.

## 5) File sink operations and rotation

When using `AGENTLOG_FILE`, configure rotation externally.

### Option A: logrotate

Use template:

- `templates/ops/agentlog.logrotate.conf`

Apply by copying into `/etc/logrotate.d/agentlog`.

### Option B: stdout-only + collector

In containerized environments, prefer stdout and route via log agent (Fluent Bit, Vector, etc.) into centralized storage.

## 6) Retention policy (recommended defaults)

Start with:

- hot retention: 7-14 days searchable
- warm archive: 30-90 days compressed storage
- incident-tagged traces: keep longer based on policy

Always align to legal/security policy of your organization.

## 7) Alert wiring

Alert on these leading signals:

- spikes in `tag=error` entries
- new error pattern hashes (regression surface)
- rising `failure` outcomes from `tag_outcome`
- sustained increase in `time_to_fix` or fix iterations from benchmark reports

Operational path:

1. Collect JSONL traces.
2. Run incident replay (`examples/incident_replay_workflow.py`).
3. Generate/refresh regression tests (`examples/trace_to_regression_test.py`).
4. Enforce CI gate (`templates/ci/agentlog_benchmark_gate.yml`).

## 8) Production incident runbook (minimal)

1. Confirm `AGENTLOG_FILE` is active and writable.
2. Pull latest trace window.
3. Run replay workflow to extract suggested fix.
4. Validate against baseline before merge/deploy.
5. Backfill postmortem with trace + outcome tags.

## 9) Cross references

- `docs/QUICKSTART_RECIPES.md`
- `docs/INCIDENT_REPLAY_WORKFLOW.md`
- `docs/TRACE_TO_REGRESSION_TEST.md`
- `docs/CI_TEMPLATES.md`
