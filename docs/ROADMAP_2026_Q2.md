# AgentLog Roadmap (2026 Q2-Q3)

Status: drafted from codebase audit + market scan, implementation started.

## 1) What is already built

AgentLog already has strong breadth in core package capabilities:

- Core logging + context budget: `log*`, ringbuffer, `get_debug_context`
- Session + failure capture: session IDs, crash locals capture, correlation
- "Clear winner" features: `fix_this_crash`, `visualize_agent_flow`, `validate_refactoring`
- Integrations: MCP server, OpenTelemetry bridge, optional Cloudflare D1 sync
- Strong test suite footprint across modules in `tests/`

## 2) Market needs and gaps (what to prioritize now)

Based on current AI-agent tooling trends and developer feedback:

1. Teams still rely heavily on existing observability stacks (Grafana/Prometheus/Sentry), so AgentLog should win by being the easiest runtime-debug context layer for agents.
2. Frequent AI coding failures are still context-related (hallucinations/incomplete understanding), so product value should focus on reducing debugging loops and proving that reduction.
3. Competitive AI observability products differentiate through eval + trace-to-test workflows; AgentLog currently has primitives, but not a streamlined "proof of value" workflow for adoption.
4. Buyer motion is increasingly platform-level (SRE + AI + backend teams), so editor-bound positioning narrows adoption compared to runtime-level positioning.

Primary product gap today is not feature count; it is adoption confidence and measurable outcomes.

## 3) Roadmap

### Phase A — Trust & adoption (next 2-4 weeks)

- [x] Add zero-config env bootstrap consistency (env-driven parent sessions, file sink, buffer tuning)
- [x] Add tests for env bootstrap behavior and startup defaults
- [x] Publish reproducible benchmark harness for "iterations to fix" and "time to fix"
- [x] Add runtime-first quickstarts with optional editor overlays (Cursor, Claude Code, Codex, Windsurf)

Success metric:
- first-time setup to useful debug context in < 2 minutes

### Phase B — Prove 10x claim (4-8 weeks)

- [x] Add automated metrics collector example + report generator for beta teams
- [x] Add incident replay workflow (JSONL -> analysis -> suggested fix -> validation)
- [x] Add 3+ public case studies using consistent measurement template

Success metric:
- >= 80% one-shot fix rate on tracked benchmark scenarios

### Phase C — Workflow depth (8-12 weeks)

- [x] Tighten integration between crash analysis and regression validation
- [x] Improve "trace to regression test" workflow docs/examples
- [x] Add CI templates for session outcome tagging + baseline comparison

Success metric:
- teams running AgentLog checks in CI before merge

## 4) Implementation started in this cycle

Completed:

- [x] Implemented env fallback for `AGENTLOG_PARENT_SESSION` in `start_session()` when `parent_session_id` is not explicitly passed.
- [x] Added tests covering explicit parent precedence and env fallback.
- [x] Added startup env bootstrap for `AGENTLOG_FILE` to auto-enable JSONL sink when enabled.
- [x] Added startup env bootstrap for `AGENTLOG_BUFFER_SIZE` with safe integer parsing.
- [x] Added bootstrap tests for file sink, valid buffer size, and invalid/non-positive buffer values.
- [x] Added reproducible benchmark harness script for fix iterations and time-to-fix.
- [x] Added benchmark harness documentation and usage guide.
- [x] Added runtime-first quickstart guide with optional overlays for Cursor, Claude Code, Codex, and Windsurf.
- [x] Added beta metrics collector + Markdown report generator for benchmark outputs.
- [x] Added incident replay workflow script and companion documentation.
- [x] Added 3 public case studies aligned to the success metrics template.
- [x] Added integrated helper to combine crash analysis with regression validation.
- [x] Added trace-to-regression-test scaffold generator and workflow docs.
- [x] Added CI workflow templates for benchmark gating and incident replay artifacts.
- [x] Added production deployment guide (sampling, retention, redaction, rotation, alert wiring).

Files changed in this implementation cycle:

- `src/agentlog/__init__.py`
- `src/agentlog/_fixer.py`
- `src/agentlog/_session.py`
- `examples/benchmark_fix_iterations.py`
- `examples/beta_metrics_collector.py`
- `examples/incident_replay_workflow.py`
- `examples/trace_to_regression_test.py`
- `docs/BENCHMARK_HARNESS.md`
- `docs/QUICKSTART_RECIPES.md`
- `docs/INCIDENT_REPLAY_WORKFLOW.md`
- `docs/CASE_STUDIES_PUBLIC.md`
- `docs/TRACE_TO_REGRESSION_TEST.md`
- `docs/CI_TEMPLATES.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `tests/test_bootstrap.py`
- `tests/test_fixer.py`
- `tests/test_session.py`
- `templates/ci/agentlog_benchmark_gate.yml`
- `templates/ci/agentlog_replay_gate.yml`
- `templates/ops/agentlog.logrotate.conf`

## 5) Immediate next implementation tasks

1. Gather real beta-team production metrics and replace representative case-study numbers with verified values.
2. Add CI wiring in live repositories using templates from `templates/ci/`.
3. Publish benchmark + replay outputs as part of release notes.

---

This roadmap intentionally prioritizes measurable outcomes and onboarding reliability over adding new surface-area features.
