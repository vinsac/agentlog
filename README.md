# agentlog

**Compact, redactable runtime context for coding agents.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

agentlog turns live runtime behavior into compact, redactable debug context that
coding agents can actually use.

It is not a logging platform, tracing backend, dashboard, prompt manager, or eval
suite. Use OpenTelemetry, Sentry, Datadog, Langfuse, Phoenix, LangSmith, or your
existing log stack for those jobs. agentlog sits beside them and answers one
narrow question:

> What exact execution context should I hand to a coding agent so it can debug
> this failure with fewer guesses?

## Why This Exists

Tracebacks show where code failed. Production logs show what happened, but often
as thousands of lines of noisy text. LLM tracing tools show prompts, responses,
costs, latency, and tool spans.

Coding agents need a smaller artifact: the relevant exception, stack, locals,
breadcrumbs, decisions, tool calls, LLM calls, correlation IDs, git metadata, and
payload summaries, already redacted and sized for a context window.

That artifact is `get_debug_context()`.

## Why Not Just Give the Runtime Context to the Agent?

The runtime has the facts, but it usually has them in the wrong shape for an
agent: too much raw log volume, too little causal context, unsafe payloads,
missing incident boundaries, and no token budget.

agentlog is not a new source of truth. It is a context compiler:

> Runtimes know everything; coding agents need the smallest safe subset.
> agentlog is the adapter between those two worlds.

Use agentlog when you want runtime facts turned into a handoff artifact that is:

- selected for debugging rather than exhaustive replay
- compressed into compact value descriptors
- redacted before it leaves the process
- scoped by incident, session, request, or correlation ID
- deterministic and explainable under a token budget

## Quick Start

```bash
pip install agentlog
export AGENTLOG=true
export AGENTLOG_INCIDENT_STORE=.agentlog/incidents.jsonl
export AGENTLOG_INCIDENT_STORE_MAX_BYTES=52428800
```

```python
import agentlog

agentlog.start_session("checkout-api", "debug failed payment authorization")

try:
    result = authorize_payment(payload)
except Exception as error:
    agentlog.log_error("authorization failed", error, request_id=request_id)
    debug_context = agentlog.get_debug_context(max_tokens=4000)
    raise
```

Example output:

```text
# agentlog debug context (session: sess_10a491b4)
# git: main@2c53442 dirty
# tokens: 230 total (gpt-4: 150in/80out)

{"event_type":"error","error_type":"ValueError","error_message":"Confidence 1.5 out of valid range [0, 1]",
 "context":{"request_id":{"type":"str","value":"req_91d2"}}}
{"event_type":"variables","variables":{"confidence":{"type":"float","value":1.5},"threshold":{"type":"float","value":0.7}}}
{"event_type":"tool","tool":"validate_rating","arguments":{"confidence":{"type":"float","value":1.5}},"success":true}
```

Give that bundle to Codex, Claude Code, Cursor, an internal repair agent, or a
human reviewer. The value is not autonomous fixing. The value is deterministic
handoff context.

For incidents that need to survive process exit, use the durable JSONL store:

```python
import agentlog

agentlog.configure_incident_store(".agentlog/incidents.jsonl", max_bytes=52_428_800)
agentlog.capture_decision("route_payment", "manual_review", incident_id="inc_123")
agentlog.log_error("authorization failed", error, incident_id="inc_123")
```

Then export a bounded handoff bundle:

```bash
agentlog incidents list
agentlog incidents export inc_123 --tokens 4000 --format markdown
agentlog incidents export --latest --scope request_id=req_91d2 --format json
```

## Core Use Cases

- **Crash to fix context** - capture exception type, message, stack, selected
  locals, correlation IDs, recent breadcrumbs, tool/LLM calls, git metadata, and
  redacted payload summaries.
- **Bad decision reconstruction** - capture candidates, chosen option, score,
  threshold, reason fields, upstream input summary, downstream outcome, and
  related events.
- **Flaky workflow replay context** - preserve ordered breadcrumbs, retries,
  external dependency behavior, feature flags, environment hints, and recent
  tool calls without dumping raw logs.
- **Human-to-agent handoff** - export a bounded incident bundle instead of
  asking an agent to scrape unstructured logs.
- **Agent regression triage** - group similar failures and surface common runtime
  signatures after code or prompt changes.

