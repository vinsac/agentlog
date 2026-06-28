# agentlog Market Research (Q2 2026)

## Research Question

What should agentlog become in a market already crowded with AI observability,
LLM tracing, eval, prompt-management, and APM products?

## Sources Reviewed

Selected public docs and positioning pages:

- LangSmith Observability: https://docs.langchain.com/langsmith/observability
- Langfuse Observability: https://langfuse.com/docs/observability/overview
- Arize Phoenix docs: https://arize.com/docs/phoenix
- OpenTelemetry GenAI semantic conventions:
  https://opentelemetry.io/docs/specs/semconv/gen-ai/
- Datadog LLM Observability: https://docs.datadoghq.com/llm_observability/
- Sentry AI Monitoring: https://docs.sentry.io/product/insights/ai/
- Braintrust evaluations: https://www.braintrust.dev/docs/evaluate
- Helicone docs: https://docs.helicone.ai/

## Market Pattern

The category is converging around:

- tracing for LLM calls, tools, chains, agents, and MCP servers
- model cost, latency, token, and quality monitoring
- prompt iteration and prompt/version management
- online and offline evals
- datasets, experiments, feedback, and regression workflows
- dashboards and production monitoring
- OpenTelemetry compatibility

The market already has strong tools for "what happened?", "which trace?",
"how often?", "how slow?", "what did the model do?", and "did quality regress?"

## Positioning Risk

The old repo story competed too broadly:

- "runtime observability for AI agents"
- "one-shot crash fixer"
- "multi-agent flow visualizer"
- "regression validator"
- "team analytics"
- MCP server positioning
- broad production workflow claims

That makes agentlog sound like a small version of LangSmith, Langfuse, Phoenix,
Sentry, Datadog, or Braintrust. This is a weak fight. Those products already own
dashboards, trace stores, eval suites, team workflows, and production monitoring.

## Positioning Decision

agentlog should be positioned as a runtime context layer for coding agents.

Use this sentence:

> agentlog turns live runtime behavior into compact, redactable debug context
> that coding agents can actually use.

This creates a narrow wedge:

- not a log platform
- not a tracing backend
- not a dashboard
- not a prompt manager
- not an eval suite
- not an autonomous repair system

The product is capture, compress, and hand off.

## Differentiator

Most tools optimize for humans viewing traces and dashboards. agentlog should
optimize for the artifact handed to a coding agent during debugging:

- selected locals
- error and stack
- causal breadcrumbs
- tool and LLM call summaries
- decision metadata
- git and environment hints
- correlation IDs
- redaction metadata
- token-budget accounting

The output should be deterministic, compact, and inspectable.

See `docs/COMPETITIVE_POSITIONING.md` for the sharper platform comparison,
why adjacent observability products do not fully solve agent handoff, and what
moat agentlog can realistically build.

## ICP

Best initial ICP:

- Python backend teams using coding agents for debugging and patching
- teams with internal AI tools, microservices, and high debugging cost
- services with tool-heavy, RAG-heavy, async, or decision-heavy flows
- platform teams standardizing "handoff to agent" workflows

Avoid generic SaaS and broad "AI observability" language until the handoff
workflow is proven.

## Product Implications

Prioritize:

- stable event schema
- redaction and field policy engine
- incident-scoped storage
- deterministic `get_debug_context()`
- token budget explanations
- stdlib logging and OpenTelemetry correlation
- optional LLM/tool/decision helpers
- CLI export of incident bundles

De-emphasize in top-level positioning:

- autonomous fix generation
- team analytics
- MCP as a product category
- broad agent workflow orchestration
- full regression/eval suite claims
- dashboard-oriented language

## Success Metrics

The product should be evaluated by:

- time to first diagnosis
- agent turns to valid patch
- tokens consumed during debugging
- rate of "cannot reproduce" incidents
- handoff time from on-call engineer to coding agent

If a feature does not move one of these metrics, it is probably outside the core.
