# Competitive Positioning

agentlog should not compete with LLM observability platforms. It should integrate
with them and own a narrower workflow: producing a compact, redacted, deterministic
debug bundle that a coding agent can use immediately.

## Market Reality

The adjacent market is strong and crowded:

- Langfuse covers LLM tracing, prompt management, evaluation, metrics, and
  dashboards.
- LangSmith covers agent/LLM observability, traces, monitoring, evaluation, and
  failure analysis workflows.
- Phoenix/Arize covers AI observability, tracing, evaluation, OpenInference, and
  OpenTelemetry-based ingestion.
- OpenTelemetry GenAI conventions are becoming the portable telemetry schema for
  model calls, tool calls, retrieval, token usage, and related attributes.

Those products answer broad observability questions:

- What happened?
- How often did it happen?
- Which trace, prompt, model, retriever, or tool was involved?
- How did quality, cost, and latency change?
- What should humans inspect in a dashboard?

agentlog should answer a different question:

> What exact bounded runtime context should I hand to a coding agent so it can
> debug or patch this failure with fewer turns?

## Why Observability Platforms Do Not Fully Solve This

They can store the raw material, but they are not primarily optimized for the
handoff artifact.

### 1. Their unit of value is the trace, not the repair bundle

Traces preserve execution flow. That is useful, but a coding agent usually needs
a smaller and more opinionated artifact:

- exception and stack
- selected locals
- relevant breadcrumbs
- recent tool/model calls
- correlation IDs
- git/environment metadata
- redacted payload summaries
- explicit inclusion/drop reasons

The useful handoff is not "the whole trace." It is the smallest trustworthy
slice of the trace plus nearby runtime facts.

### 2. Their primary consumer is a human dashboard

Dashboards optimize for exploration, filtering, grouping, charts, and drilldown.
Coding agents need stable text/JSON context with a token budget and no UI
interaction requirement.

### 3. They preserve too much by default

Observability tools are designed to keep rich traces for analysis. agentlog
should aggressively compress, redact, and explain what was dropped. That is a
different product bias.

### 4. They are backend/platform workflows

Most teams already have logs, traces, and monitoring. agentlog can run locally
inside a service or test process and produce a handoff bundle without adopting a
new backend.

### 5. Their incentives broaden over time

LLM observability platforms naturally expand into prompt management, evals,
datasets, annotations, monitoring, billing, dashboards, and governance.
agentlog's advantage only exists if it refuses that expansion and stays narrow.

## Advantage

agentlog can be useful because it is:

- **agent-first**: output is designed for coding agents, not dashboards.
- **token-budgeted**: bundle assembly optimizes for context windows.
- **redaction-first**: emitted and persisted events are scrubbed before handoff.
- **runtime-local**: works with stdout, JSONL, CLI, and tests without a backend.
- **deterministic**: explain mode records filters, selected entries, drops, and
  budget usage.
- **observability-compatible**: OTel-style attributes and existing logging
  adapters let teams keep their current stack.

## Possible Moat

The moat is not storage, dashboards, or tracing. Those are already owned by
larger platforms.

The moat can be:

1. **Bundle quality**
   The best token-bounded incident artifact for coding agents. This can improve
   through real-world debugging outcomes.

2. **Redaction trust**
   Strong defaults, policy tests, field-level metadata, and repeated security
   audits. Teams only use handoff bundles if they trust the safety boundary.

3. **Agent outcome data**
   Measure whether bundles reduce turns-to-diagnosis, tokens consumed, and
   failed repair attempts. That feedback loop is more defensible than generic
   tracing.

4. **Context selection heuristics**
   Prioritization logic for crashes, bad decisions, tool failures, retries, and
   flaky workflows can become a specialized library of runtime-to-agent
   compression patterns.

5. **Interoperability**
   Pull from logs/traces/OTel and export to Codex, Claude Code, Cursor, MCP, CI,
   or incident systems. The more handoff targets are supported, the harder it is
   to replace as the glue layer.

## What Not To Build

Do not build:

- a dashboard
- a trace backend
- a generic eval suite
- prompt management
- team analytics as the core product
- autonomous code fixing as the promise

Those weaken differentiation.

## Strategic Position

The durable position is:

> agentlog is the incident handoff layer between runtime telemetry and coding
> agents.

It should sit beside Langfuse, LangSmith, Phoenix, Sentry, Datadog, and OTel.
It should make their telemetry usable by agents when the job is debugging and
patching code.
