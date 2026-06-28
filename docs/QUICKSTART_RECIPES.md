# agentlog Runtime Quickstarts

This guide is runtime-first and editor-agnostic.

Use it in services, workers, CI pipelines, and incident-response workflows to
capture compact debug context for coding agents.
Editor-specific instructions (Cursor, Claude Code, Codex, Windsurf) are optional overlays.

## Shared zero-config bootstrap (recommended)

Set these once in your shell or project env:

```bash
export AGENTLOG=true
export AGENTLOG_INCIDENT_STORE=.agentlog/incidents.jsonl
export AGENTLOG_INCIDENT_STORE_MAX_BYTES=52428800
export AGENTLOG_BUFFER_SIZE=2000
```

Why this helps:

- `AGENTLOG=true` enables logging and failure capture
- `AGENTLOG_INCIDENT_STORE` stores durable incident events for later export
- `AGENTLOG_INCIDENT_STORE_MAX_BYTES` rotates the JSONL store before it grows without bound
- `AGENTLOG_BUFFER_SIZE` tunes context budget for long tasks

---

## 1) Generic API service quickstart

```python
import agentlog

agentlog.enable()

def handle_request(request_id: str) -> dict:
    incident_id = f"inc_{request_id}"
    agentlog.start_session("api-service", f"request {request_id}")
    try:
        # ... your business logic ...
        result = {"ok": True}
        agentlog.tag_outcome("success", 1.0)
        return result
    except Exception as exc:
        agentlog.log_error("request failed", exc, request_id=request_id, incident_id=incident_id)
        context = agentlog.get_debug_context(max_tokens=4000, incident_id=incident_id)
        attach_to_incident_or_agent_task(context)
        agentlog.tag_outcome("failure", 1.0, str(exc))
        raise
    finally:
        agentlog.end_session()
```

Durable handoff after the process exits:

```bash
agentlog incidents export inc_req_123 --tokens 4000 --format markdown
agentlog incidents export --latest --scope request_id=req_123 --format json
```

## 2) Bad decision reconstruction

```python
import agentlog

def route_payment(request_id: str, features: dict) -> str:
    candidates = [
        {"route": "approve", "score": features["approval_score"]},
        {"route": "manual_review", "score": features["risk_score"]},
    ]
    chosen = "manual_review"

    agentlog.capture_decision(
        "payment_route",
        chosen,
        candidates=candidates,
        threshold=0.7,
        reason="risk score exceeded review threshold",
        request_id=request_id,
        incident_id=f"inc_{request_id}",
    )

    return chosen
```

When the route is wrong, export:

```bash
agentlog incidents export inc_req_123 --scope request_id=req_123 --format markdown
```

## 3) Generic worker/pipeline quickstart

```python
import agentlog

agentlog.enable()
agentlog.start_session("worker", "nightly-pipeline")

try:
    # ... process batch ...
    agentlog.log("batch_complete", items_processed=1000)
    agentlog.tag_outcome("success", 0.95)
except Exception as exc:
    agentlog.capture_tool_call("nightly_loader", error=exc, incident_id="inc_nightly_pipeline")
    agentlog.log_error("pipeline failure", exc, incident_id="inc_nightly_pipeline")
    replay_ready_context = agentlog.get_debug_context(
        max_tokens=3000,
        incident_id="inc_nightly_pipeline",
    )
    print(replay_ready_context)
    agentlog.tag_outcome("failure", 1.0, str(exc))
    raise
finally:
    agentlog.end_session()
```

## 4) Generic CI quickstart

```python
import agentlog

agentlog.enable()
agentlog.start_session("ci", "pull-request-validation")

# ... run checks/tests ...
context = agentlog.get_debug_context(max_tokens=4000)
write_ci_artifact("agentlog-debug-context.txt", context)

agentlog.tag_outcome("success", 1.0, "ci checks passed")
agentlog.end_session()
```

---

## 5) Editor overlays (optional)

### Cursor quickstart

Add this to `.cursorrules`:

```text
When a command/test fails:
1) call agentlog.get_debug_context(max_tokens=4000)
2) use the context as the primary failure bundle
3) use analysis/fix helpers only as optional supporting evidence
```

Minimal bootstrap in your app entrypoint:

```python
import agentlog

agentlog.enable()
agentlog.start_session("cursor", "feature-task")
```

Debug loop command:

```python
context = agentlog.get_debug_context(max_tokens=4000)
analysis = agentlog.analyze_crash()  # optional
```

---

### Claude Code quickstart

Add this to project instructions:

```text
Use AgentLog for failures and regressions:
- get_debug_context for the failure handoff bundle
- analyze_crash as optional supporting detail
- quick_validate as an optional regression signal
```

Session pattern:

```python
import agentlog

agentlog.enable()
sid = agentlog.start_session("claude-code", "task")
# ...work...
agentlog.end_session()
```

Production-safe sink setup:

```python
import agentlog
agentlog.to_file("/var/log/agentlog/sessions.jsonl")
```

---

### Codex quickstart

For multi-process workflows, pass parent session automatically:

```python
import os
import subprocess
import agentlog

agentlog.enable()
agentlog.start_session("codex", "parent-workflow")
parent = agentlog.get_session_id()

env = os.environ.copy()
env["AGENTLOG_PARENT_SESSION"] = parent
subprocess.run(["python3", "child_task.py"], env=env, check=False)

flow = agentlog.get_cascade_summary()
print(flow)
```

Validation gate:

```python
result = agentlog.quick_validate()
if result in {"REVIEW", "UNSAFE"}:
    raise RuntimeError("Refactor blocked by AgentLog validation")
```

---

### Windsurf quickstart

Add this to `.windsurfrules`:

```text
If AGENTLOG=true is present:
- inspect get_debug_context() on failures
- use analysis helpers only after reading the debug context
- check quick_validate() only when a baseline exists
```

Operational session pattern:

```python
import agentlog

agentlog.enable()
agentlog.start_session("windsurf", "runtime-debug")
# ...work...
agentlog.tag_outcome("success", 0.95, "validated behavior")
agentlog.end_session()
```

---

## Development + production usage model

agentlog supports both:

- **Development:** local crash context and agent handoff bundles.
- **Production:** structured error/session context, incident replay from JSONL,
  and optional outcome/regression signals.

Typical deployment pattern:

1. Keep `AGENTLOG=true` enabled in target service.
2. Write JSONL to durable storage via `AGENTLOG_FILE` or `to_file(...)`.
3. Run replay + reporting workflows from collected traces.

See:

- `docs/BENCHMARK_HARNESS.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `docs/INCIDENT_REPLAY_WORKFLOW.md`
- `docs/CI_TEMPLATES.md`
