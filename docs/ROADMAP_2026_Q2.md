# agentlog Roadmap (2026 Q2-Q3)

Status: updated after product-vision and market-positioning review.

## Current Diagnosis

agentlog has useful primitives, but the repo currently exposes too many product
stories at once:

- runtime context capture
- crash analysis
- agent flow visualization
- regression validation
- analytics
- MCP integration
- OpenTelemetry export
- incident replay
- CI templates

The code breadth is not the main problem. The problem is product focus. The v2
roadmap should make `get_debug_context()` the center of gravity and move
everything else into adapters, advanced workflows, or future experiments.

## North Star

agentlog turns live runtime behavior into compact, redactable debug context that
coding agents can actually use.

The roadmap should serve three verbs:

1. Capture
2. Compress
3. Hand off

## Phase 1 - Trust the Bundle

Goal: teams trust the debug bundle enough to hand it to a coding agent.

- [ ] Define a stable incident/event schema.
- [ ] Add first-class redaction policies for secrets, PII, allowlists, and
  denylists.
- [ ] Add field-level inclusion/drop metadata.
- [ ] Make `get_debug_context()` explain budget usage and selection reasons.
- [ ] Add incident/session store abstraction separate from the in-memory buffer.
- [ ] Keep stdlib-only install path.
- [ ] Add compatibility tests for existing v1 API names.

Success metric:

- a production exception can produce a safe, bounded, explainable context bundle
  in under two minutes of setup.

## Phase 2 - Runtime Integrations

Goal: capture enough causal context without turning into an observability
platform.

- [ ] stdlib logging adapter.
- [ ] structlog adapter.
- [ ] OpenTelemetry trace/span correlation.
- [ ] optional OTLP export hooks.
- [ ] LLM call capture helper.
- [ ] tool call capture helper.
- [ ] decision capture helper.
- [ ] framework examples for API services and workers.

Success metric:

- a service can correlate agentlog context with its existing logs/traces without
  adopting a new backend.

## Phase 3 - Handoff Workflow

Goal: make incident context easy to inspect, export, and attach to agent tasks.

- [ ] CLI: list incidents.
- [ ] CLI: inspect incident.
- [ ] CLI: export debug bundle.
- [ ] JSON and Markdown bundle formats.
- [ ] optional MCP resource formatting.
- [ ] docs for Codex, Claude Code, Cursor, and internal agents as consumers of
  exported bundles.

Success metric:

- on-call engineer can attach one bounded artifact to an agent task instead of
  copying logs manually.

## Phase 4 - Regression Signatures

Goal: identify repeated runtime signatures without becoming an eval suite.

- [ ] cluster similar failures by exception, stack, decision type, and compact
  context shape.
- [ ] compare incident signatures across code/prompt releases.
- [ ] generate regression signature summaries.
- [ ] keep validation helpers optional.

Success metric:

- teams can see whether a new incident matches an existing runtime signature.

## De-emphasize

These can remain in the codebase, but should not lead README or product docs:

- `fix_this_crash()` as an autonomous repair promise
- "10X" claims without verified data
- team analytics suite language
- MCP server as core product identity
- full observability platform language
- broad "agent workflow" framework language

## Documentation Cleanup

- [x] Replace README positioning with runtime-context-layer framing.
- [x] Add `docs/PRODUCT_VISION.md`.
- [x] Update market research with critical positioning decision.
- [ ] Rewrite `docs/API_REFERENCE.md` to put core context APIs first.
- [ ] Move advanced features into an "optional workflows" section.
- [ ] Update examples so the default path is capture -> `get_debug_context()` ->
  handoff.

## Release Criteria for v2

v2 should not ship because there are more features. It should ship when the
debug bundle is:

- safe by default
- deterministic
- token-budgeted
- redaction-aware
- correlated with existing observability
- easy to export to a coding agent
