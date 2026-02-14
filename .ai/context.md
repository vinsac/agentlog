# agentlog — AI Agent Context

> Runtime observability for AI coding agents.

## What This Is

A zero-dependency Python library (stdlib only, 3.9+) that outputs structured JSON logs designed for AI coding agents to parse from terminal output. Works in both development and production.

## Repo Structure

```
agentlog/
├── src/agentlog/          # Source code
│   ├── __init__.py        # Public API re-exports
│   ├── _core.py           # Config, enable/disable, env detection, log levels
│   ├── _describe.py       # Value descriptor engine (compact keys: t, v, n, k)
│   ├── _emit.py           # Output engine: format, route to sinks
│   ├── _api.py            # Core API: log, log_vars, log_state, log_error, log_check, log_http
│   ├── _trace.py          # Distributed tracing: trace, span, get_trace_id
│   ├── _advanced.py       # log_decision, log_flow, log_diff, log_query, log_perf
│   ├── _buffer.py         # Token-aware ringbuffer, get_context, summary
│   ├── _sink.py           # JSONL file sink
│   ├── _decorator.py      # @log_func decorator (sync + async)
│   ├── compat.py          # Backward compat shim for devlog API names
│   └── py.typed           # PEP 561 marker
├── tests/                 # pytest test suite (82 tests)
├── pyproject.toml         # PEP 621, hatchling build
├── PLAN.md                # Project plan and design decisions
├── CHANGELOG.md           # Version history
└── README.md              # Full documentation
```

## Key Design Decisions

- **Short keys** (`t`, `v`, `n`, `k`) minimize LLM token usage
- **Log levels** (debug/info/warn/error) via `AGENTLOG_LEVEL` env var
- **Tag prefix** `[AGENTLOG:<tag>]` for grep-friendly output
- **Ringbuffer** (default 500 entries) with token-budgeted export
- **Thread-safe** sequence counter, JSONL writes, ringbuffer access
- **No dependencies** — everything is Python stdlib

## Environment Variables

| Variable | Purpose | Values |
|----------|---------|--------|
| `AGENTLOG` | Enable/disable | `true`, `1`, `yes`, `on` |
| `AGENTLOG_LEVEL` | Minimum log level | `debug`, `info`, `warn`, `error` |
| `DEVLOG` | Legacy toggle (also works) | `true`, `1`, `yes`, `on` |

## Running Tests

```bash
pytest tests/ -v
```
