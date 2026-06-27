# agentlog Product Vision

## Decision

agentlog v2 should be the runtime context layer for agent-assisted debugging.

The product should own one job: when software breaks, behaves strangely, or makes
a bad decision, agentlog captures the smallest useful slice of runtime context
and turns it into safe, structured, model-ready debugging input.

Use this sentence everywhere:

> agentlog turns live runtime behavior into compact, redactable debug context
> that coding agents can actually use.

## Why This Is the Right Wedge

The AI observability market is already crowded. LangSmith, Langfuse, Phoenix,
Datadog, Sentry, and OpenTelemetry GenAI conventions are all converging on
traces, spans, cost, latency, evals, prompt iteration, model behavior, and
workflow monitoring.

agentlog should not compete head-on with those systems. It should sit on top of
normal observability and make the relevant runtime facts usable by a coding
agent.

Most tools answer:

- what happened?
- how often?
- how slow?
- which trace?
- what did the model/tool call do?

agentlog should answer:

- what exact context should I give the coding agent so it can fix this with
  minimal iteration?

That is a real product distinction.

## ICP

The best early users are narrow:

- Python backend teams using Codex, Claude Code, Cursor, or similar coding agents
- companies with internal AI tools and microservices
- AI-heavy services with tool calls, RAG/agent flows, routing decisions, retries,
  and flaky failures
- internal platform teams that want "handoff to agent" to be deterministic

Avoid generic SaaS positioning until this workflow is proven.

## Product Boundaries

The product has three layers:

1. Capture - collect structured runtime facts at the moment they matter.
2. Compress - convert noisy runtime state into concise, token-aware summaries.
3. Hand off - export context for agents, humans, or other platforms.

That is the product.

Everything else should be optional:

- OpenTelemetry adapters
- stdlib logging and structlog adapters
- LLM/tool-call schema helpers
- CLI inspection and export
- MCP formatting
- regression clustering
- framework integrations

## Core Use Cases

### Crash to fix context

A service throws an exception. agentlog captures:

- exception type and message
- stack
- selected locals
- correlation/session/request IDs
- recent breadcrumbs
- recent tool and LLM calls
- git SHA and environment metadata
- redacted payload summary

Then `get_debug_context()` returns a token-budgeted bundle an agent can use
immediately.

### Bad decision reconstruction

An agent, router, classifier, or rule engine made the wrong call. agentlog
captures:

- decision type
- candidate options
- threshold and score
- reason fields
- upstream input summary
- downstream outcome
- related events

This is not only "the request failed." It is "why the system chose X."

### Flaky workflow replay context

A multi-step workflow fails intermittently. agentlog captures:

- ordered breadcrumbs
- tool call summaries
- retries
- external dependency behavior
- feature flags
- environment diffs

The output is a compact narrative an agent can inspect without reading raw logs.

### Human-to-agent handoff

An engineer says: "look at this failure and patch it." agentlog generates a
bounded incident bundle instead of forcing the agent to scrape thousands of
lines of logs.

### Agent regression triage

After a code or prompt change, failures cluster. agentlog groups similar
failures and surfaces the common runtime signature.

## API Vision

Keep the surface small and opinionated.

Core primitives:

- `log(event, **ctx)`
- `log_error(message, error, **ctx)`
- `log_vars(*args, **vars)`
- `breadcrumb(event, **ctx)`
- `start_operation(name, **ctx)`
- `end_operation(status="success", **ctx)`
- `capture_decision(decision_type, chosen, candidates=None, **ctx)`
- `capture_tool_call(name, input=None, output=None, error=None, **ctx)`
- `capture_llm_call(model, input=None, output=None, usage=None, error=None, **ctx)`
- `get_debug_context(token_budget=4000, incident_id=None, scope=None)`

The current v1 API has similar primitives under names like `log_decision`,
`log_tool_call`, and `log_llm_call`. v2 should converge naming around capture,
compression, and handoff without expanding the conceptual surface.

## Design Principles

### Agent-first, not dashboard-first

Every event shape should answer: "would this help an agent fix the problem?"

### Token-budgeted by default

The library should optimize for context windows:

- summarize large payloads
- keep low-cardinality fields intact
- truncate safely
- preserve causal chain

### Redaction is mandatory

First-class redaction is not optional:

- secret scrubbing
- PII redaction
- configurable field policies
- allowlist and denylist controls

### OTel-compatible, not OTel-replacing

Support:

- trace/span correlation
- export to existing logging/tracing stacks
- incident context layered on top

### Deterministic context assembly

`get_debug_context()` should be stable and explainable:

- why each event was included
- why each field was dropped
- how token budget was spent

That matters if teams are going to trust it.

## What To De-emphasize

The repo should hide or move behind advanced docs anything that makes the
product look like:

- autonomous crash fixing
- team analytics suite
- full observability platform
- MCP platform
- broad agent workflow framework
- generic eval suite

Those may remain useful modules, but they should not be the core story.

## Success Metrics

If v2 works, users should be able to show:

- lower time to first diagnosis
- fewer agent turns to produce a valid fix
- fewer tokens consumed during debugging
- fewer "cannot reproduce" incidents
- faster handoff from on-call engineer to coding agent

If these are not measurable, the product is drifting.

## Build Order

### Phase 1

- stable event schema
- redaction engine
- incident store abstraction
- `get_debug_context()`
- stdlib logging adapter
- OTel correlation support

### Phase 2

- tool call and LLM call capture helpers
- decision event helpers
- CLI to inspect/export incident bundles

### Phase 3

- clustering similar failures
- regression signatures
- framework integrations

## One-sentence Vision

agentlog v2 is the missing layer between application runtime and coding agents:
it captures, redacts, compresses, and exports the exact execution context needed
for agent-assisted debugging.