## API Shape

The public surface is intentionally small:

| Function | Purpose |
| --- | --- |
| `breadcrumb(event, **ctx)` / `log(message, **ctx)` | Record a structured breadcrumb. |
| `log_error(message, error, **ctx)` | Record an exception with traceback and context. |
| `log_vars(*args, **vars)` | Capture compact value descriptors for runtime state. |
| `capture_decision(decision_type, chosen, candidates=None, **ctx)` | Record why code selected one path over another. |
| `capture_tool_call(name, input=None, output=None, error=None, **ctx)` | Capture tool/function behavior. |
| `capture_llm_call(model, input=None, output=None, usage=None, error=None, **ctx)` | Capture model interaction summaries. |
| `start_operation(name, **ctx)` / `end_operation(status="success", **ctx)` | Capture bounded operations. |
| `start_session(name, task=None)` / `end_session()` | Correlate events into a handoff scope. |
| `get_debug_context(token_budget=4000, incident_id=None, scope=None)` | Export token-budgeted, failure-prioritized context. |
| `configure_redaction(...)` | Configure deny fields, allowlists, PII fields, and custom regexes. |
| `configure_incident_store(path)` | Persist emitted events for later incident export. |
| `export_debug_bundle(incident_id=..., format="json")` | Export a versioned stored bundle. |
| `install_logging_handler(...)` / `structlog_processor` | Mirror existing logs into agentlog context. |

Additional modules for OpenTelemetry export, MCP formatting, file sinks,
regression checks, and analytics are optional adapters around this core.

## Design Principles

- **Agent-first, not dashboard-first** - every captured event should help an
  agent or engineer understand and patch a failure.
- **Token-budgeted by default** - large payloads are summarized; low-cardinality
  fields and causal breadcrumbs are preserved.
- **Redaction is mandatory** - secrets and sensitive fields must be scrubbed
  before context leaves the process.
- **OTel-compatible, not OTel-replacing** - agentlog should correlate with
  traces and logs, not become the trace store.
- **Deterministic context assembly** - teams should be able to explain why a
  bundle included or dropped each piece of context.

## What agentlog Is Not

agentlog should not be positioned as:

- a full observability platform
- a metrics or trace backend
- a log storage product
- a vendor-specific APM clone
- a prompt management system
- a broad agent workflow framework
- a promise that crashes are fixed automatically

Those claims are already served by larger tools and weaken the reason this
library should exist.

## When It Helps Most

- Python backend teams using coding agents for debugging and patching
- AI-heavy services with tool calls, RAG/agent flows, routing decisions, retries,
  and flaky failures
- Internal platform teams building deterministic "handoff to agent" workflows
- Services that already have logs/traces but lack compact, model-ready incident
  context

## Agent-Readable Versus Compact Descriptors

agentlog stores runtime values internally as compact descriptors instead of
dumping full objects:

```json
{"t":"str","v":"Python"}
{"t":"list","n":100,"it":"dict","preview":[{"id":1},{"id":2}]}
{"t":"ndarray","sh":"(768,)","dt":"float32","range":[0.0,1.0]}
```

But `get_debug_context()` and `agentlog incidents export` default to readable
agent-facing descriptors:

```json
{"type":"str","value":"Python"}
{"type":"list","length":100,"item_type":"dict","preview":[{"id":1},{"id":2}]}
{"type":"ndarray","shape":"(768,)","dtype":"float32","range":[0.0,1.0]}
```

Use `schema_style="compact"` or `--schema-style compact` only when you need the
legacy abbreviated JSONL shape.

## Project Direction

The v2 product should focus on three layers:

1. **Capture** - collect structured runtime facts at the moment they matter.
2. **Compress** - convert noisy runtime state into concise, token-aware context.
3. **Hand off** - export safe bundles for agents, humans, or existing platforms.

Everything else belongs in adapters or optional modules.

See:

- `docs/PRODUCT_VISION.md`
- `docs/HOW_TO_USE_AGENTLOG.md`
- `docs/ARCHITECTURE.md`
- `docs/COMPETITIVE_POSITIONING.md`
- `docs/MARKET_RESEARCH_2026_Q2.md`
- `docs/QUICKSTART_RECIPES.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `docs/API_REFERENCE.md`

## License

MIT
