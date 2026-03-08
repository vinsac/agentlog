# AgentLog Market Research (Q2 2026): Positioning Decision

## Question

Should AgentLog be positioned as editor-specific (Cursor/Claude Code/Codex/Windsurf) or as a generic runtime layer?

## Internet scan (selected sources)

1. LangSmith Observability docs
   - https://docs.langchain.com/langsmith/observability
   - Signals: tracing, monitoring, automations, feedback loops, RAG tracing.
2. OpenTelemetry GenAI semantic conventions
   - https://opentelemetry.io/docs/specs/semconv/gen-ai/
   - Signals: standard traces/events/metrics for model + agent spans and MCP.
3. Sentry AI Monitoring docs
   - https://docs.sentry.io/product/insights/ai/
   - Signals: production monitoring for agent workflows, tool calls, model interactions, MCP servers.
4. Arize Phoenix docs
   - https://arize.com/docs/phoenix
   - Signals: tracing + evaluations + prompt engineering + datasets/experiments + span replay.
5. Braintrust evaluation docs
   - https://www.braintrust.dev/docs/evaluate
   - Signals: offline eval + online production scoring + continuous feedback loop.
6. Langfuse observability docs
   - https://langfuse.com/docs/observability/overview
   - Signals: prompt/response/tool traces, token/cost/latency visibility, non-deterministic debugging.
7. Datadog LLM observability docs
   - https://docs.datadoghq.com/llm_observability/
   - Signals: end-to-end traces, cost/perf monitoring, quality/safety checks, anomaly detection.
8. Helicone guides
   - https://docs.helicone.ai/guides/overview
   - Signals: replay sessions, CI integrations, environment tracking, evaluation workflows.

## Market pattern summary

Across vendors, the common buyer and usage pattern is:

- runtime-first instrumentation (not editor plugins first)
- production observability + cost/performance visibility
- evaluation and regression loops connected to traces
- CI/CD and incident workflows
- standards/interoperability pressure (OpenTelemetry GenAI)

## User needs implied by market

1. Work everywhere: APIs, workers, async jobs, CI, prod services.
2. Low-friction adoption: env-vars, drop-in bootstrap, no heavy setup.
3. Incident lifecycle support: capture -> replay -> suggested fix -> regression gate.
4. Proof of value: measurable reduction in iterations/time-to-fix.
5. Optional tool overlays: editor-specific instructions are useful, but secondary.

## Positioning decision

**Decision: AgentLog should be positioned as a generic runtime observability layer with optional editor overlays.**

Why:

- Expands ICP beyond editor users to platform/SRE/backend teams.
- Aligns with market buying behavior and competitive framing.
- Better supports production monitoring and incident response narratives.
- Keeps editor integrations as accelerators, not product identity.

## Implementation changes completed

1. README repositioned to generic runtime + production/development scope.
2. Quickstarts refactored to runtime-first, with editor sections marked optional.
3. Usage examples now lead with generic runtime patterns.
4. Roadmap wording updated to runtime-first quickstarts and market rationale.

## Next recommendation

Add one consolidated "production deployment guide" (sampling, retention, redaction, PII handling, sink rotation, alert wiring) to strengthen enterprise adoption.
