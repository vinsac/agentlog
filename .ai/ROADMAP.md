# AgentLog Product Roadmap

**Status:** Strategic Planning Complete  
**Version:** 2.0 (Consolidated)  
**Date:** 2026-02-14

---

## Table of Contents

1. [Vision Statement](#1-vision-statement)
2. [Why AgentLog Exists](#2-why-agentlog-exists)
3. [Why NOT These Alternatives](#3-why-not-these-alternatives)
4. [Market Dynamics](#4-market-dynamics)
5. [Phase-Based Roadmap](#5-phase-based-roadmap)
6. [Constraints / Guardrails](#6-constraints--guardrails)
7. [Metrics / Success Hypotheses](#7-metrics--success-hypotheses)
8. [Decision Log](#8-decision-log)

---

## 1. Vision Statement

### What AgentLog Solves

AI coding agents (Cursor, Claude Code, Codex, Continue) can read source code but are **blind to runtime reality**. When a Python app crashes at 3am with `ValueError: Confidence 1.5 out of range [0, 1]`, the agent sees a traceback showing *where* code failed, but not:

- What `validate_rating()` actually returned for `confidence=1.5`
- Why the function accepted an invalid value
- The actual runtime data flow that led to the crash

**AgentLog captures the "why"** — automatically, passively, with zero developer effort.

### The Unique Value Proposition

| Capability | Traditional Logging | AgentLog |
|------------|----------------------|----------|
| **Variable values at crash** | ❌ Print debugging required | ✅ Captured automatically |
| **Token-efficient format** | ❌ Verbose human-readable strings | ✅ Compact JSON (`t`, `v`, `n`) |
| **Tool output isolation** | ❌ Mixed with app logs | ✅ Separate streams per call |
| **AI-optimized context export** | ❌ Manual filtering needed | ✅ `get_debug_context(max_tokens=4000)` |
| **Zero instrumentation** | ❌ Code changes required | ✅ `export AGENTLOG=true` |

> **Core Principle:** Machine-readable logs for AI agents, not dashboards for humans.

---

## 2. Why AgentLog Exists

### The Problem: AI Agents Are Runtime Blind

AI coding agents have transformed software development, but they face a critical limitation: **they can read static code but cannot see dynamic execution**. This creates a debugging crisis:

| What Agents CAN Do | What Agents CANNOT Do |
|--------------------|-----------------------|
| Read source files | See variable values during execution |
| Understand code structure | Know which code path actually executed |
| Suggest fixes | Understand why a specific failure occurred |
| Run tests | Correlate test failures with runtime state |

**The Debugging Loop Crisis:**
```
1. Agent sees error: ValueError: Confidence 1.5 out of range
2. Agent guesses at variable values
3. Agent proposes fix based on incorrect assumptions
4. Fix fails
5. Repeat 3-5 more times
6. Finally discovers actual runtime state
```

**With AgentLog:**
```
1. Agent sees error
2. Agent sees actual variable: confidence=1.5, threshold=0.7
3. Agent sees validate_rating() returned success=true for confidence=1.5
4. Bug is obvious: missing upper-bound check
5. Fixed in one turn
```

### Why Now

1. **Agentic Coding Explosion** — Cursor (1M+ users), Claude Code, Codex CLI, Cline, Roo Code are mainstream. These execute code, not just suggest it.

2. **Non-Reproducible Failures** — With agents making dynamic changes, crashes often cannot be reproduced. Runtime state capture becomes essential.

3. **Token Budget Pressure** — Context windows are expensive ($0.03-0.12 per 1K tokens). Compact, AI-optimized log formats directly reduce costs.

4. **Long-Running Agents** — Multi-hour refactoring tasks need state tracking across the entire session, not just per-request traces.

---

## 3. Why NOT These Alternatives

### Why NOT Traditional Logging (structlog, loguru, standard logging)

| Issue | Explanation |
|-------|-------------|
| **Human-centric design** | Built for humans reading logs in Kibana/Datadog, not AI agents consuming context windows |
| **Verbose format** | Long keys (`timestamp`, `level`, `message`) waste tokens; AgentLog uses compact (`t`, `l`, `m`) |
| **No runtime capture** | Still requires manual `logger.info(f"x={x}")` statements |
| **Dashboard dependency** | Value is in browsing dashboards, not in providing debugging context to agents |
| **Manual instrumentation** | Adding log statements defeats the purpose of AI automation |

**Verdict:** Traditional logging is complementary, not competitive. Use it for operational monitoring; use AgentLog for AI debugging.

### Why NOT LLM Tracing Tools (LangSmith, Langfuse, Helicone)

| Issue | Explanation |
|-------|-------------|
| **LLM-call-centric** | Focus on tracing OpenAI/Anthropic API calls, not your application code |
| **No variable capture** | They don't capture Python variable values at crash points |
| **Dashboard-first** | Built for browsing traces, not exporting debugging context |
| **Framework lock-in** | Many require LangChain or specific LLM frameworks |
| **Requires integration** | Need SDK setup, API keys, configuration |

**Verdict:** LangSmith/Langfuse solve "what did the LLM do?"; AgentLog solves "what did my code do?". Complementary, not competitive.

### Why NOT OpenTelemetry

| Issue | Explanation |
|-------|-------------|
| **Heavy and complex** | Requires instrumentation throughout codebase |
| **APM mindset** | Built for distributed tracing across services, not single-process debugging |
| **Verbose by default** | Spans, traces, attributes create overhead |
| **Not AI-optimized** | Output format not designed for LLM context windows |
| **Enterprise complexity** | Solves problems AgentLog users don't have |

**Verdict:** OTEL is for platform teams running microservices. AgentLog is for developers debugging with AI agents.

### Why NOT APM Tools (Datadog, New Relic)

| Issue | Explanation |
|-------|-------------|
| **Enterprise overhead** | Complex setup, agents, configuration |
| **Expensive** | $$$ per host, per month |
| **Dashboard-centric** | Value in visualizations, not in debugging context |
| **Not agent-native** | No concept of "export debugging context to AI" |
| **Overkill for debugging** | Designed for monitoring, not AI-assisted debugging |

**Verdict:** APM tools monitor production health; AgentLog enables AI debugging. Different use cases.

### Why NOT Build Dashboards

**Explicit Decision:** AgentLog will NEVER build dashboards.

| Why NOT | Why This Matters |
|---------|------------------|
| **Scope creep** | Dashboards require frontend, hosting, auth, billing — entire different product |
| **Competitive distraction** | Datadog, Grafana, etc. already exist and are excellent |
| **Core value dilution** | Time spent on dashboards is time not spent on AI debugging primitives |
| **User confusion** | "Is this for me or for AI?" — keep focus sharp |
| **Token-first priority** | Dashboards encourage human-readable formats; we optimize for machines |

**Alternative:** Users pipe JSONL to `jq`, `cat`, or their own visualization tools. We stay focused.

---

## 4. Market Dynamics

### Why AI Agent Debugging is Painful Today

**The Gap:** Existing observability tools solve *LLM call tracing* but fail at *application runtime debugging*.

| Pain Point | Current Reality |
|------------|---------------|
| **Variable blindness** | Agents must guess variable values from tracebacks |
| **Tool output noise** | stdout/stderr mixed; agents can't isolate tool failures |
| **Context window overflow** | Logs are too verbose; agents lose signal in noise |
| **Manual instrumentation** | Adding print statements defeats the purpose |
| **Dashboard-centric design** | Built for humans to browse, not agents to consume |

### Market Trends Making AgentLog Valuable

1. **Agentic Coding Explosion** — Cursor, Claude Code, Codex CLI, Cline, Roo Code adoption is accelerating. These tools execute code, not just suggest it.

2. **Non-Reproducible Failures** — With agents making dynamic changes, crashes often cannot be reproduced. Runtime state capture becomes essential.

3. **Long-Running Agents** — Multi-hour refactoring tasks need state tracking across the entire session, not just per-request traces.

4. **Token Budget Pressure** — Context windows are expensive. Compact, AI-optimized log formats directly reduce costs.

### Competitive Landscape Gap Analysis

| Competitor | Focus | What They Miss |
|------------|-------|----------------|
| **LangSmith** | LangChain trace visualization | No automatic variable capture at crash points |
| **Langfuse** | LLM call tracing + cost tracking | No local runtime state; dashboard-first |
| **OpenTelemetry** | Distributed tracing standard | Requires manual instrumentation; verbose |
| **Datadog/New Relic** | APM metrics and alerts | Enterprise overhead; not AI-agent-centric |
| **Braintrust** | Evaluation + tracing | Requires integration; not for general debugging |

**The Opportunity:** No tool focuses on *making AI agents better debuggers of arbitrary Python code* with zero setup.

---

## 5. Phase-Based Roadmap

### Phase 1: Cement Core Primitives (Weeks 1-3)

**Objective:** Make AgentLog the best-in-class tool for AI agent runtime debugging.

**Implementation Status:** ✅ Complete (146 tests passing)

| Deliverable | Status | Implementation | Value |
|-------------|--------|----------------|-------|
| **Session Correlation** | ✅ Complete | `_session.py`: `start_session(agent, task)`, automatic git capture | Agents track multi-turn work context |
| **Enhanced Failure Capture** | ✅ Complete | `_failure.py`: Locals at crash point, inline secret redaction | Agents see *actual* variable values when code fails |
| **Token Aggregation** | ✅ Complete | `_buffer.py`: `token_summary()` by model | Agents understand cumulative cost per session |
| **Tool Output Isolation** | ✅ Complete | `_capture.py`: Context manager capturing stdout/stderr | Agents debug tool failures without log noise |
| **Git Diff Tracking** | ✅ Complete | `_git.py`: Auto-capture first 50 lines of diff | Agents see what changed between turns |

**Why These Features:**
- These primitives directly address the 5 most common debugging bottlenecks
- Each feature works immediately with `AGENTLOG=true` — no config files, no code changes
- They form the foundation for all future phases

**Why NOT Other Features in Phase 1:**
- ❌ Full stack traces: Too verbose; bottom frame + locals is sufficient
- ❌ Per-file snapshots: Storage/complexity explosion; git diff covers changes
- ❌ Multi-language: Dilutes focus; nail Python first
- ❌ Dashboards: Violates core principle

**Success Metric:** 
- Debug loop reduction: 5-turn average → 1-turn resolution for variable-related bugs
- Token efficiency: 40% fewer tokens than equivalent human-readable logging

---

### Phase 2: Cross-Run Trace Correlation (Weeks 4-6)

**Objective:** Enable agents to learn from previous debugging attempts.

**Implementation Status:** 🔄 In Progress (31 new tests)

| Deliverable | Status | Implementation | Value |
|-------------|--------|----------------|-------|
| **Error Pattern Detection** | ✅ Complete | `_correlation.py`: `hash_error()`, `record_error_pattern()`, `correlate_error()` | Agents recognize recurring failures |
| **Debug Context Persistence** | ✅ Complete | `get_debug_context()` exports JSONL; patterns stored in `.agentlog/error_patterns.json` | Agents reference previous fixes |
| **Session-to-Session Linking** | ✅ Complete | `_session.py`: `parent_session_id` parameter, `get_parent_session_id()` | Track iterative debugging attempts |
| **Workspace State Snapshots** | ✅ Complete | `_workspace.py`: `snapshot_workspace()`, `compare_snapshots()`, file hash tracking | Agents know what files existed when |

---

### Phase 3: Evaluation & Behavior Signals (Weeks 7-9)

**Objective:** Help agents understand their own effectiveness.

**Implementation Status:** ✅ Complete (202 tests passing)

| Deliverable | Status | Implementation | Value |
|-------------|--------|----------------|-------|
| **Decision Logging** | ✅ Complete | `_advanced.py`: `log_decision()` already exists | Track why agents took certain paths |
| **Outcome Tagging** | ✅ Complete | `_outcome.py`: `tag_outcome()`, `tag_session_outcome()`, `get_outcome_stats()` | Build evaluation datasets |
| **Regression Detection** | ✅ Complete | `_regression.py`: `detect_regression()`, `compare_to_baseline()`, `generate_regression_report()` | Catch introduced bugs automatically |
| **Performance Markers** | ✅ Complete | `_advanced.py`: `log_perf()` enhanced with memory/threads/PID | Identify slow operations |

---

### Phase 4: Integrations & Export (Weeks 10-12)

**Objective:** Meet agents where they work — inside their existing tools.

**Implementation Status:** ✅ Complete (251 tests passing)

| Deliverable | Status | Implementation | Value |
|-------------|--------|----------------|-------|
| **MCP Server Protocol** | ✅ Complete | `_mcp.py`: `run_mcp_server()`, 4 tools, 3 resources | Cursor/Claude Desktop native integration |
| **OpenTelemetry Bridge** | ✅ Complete | `_otel.py`: `to_otlp_logs()`, `to_otlp_spans()`, `export_otlp_json()` | Fits into existing observability stacks |
| **Structured Output Templates** | ✅ Complete | `_formats.py`: `get_formatted_context()`, cursor/claude/codex formats | Optimized prompts per agent type |
| **Remote Sync (Optional)** | ✅ Complete | `_remote.py`: `sync_session_to_d1()`, `share_session()` | Cloudflare D1 for team sharing |

---

### Phase 5+ (Longer-Term — Post Validation)

Only pursue after core value is validated with real users:

| Innovation | Trigger Condition | Description |
|------------|---------------------|-------------|
| **Intelligent Context Pruning** | 100+ active users | AI-powered log summarization |
| **Multi-Language Support** | Python adoption plateau | Rust/Go/TypeScript ports |
| **Visual Diff Rendering** | User request volume | Render code changes for non-technical review |
| **Team Analytics** | Enterprise interest | Aggregate debugging patterns |

**Why NOT Pursue These Now:**
- Premature optimization without validated demand
- Each requires significant complexity
- Core value must be proven first

---

## 6. Constraints / Guardrails

### What AgentLog Should NOT Do

**Technical Boundaries:**

| Avoid | Why | Alternative |
|-------|-----|-------------|
| ❌ Full stack traces | Too verbose; agents don't need all frames | Bottom frame + locals only |
| ❌ Per-file workspace snapshots | Storage/complexity explosion | Git diff + selective logging |
| ❌ Multi-language support (yet) | Dilutes focus | Nail Python first |
| ❌ Dashboards or UI | Scope creep; humans have enough tools | JSONL + CLI export only |
| ❌ New dependencies | Breaks zero-dependency promise | Use stdlib only |

**Strategic Boundaries:**

| Avoid | Why | Alternative |
|-------|-----|-------------|
| ❌ Enterprise features | Premature; focus on individual developers | Wait for pull from users |
| ❌ SaaS/cloud-first | Adds ops burden; core value is local | Optional D1 sync only |
| ❌ OTEL replacement | Complementary, not competitive | Bridge/adapter pattern |
| ❌ APM metrics | Datadog exists; don't compete | Focus on AI-agent-specific signals |
| ❌ Complex configuration | Violates "zero friction" principle | Env var only |

**Product Boundaries:**

| Avoid | Why | Alternative |
|-------|-----|-------------|
| ❌ "Monitoring" positioning | Implies passive dashboards | "Debugging" = active problem-solving |
| ❌ Human-readable logs default | Wastes tokens | Machine-first, human-optional |
| ❌ Real-time streaming | Adds complexity without agent value | Batch export on crash |
| ❌ Alerting/notifications | Out of scope | Let users pipe to their own systems |

---

## 7. Metrics / Success Hypotheses

### Primary Metrics (Validate Core Value)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Debug Turn Reduction** | 5 turns (industry avg) | 1-2 turns | User reports / test scenarios |
| **Token Efficiency** | JSON logging (100%) | 60% of baseline | Byte comparison on equivalent context |
| **Setup Friction** | 30 min (typical observability) | <1 min | Time to first debug context export |
| **Tool Output Clarity** | Mixed logs (0% isolation) | 100% isolated | Manual inspection |

### Secondary Metrics (Track Adoption)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **GitHub Stars** | 1,000 in 6 months | GitHub API |
| **PyPI Downloads** | 10,000/month in 6 months | PyPI stats |
| **Active Sessions** | 100/day tracked | Optional telemetry (opt-in) |
| **Agent Integration Requests** | 3 major tools | GitHub issues |

### Signal Quality Hypotheses

1. **Failure Context Quality:** Agents with AgentLog context produce correct fixes 3x faster than those with tracebacks alone.

2. **Token Efficiency:** Compact JSON format enables 40% more debugging context within the same context window.

3. **Tool Isolation Value:** Separated stdout/stderr reduces agent confusion by 50% on tool-related failures.

4. **Zero Friction Adoption:** 90% of developers who try AgentLog continue using it after the first successful debug.

---

## 8. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-14 | Zero dependencies forever | Removes adoption friction; forces quality |
| 2026-02-14 | No dashboards, ever | Keeps focus sharp; humans have alternatives |
| 2026-02-14 | Python-only for Phase 1-4 | Nail one language before diluting |
| 2026-02-14 | Optional D1, never required | Local-first architecture is the moat |
| 2026-02-14 | Compact JSON as native format | Token efficiency is core value |
| 2026-02-14 | Why/Why NOT documented | Prevents scope creep and strategic drift |
| 2026-02-14 | Phase 1 scope limited to 5 primitives | Deliverable in 3 weeks; clear value |

---

## Next Steps

1. **Execute Phase 1** — Session management + enhanced failures
2. **Dogfood** — Use on AgentLog's own development
3. **Seek 3 beta users** — Cursor/Claude Code developers with debugging pain
4. **Iterate** — Gather feedback on context quality
5. **Document** — Create agent-specific integration guides

---

*This roadmap defines AgentLog as the definitive runtime state capture tool for AI coding agents. The path forward is clear: execute Phase 1 ruthlessly, validate with real users, and expand based on proven demand.*
