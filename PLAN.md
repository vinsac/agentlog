# agentlog — Project Plan

> **Runtime observability for AI coding agents.**

**Author:** Vinay Sachdeva
**Date:** February 14, 2026
**Status:** Planning
**License:** MIT
**Repo:** github.com/vinsac/agentlog

---

## 1. Vision

AI coding agents (Cursor, Windsurf, Copilot, Claude Code, Codex) are **blind to runtime state**. They can read source code but cannot see what variables contain, which code paths executed, what shape data has, or why something failed at runtime.

Existing tools don't solve this:

| Tool | What it does | Gap |
|------|-------------|-----|
| **structlog / loguru** | Structured production logging | Designed for ops dashboards, not AI context windows |
| **icecream** | Pretty-prints variables | Human-readable, not machine-parseable |
| **Langfuse / LangSmith** | Traces LLM API calls | Only instruments AI calls, not your app code |
| **OpenTelemetry** | Distributed tracing | Heavy, complex, designed for APM platforms |
| **Gasoline MCP** | Streams browser state | Browser-only, not backend |

**agentlog** fills the gap: structured, token-efficient logging that works in both development AND production, designed specifically for AI agents to consume.

### Key Differentiators

1. **AI-First Output** — Compact JSON with short keys (`t`, `v`, `n`, `k`) that minimize token usage in LLM context windows
2. **Dev + Production** — Not just a dev tool. Production-grade with log levels, structured output, and JSONL sinks
3. **Zero Dependencies** — Python stdlib only. Single file. Works anywhere Python 3.9+ runs
4. **Zero Cost When Off** — All calls are no-ops when disabled. No performance impact in production
5. **Token-Aware** — Built-in ringbuffer with token-budgeted export. Solves context window overflow
6. **Framework Agnostic** — Works with Django, FastAPI, Flask, scripts, notebooks, anything

---

## 2. Name & Identity

- **Package name:** `agentlog`
- **PyPI:** `pip install agentlog`
- **npm:** `npm install agentlog` (TypeScript version)
- **Import:** `from agentlog import log, trace, span, check`
- **Tagline:** *"Runtime observability for AI coding agents."*
- **Env var:** `AGENTLOG=true` (enable), `AGENTLOG_LEVEL=info` (level filter)

### Rename from devlog

The `devlog` name implied "development-only logging." `agentlog` communicates:
- It's for **agents** (AI coding agents, not just developers)
- It works in **production** (not just dev)
- It's a **log** system (familiar concept)

---

## 3. Architecture

### 3.1 Core Design

```
┌─────────────────────────────────────────────────┐
│                   agentlog                       │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Public   │  │  Value   │  │   Output     │  │
│  │  API      │→ │  Descr.  │→ │   Engine     │  │
│  │          │  │  Engine   │  │  (sinks)     │  │
│  └──────────┘  └──────────┘  └──────┬───────┘  │
│                                      │          │
│  ┌──────────┐  ┌──────────┐  ┌──────▼───────┐  │
│  │  Trace   │  │  Ring    │  │  Formatters  │  │
│  │  Context │  │  Buffer  │  │  (json,text) │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

### 3.2 Module Structure

```
agentlog/
├── __init__.py          # Public API re-exports
├── _core.py             # Configuration, enable/disable, env detection
├── _describe.py         # Value descriptor engine (the AI-first secret sauce)
├── _emit.py             # Output engine: format, route to sinks
├── _api.py              # Public functions: log, vars, state, error, check, http
├── _trace.py            # Trace/span context propagation
├── _advanced.py         # decision, flow, diff, query, perf
├── _buffer.py           # Token-aware ringbuffer, context export, summary
├── _sink.py             # JSONL file sink, future: remote sinks
├── _decorator.py        # @log_func decorator
└── py.typed             # PEP 561 marker for type checkers
```

### 3.3 Output Format

Every log entry is a single JSON line prefixed with a tag for grep:

```
[AGENTLOG:info] {"seq":1,"ts":1739512200.5,"at":"main.py:42 create_skill","msg":"Processing","ctx":{...}}
[AGENTLOG:error] {"seq":2,"ts":1739512200.8,"at":"main.py:55 create_skill","msg":"Failed","err":"ValueError",...}
```

**Tag prefix change:** `[DEVLOG:*]` → `[AGENTLOG:*]`

### 3.4 Log Levels (New for Production)

```python
# Development: everything enabled
AGENTLOG=true

# Production: only errors and checks
AGENTLOG=true
AGENTLOG_LEVEL=error

