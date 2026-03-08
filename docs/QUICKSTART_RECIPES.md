# AgentLog Runtime Quickstarts (Generic First)

This guide is intentionally **runtime-first** and **editor-agnostic**.

Use it in services, workers, CI pipelines, and incident-response workflows.
Editor-specific instructions (Cursor, Claude Code, Codex, Windsurf) are optional overlays.

## Shared zero-config bootstrap (recommended)

Set these once in your shell or project env:

```bash
export AGENTLOG=true
export AGENTLOG_FILE=.agentlog/sessions.jsonl
export AGENTLOG_BUFFER_SIZE=2000
```

Why this helps:

- `AGENTLOG=true` enables logging and failure capture
- `AGENTLOG_FILE` stores replayable JSONL traces
- `AGENTLOG_BUFFER_SIZE` tunes context budget for long tasks

---

## 1) Generic API service quickstart

```python
import agentlog

agentlog.enable()

def handle_request(request_id: str) -> dict:
    agentlog.start_session("api-service", f"request {request_id}")
    try:
        # ... your business logic ...
        result = {"ok": True}
        agentlog.tag_outcome("success", 1.0)
        return result
    except Exception as exc:
        agentlog.log_error("request failed", exc, request_id=request_id)
        fix_code, explanation = agentlog.fix_this_crash()
        agentlog.log("fix_suggestion", preview=fix_code[:120], explanation=explanation)
        agentlog.tag_outcome("failure", 1.0, str(exc))
        raise
    finally:
        agentlog.end_session()
```

## 2) Generic worker/pipeline quickstart

```python
import agentlog

agentlog.enable()
agentlog.start_session("worker", "nightly-pipeline")

try:
    # ... process batch ...
    agentlog.log("batch_complete", items_processed=1000)
    agentlog.tag_outcome("success", 0.95)
except Exception as exc:
    agentlog.log_error("pipeline failure", exc)
    replay_ready_context = agentlog.get_debug_context(max_tokens=3000)
    print(replay_ready_context)
    agentlog.tag_outcome("failure", 1.0, str(exc))
    raise
finally:
    agentlog.end_session()
```

## 3) Generic CI quickstart

```python
import agentlog

agentlog.enable()
agentlog.start_session("ci", "pull-request-validation")

# ... run checks/tests ...
result = agentlog.analyze_and_validate_refactoring()
if result["regression_validation"] and not result["regression_validation"]["safe_to_merge"]:
    raise SystemExit("AgentLog regression gate failed")

agentlog.tag_outcome("success", 1.0, "ci checks passed")
agentlog.end_session()
```

---

## 4) Editor overlays (optional)

### Cursor quickstart

Add this to `.cursorrules`:

```text
When a command/test fails:
1) call agentlog.analyze_crash()
2) call agentlog.fix_this_crash() and propose smallest safe patch
3) run validate_refactoring against baseline before merge
```

Minimal bootstrap in your app entrypoint:

```python
import agentlog

agentlog.enable()
agentlog.start_session("cursor", "feature-task")
```

Debug loop command:

```python
analysis = agentlog.analyze_crash()
fix_code, explanation = agentlog.fix_this_crash()
combined = agentlog.analyze_and_validate_refactoring()
```

---

### Claude Code quickstart

Add this to project instructions:

```text
Use AgentLog for failures and regressions:
- analyze_crash for root cause context
- fix_this_crash for first candidate patch
- analyze_and_validate_refactoring before final answer
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
- use fix_this_crash() for first patch proposal
- check quick_validate() before task completion
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

AgentLog supports both:

- **Development:** local crash context, fix suggestions, refactor validation.
- **Production:** structured error/session logs, incident replay from JSONL, and outcome/regression analytics.

Typical deployment pattern:

1. Keep `AGENTLOG=true` enabled in target service.
2. Write JSONL to durable storage via `AGENTLOG_FILE` or `to_file(...)`.
3. Run replay + reporting workflows from collected traces.

See:

- `docs/BENCHMARK_HARNESS.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `docs/INCIDENT_REPLAY_WORKFLOW.md`
- `docs/CI_TEMPLATES.md`
