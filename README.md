# agentlog

**Runtime observability for AI coding agents.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-82%20passing-brightgreen.svg)]()

---

## The Problem

AI coding agents (Cursor, Windsurf, Copilot, Claude Code, Codex) are **blind to your application's runtime state**. They can read your source code, but they can't see what your variables contain, which code paths executed, what shape your data has, or why something failed at runtime.

Existing tools don't solve this:

| Tool | What it does | Gap |
|------|-------------|-----|
| **structlog / loguru** | Structured production logging | Designed for ops dashboards, not AI context windows |
| **icecream** | Pretty-prints variables | Human-readable, not machine-parseable |
| **Langfuse / LangSmith** | Traces LLM API calls | Only instruments AI calls, not your app code |
| **OpenTelemetry** | Distributed tracing | Heavy, complex, designed for APM platforms |

## The Solution

```bash
pip install agentlog
```

```python
from agentlog import log, log_vars, log_error, log_func, span

log("Processing request", user_id=uid, skill_name=name)
log_vars(confidence, embedding_vector, result_dict)

@log_func
async def create_skill(name: str) -> dict: ...

with span("normalize"):
    result = normalize(raw_name)
```

Output (one JSON line per call, greppable):
```
[AGENTLOG:info] {"seq":1,"ts":1739512200,"at":"main.py:42 create_skill","msg":"Processing request","ctx":{"user_id":{"t":"str","v":"u_abc"},"skill_name":{"t":"str","v":"Python"}}}
```

AI agents parse this from terminal output to understand your application's runtime state.

## Why agentlog?

1. **AI-First** — Compact JSON with short keys (`t`, `v`, `n`, `k`) that minimize token usage in LLM context windows
2. **Dev + Production** — Not just a dev tool. Log levels, structured output, JSONL sinks
3. **Zero Dependencies** — Python stdlib only. Works anywhere Python 3.9+ runs
4. **Zero Cost When Off** — All calls are no-ops when disabled
5. **Token-Aware** — Built-in ringbuffer with token-budgeted export for context window management
6. **Framework Agnostic** — Django, FastAPI, Flask, scripts, notebooks, anything

## Quick Start

### Enable

```bash
# Environment variable (recommended)
export AGENTLOG=true

# With level filter for production
export AGENTLOG=true
export AGENTLOG_LEVEL=error
```

```python
# Or programmatically
from agentlog import enable, disable
enable()   # for tests, REPL, notebooks
disable()  # turn off
```

### Core API

```python
from agentlog import log, log_vars, log_state, log_error, log_check, log_http

# Message with context
log("Processing request", user_id=uid, skill_name=name)

# Variable inspection — names extracted from source
log_vars(confidence, embedding_vector, result_dict)

# State snapshots
log_state("before_update", profile.__dict__)

# Error with traceback
try:
    result = await normalize(name)
except Exception as e:
    log_error("Normalization failed", error=e, input_name=name)

# Runtime assertions (log, don't crash)
log_check(len(results) > 0, "Expected results", query=q)

# HTTP request/response
log_http("POST", "/api/skills", 201, 45.2, body=payload)
```

### Function Decorator

```python
from agentlog import log_func

@log_func
def create_skill(name: str, source: str) -> dict:
    ...

@log_func(log_return=False)
async def fetch_all_embeddings() -> list:
    ...
```

Logs entry, exit, args, return value, duration, and exceptions automatically.

### Distributed Tracing

```python
from agentlog import trace, trace_end, get_trace_id, span

# Start a trace at your entry point
tid = trace()
resp = httpx.post(url, headers={"X-Trace-Id": tid})

# In downstream service
trace(request.headers.get("X-Trace-Id"))

# Named spans with auto timing
with span("normalize_skill", input=raw_name):
    normalized = await normalize(raw_name)
    with span("fetch_embeddings"):
        embeddings = await get_embeddings(normalized)

trace_end()
```

All log entries within a trace automatically include the trace/span IDs.

### Decision Logging

```python
from agentlog import log_decision

log_decision(
    "Should merge with existing skill?",
    confidence >= 0.9,
    reason=f"confidence {confidence} >= threshold 0.9",
    confidence=confidence, threshold=0.9
)
```

AI agents need to understand **why** a code path was taken, not just what happened.

### Data Flow Tracing

```python
from agentlog import log_flow

log_flow("skill_pipeline", "raw_input", raw_name)
log_flow("skill_pipeline", "validated", validated)
log_flow("skill_pipeline", "normalized", normalized, confidence=0.95)
log_flow("skill_pipeline", "embedded", embedding)
```

### State Diffing

```python
from agentlog import log_diff

# Shows added/removed/changed — not two raw dumps
log_diff("user_profile", old_profile.__dict__, new_profile.__dict__)
```

### Query Logging

```python
from agentlog import log_query

log_query("SELECT", "skills", 12.3, rows=42, where="category='ml'")
log_query("vector_search", "embeddings", 89.5, rows=10, k=10)
log_query("cache_get", "redis:skills", 0.5, hit=True, key=cache_key)
```

### Performance Snapshots