# Levels (inclusive): debug < info < warn < error
# debug: vars, state, flow, diff, perf
# info: log, http, query, func, decision, span, trace
# warn: check (failed)
# error: error
```

---

## 4. API Design

### 4.1 Core API (from devlog v0.2)

```python
from agentlog import log, log_vars, log_state, log_error, log_check, log_http, log_func

# Message with context
log("Processing request", user_id=uid, skill_name=name)

# Variable inspection
log_vars(confidence, embedding_vector, result_dict)

# State snapshots
log_state("before_update", profile.__dict__)

# Error with traceback
log_error("Normalization failed", error=e, input_name=name)

# Runtime assertions (log, don't crash)
log_check(len(results) > 0, "Expected results", query=q)

# HTTP request/response
log_http("POST", "/api/skills", 201, 45.2, body=payload)

# Function decorator
@log_func
async def create_skill(name: str) -> dict: ...
```

### 4.2 Distributed Tracing (from devlog v0.3)

```python
from agentlog import trace, trace_end, get_trace_id, span

tid = trace()  # generate trace ID
resp = httpx.post(url, headers={"X-Trace-Id": tid})

# Downstream service
trace(request.headers.get("X-Trace-Id"))

with span("normalize_skill", input=raw_name):
    result = normalize(raw_name)
```

### 4.3 Advanced Observability (from devlog v0.3)

```python
from agentlog import log_decision, log_flow, log_diff, log_query, log_perf

# Decision logging
log_decision("Merge with existing?", confidence >= 0.9, reason="above threshold")

# Data flow tracing
log_flow("skill_pipeline", "raw_input", raw_name)
log_flow("skill_pipeline", "normalized", normalized)

# State diffing
log_diff("profile", old_state, new_state)

# Query logging
log_query("SELECT", "skills", 12.3, rows=42)

# Performance snapshots
log_perf("after_batch", batch_size=100)
```

### 4.4 Context Budget (from devlog v0.3)

```python
from agentlog import get_context, summary, set_buffer_size

# Export recent logs within token budget
context = get_context(max_tokens=4000, tags=["error", "check"])

# Compact session summary
s = summary()

# Configure buffer
set_buffer_size(1000)
```

### 4.5 File Sink

```python
from agentlog import to_file, close_file

to_file(".agentlog/session.jsonl")
# ... run code ...
close_file()
```

### 4.6 Configuration

```python
from agentlog import enable, disable, configure

enable()   # programmatic enable
disable()  # programmatic disable

