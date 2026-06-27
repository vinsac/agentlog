# agentlog v2 Architecture

agentlog v2 is organized around three product layers:

1. Capture runtime facts.
2. Compress them into token-budgeted context.
3. Hand off a safe bundle to a coding agent or human.

## Canonical Modules

### `agentlog._capture`

Canonical v2 capture primitives:

- `breadcrumb(event, **ctx)`
- `start_operation(name, **ctx)`
- `end_operation(status="success", **ctx)`
- `operation(name, **ctx)`
- `capture_decision(decision_type, chosen, candidates=None, **ctx)`
- `capture_tool_call(name, input=None, output=None, error=None, **ctx)`
- `capture_llm_call(model, input=None, output=None, usage=None, error=None, **ctx)`

This module emits normalized events. It also promotes common correlation fields
such as `incident_id`, `request_id`, and `correlation_id` to top-level fields so
context assembly can filter deterministically.

### `agentlog._redaction`

Redaction policy engine:

- default secret field denylist
- default PII field denylist
- default token/key regexes
- configurable deny fields
- configurable allowlist
- configurable custom regex patterns

All descriptor-producing APIs route through this layer.

### `agentlog._context`

Debug-context assembly:

- filters by `session_id`
- filters by `incident_id`
- filters by arbitrary scope fields
- selects entries deterministically by priority, recency, and token budget
- emits optional redaction and budget metadata
- emits optional drop/selection explanations

Storage does not own formatting decisions. `_context` does.

### `agentlog._buffer`

In-memory event storage facade:

- ringbuffer storage
- raw JSONL context export
- v2 `get_debug_context(...)` delegation into `_context`

The ringbuffer is intentionally simple. More durable stores should implement the
same "list of event dicts" handoff shape and reuse `_context`.

### `agentlog._store`

Durable incident storage and bundle export:

- append-only JSONL incident store
- incident listing by `incident_id`
- stored-entry loading by `incident_id` or `session_id`
- versioned JSON/Markdown/text debug bundle export

This layer persists sanitized emitted entries and delegates context assembly to
`_context`, so stored bundles and live bundles follow the same selection rules.

### `agentlog.cli`

Command-line handoff workflow:

- `agentlog incidents list`
- `agentlog incidents inspect <incident_id>`
- `agentlog incidents export <incident_id>`

The CLI reads the JSONL store and exports bounded artifacts for coding agents.

## Compatibility Modules

Older modules remain available:

- `_api`: legacy `log`, `log_error`, `log_vars`, `log_http`
- `_agent`: legacy LLM/tool call helpers and context managers
- `_advanced`: legacy decision/flow/diff/query/perf helpers
- `_fixer`, `_validate`, `_flow`, `_analytics`: optional workflows

These modules should call the v2 redaction and context layers rather than
creating new safety or bundle-assembly logic.

## Public API Direction

Prefer new code like this:

```python
import agentlog

agentlog.breadcrumb("request_started", request_id=request_id)
agentlog.capture_decision(
    "route_payment",
    "manual_review",
    candidates=["approve", "manual_review", "decline"],
    score=0.62,
    threshold=0.7,
    incident_id=incident_id,
)

context = agentlog.get_debug_context(
    token_budget=4000,
    incident_id=incident_id,
    include_metadata=True,
    explain=True,
)
```

Legacy APIs can stay as thin aliases or adapters, but new features should land
in the canonical modules above.