```python
from agentlog import log_perf

log_perf("before_embedding_batch")
embeddings = compute_embeddings(batch)
log_perf("after_embedding_batch", batch_size=len(batch))
```

### JSONL File Sink

```python
from agentlog import to_file, close_file

to_file(".agentlog/session.jsonl")
# ... run your code ...
close_file()
# AI agent can read .agentlog/session.jsonl for full replay
```

### Context Budget (Token-Aware Export)

The #1 pain point with AI coding agents: **context window overflow**.

```python
from agentlog import get_context, summary, set_buffer_size

# Export recent logs within token budget
context = get_context(max_tokens=4000, tags=["error", "check", "decision"])

# Compact session summary
s = summary()
# {"total": 142, "by_tag": {"info": 80, "func": 40, "error": 2},
#  "errors": ["Failed: ValueError(...)"],
#  "failed_checks": ["Expected non-empty results"],
#  "slowest_funcs": [{"fn": "create_skill", "ms": 245.3}]}

# Configure buffer size
set_buffer_size(1000)
```

### Log Levels

```bash
# Development: everything
AGENTLOG=true

# Production: only errors and failed checks
AGENTLOG=true
AGENTLOG_LEVEL=error
```

| Level | Tags included |
|-------|--------------|
| `debug` | vars, state, flow, diff, perf |
| `info` | log, http, query, func, decision, span, trace |
| `warn` | check (failed) |
| `error` | error |

### Configuration

```python
from agentlog import configure

configure(
    level="info",           # minimum level
    tag_prefix="MYAPP",     # customize prefix: [MYAPP:info]
)
```

## Value Descriptor Schema

Every value is described with a compact descriptor optimized for LLM token budgets:

| Key | Meaning | Example |
|-----|---------|---------|
| `t` | type name | `"str"`, `"list"`, `"ndarray"` |
| `v` | value (scalars, small collections) | `"Python"`, `0.95`, `[1,2,3]` |
| `n` | length/count | `42` |
| `k` | keys (dicts, objects) | `["name","id","score"]` |
| `it` | item type (homogeneous collections) | `"dict"` |
| `sh` | shape (numpy/torch/pandas) | `"(768,)"` |
| `dt` | dtype (numpy/torch) | `"float32"` |
| `range` | min/max (numeric arrays) | `[0.0, 1.0]` |
| `preview` | first 3 items of large collections | `[1, 2, 3]` |
| `truncated` | original length if string was cut | `5000` |

### Why Short Keys?

```json
// Human-friendly (wasteful for AI)
{"type": "str", "value": "Python", "length": 6}

// AI-first (agentlog)
{"t": "str", "v": "Python"}
```

~40% fewer tokens. Over hundreds of log lines in a debugging session, this adds up.

## Migrating from devlog

agentlog includes a backward compatibility shim:

```python
# Step 1: Change import source
from agentlog.compat import devlog, devlog_vars, devlog_func, devlog_span

# Step 2 (optional): Rename to new API
from agentlog import log, log_vars, log_func, span
```

The `DEVLOG=true` env var also continues to work.

## API Reference

### Core

| Function | Purpose |
|----------|---------|
| `log(msg, **ctx)` | Log message with context |
| `log_vars(*args, **kw)` | Log variable names, types, values |
| `log_state(label, obj)` | Log state snapshot |
| `log_error(msg, error, **ctx)` | Log error with traceback |
| `log_check(cond, msg, **ctx)` | Runtime assertion (logs, doesn't crash) |
| `log_http(method, url, status, ms)` | Log HTTP request/response |
| `@log_func` | Decorator: entry/exit/args/return/duration |

### Tracing

| Function | Purpose |
|----------|---------|
| `trace(id?)` | Start/set trace ID |
| `trace_end()` | End current trace |
| `get_trace_id()` | Get trace ID for header propagation |
| `span(name, **ctx)` | Context manager for named spans |

### Advanced

| Function | Purpose |
|----------|---------|
| `log_decision(q, answer, reason)` | Log why a code path was taken |
| `log_flow(pipeline, step, value)` | Track value through pipeline |
| `log_diff(label, before, after)` | Compute and log state diff |
| `log_query(op, target, ms, rows)` | Log DB/cache/vector queries |
| `log_perf(label)` | Memory/thread/PID snapshot |

### Context Budget

| Function | Purpose |
|----------|---------|
| `get_context(max_tokens, tags)` | Export recent logs within token budget |
| `summary()` | Compact session summary |
| `set_buffer_size(n)` | Configure ringbuffer (default 500) |

### Configuration

| Function | Purpose |
|----------|---------|
| `enable()` / `disable()` | Programmatic toggle |
| `configure(level, tag_prefix)` | Set level and prefix |
| `to_file(path)` / `close_file()` | JSONL file sink |

## Philosophy

> "AI agents are blind to runtime state unless you show it to them."
>
> "We will need logging and debugging systems designed for machines to reason over, not just dashboards for people to read."
>
> — [From Vibe Coding to Building Real Infrastructure with AI Agents](https://www.vinaysachdeva.com/from-vibe-coding-to-building-real-infrastructure-with-ai-agents/)

## License

MIT