configure(
    level="info",           # minimum level
    output="stdout",        # stdout, stderr, or file path
    format="json",          # json or text
    tag_prefix="AGENTLOG",  # customize prefix
)
```

### 4.7 Naming Convention

Rename from `devlog_*` to cleaner names:

| Old (devlog) | New (agentlog) | Reason |
|-------------|---------------|--------|
| `devlog()` | `log()` | Shorter, cleaner |
| `devlog_vars()` | `log_vars()` | Consistent prefix |
| `devlog_state()` | `log_state()` | Consistent prefix |
| `devlog_error()` | `log_error()` | Consistent prefix |
| `devlog_check()` | `log_check()` | Consistent prefix |
| `devlog_http()` | `log_http()` | Consistent prefix |
| `devlog_func` | `log_func` | Consistent prefix |
| `devlog_trace()` | `trace()` | Top-level, used frequently |
| `devlog_trace_end()` | `trace_end()` | Top-level |
| `devlog_span()` | `span()` | Top-level, used frequently |
| `devlog_decision()` | `log_decision()` | Consistent prefix |
| `devlog_flow()` | `log_flow()` | Consistent prefix |
| `devlog_diff()` | `log_diff()` | Consistent prefix |
| `devlog_query()` | `log_query()` | Consistent prefix |
| `devlog_perf()` | `log_perf()` | Consistent prefix |
| `devlog_to_file()` | `to_file()` | Top-level config |
| `devlog_close_file()` | `close_file()` | Top-level config |
| `devlog_get_context()` | `get_context()` | Top-level |
| `devlog_summary()` | `summary()` | Top-level |
| `devlog_set_buffer_size()` | `set_buffer_size()` | Top-level config |

---

## 5. Repo Structure

```
agentlog/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Test on push/PR (Python 3.9-3.13)
│       └── publish.yml         # Publish to PyPI on tag
├── src/
│   └── agentlog/
│       ├── __init__.py
│       ├── _core.py
│       ├── _describe.py
│       ├── _emit.py
│       ├── _api.py
│       ├── _trace.py
│       ├── _advanced.py
│       ├── _buffer.py
│       ├── _sink.py
│       ├── _decorator.py
│       └── py.typed
├── tests/
│   ├── test_core.py            # Enable/disable, env detection
│   ├── test_describe.py        # Value descriptor for all types
│   ├── test_api.py             # All public API functions
│   ├── test_trace.py           # Trace/span context
│   ├── test_advanced.py        # Decision, flow, diff, query, perf
│   ├── test_buffer.py          # Ringbuffer, context export, summary
│   ├── test_sink.py            # JSONL file sink
│   ├── test_decorator.py       # @log_func sync and async
│   └── conftest.py             # Shared fixtures
├── typescript/
│   ├── src/
│   │   └── index.ts
│   ├── package.json
│   └── tsconfig.json
├── examples/
│   ├── basic.py                # Quick start
│   ├── fastapi_middleware.py   # FastAPI integration
│   ├── django_middleware.py    # Django integration
│   └── distributed_trace.py   # Multi-service tracing
├── docs/
│   ├── quickstart.md
│   ├── api-reference.md
│   ├── production-guide.md
│   └── ai-agent-guide.md      # How AI agents should use agentlog output
├── .ai/
│   ├── context.md              # AI agent context for this repo
│   └── coding-standards.md     # Coding standards for AI contributions
├── pyproject.toml              # PEP 621 metadata, build config
├── README.md                   # Main documentation
├── LICENSE                     # MIT
├── CHANGELOG.md                # Version history
└── .gitignore
```

---

## 6. Build & Release Plan

### Phase 1: Core Library (This Session)
1. Create repo structure with `pyproject.toml`
2. Port and refactor Python code from devlog v0.3 into modular files
3. Rename all APIs (`devlog_*` → `log_*` / top-level)
4. Add log levels for production use
5. Write comprehensive tests
6. Write README

### Phase 2: Polish & Publish
7. Add GitHub Actions CI (test matrix: Python 3.9-3.13)
8. Add publish workflow (PyPI on tag)
9. Port TypeScript version
10. Write examples (FastAPI, Django, basic)
11. Write docs (quickstart, API reference, production guide)
12. First release: `v1.0.0`

### Phase 3: Curiios Integration
13. Publish to PyPI
14. Update Curiios to `pip install agentlog` instead of local copies
15. Remove old devlog files from Curiios repo
16. Update Curiios `.ai/coding-standards.md` to reference agentlog

---

## 7. pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agentlog"
version = "1.0.0"
description = "Runtime observability for AI coding agents"
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
authors = [{ name = "Vinay Sachdeva" }]
keywords = ["logging", "ai", "agents", "observability", "debugging", "llm", "vibe-coding"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Logging",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/vinsac/agentlog"
Documentation = "https://github.com/vinsac/agentlog#readme"
Repository = "https://github.com/vinsac/agentlog"
Issues = "https://github.com/vinsac/agentlog/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/agentlog"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 8. Backward Compatibility

For Curiios and existing users of `devlog`:

```python
# agentlog provides a compatibility shim
from agentlog.compat import (
    devlog, devlog_vars, devlog_state, devlog_error,
    devlog_check, devlog_http, devlog_func,
    devlog_trace, devlog_trace_end, devlog_span,
    devlog_decision, devlog_flow, devlog_diff,
    devlog_query, devlog_perf,
    devlog_to_file, devlog_close_file,
    devlog_get_context, devlog_set_buffer_size, devlog_summary,
)
```

The `DEVLOG=true` env var will also continue to work alongside `AGENTLOG=true`.

---

## 9. Success Criteria

- [ ] `pip install agentlog` works
- [ ] Zero dependencies (stdlib only)
- [ ] 100% test coverage on core API
- [ ] Works with Python 3.9-3.13
- [ ] README is compelling and complete
- [ ] Curiios imports from `agentlog` instead of local copies
- [ ] TypeScript version published to npm
- [ ] Blog post: "Why We Built agentlog"

---

## 10. References

- [From Vibe Coding to Building Real Infrastructure with AI Agents](https://www.vinaysachdeva.com/from-vibe-coding-to-building-real-infrastructure-with-ai-agents/)
- [10 Things Developers Want from Agentic IDEs (RedMonk 2025)](https://redmonk.com/kholterhoff/2025/12/22/10-things-developers-want-from-their-agentic-ides-in-2025/)
- [AgentTrace: Agent-Centric Observability (arXiv)](https://arxiv.org/html/2602.10133)
- [Agentic Coding Handbook: Debug Workflow](https://tweag.github.io/agentic-coding-handbook/WORKFLOW_DEBUG/)
