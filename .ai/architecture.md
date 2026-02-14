# Architecture Guide

## Purpose

Defines the minimal, functional architecture for agentlog's failure-boundary runtime visibility.

## Architecture Pattern

**Functional Module with Global State**

- Single Python module (`agentlog.py`)
- Module-level state (enabled flag, buffer, config)
- Pure functions for all operations
- No classes, no inheritance, no OOP complexity

## Component Structure

### Core Components

**1. State Management**
- `_enabled`: Boolean flag (default: False)
- `_buffer`: Ringbuffer (list with max size)
- `_config`: Dict with level, prefix, file handle
- `_trace_context`: Thread-local trace/span IDs

**2. Public API Functions**
- `enable()` / `disable()`: Toggle logging
- `log()`: Basic message with context
- `log_error()`: Error with structured context
- `log_vars()`: Variable inspection
- `start_session()` / `end_session()`: Session management
- `llm_call()` / `tool_call()`: Context managers
- `get_debug_context()`: Failure-prioritized export
- `get_context()`: Log export
- `summary()` / `token_summary()`: Aggregations

**3. Private Helper Functions**
- `_summarize_value()`: Convert any value to descriptor
- `_emit()`: Write JSON line to output
- `_should_log()`: Check if logging enabled and level matches

**4. Automatic Capture**
- `sys.excepthook` override for unhandled exceptions
- Captures local variables at failure point
- Captures stdout/stderr from tools (`_capture.py`)
- Captures git diffs between turns (`_git.py`)
- No decorator or instrumentation required

## Data Flow

```
1. Application code calls log function
2. Check if enabled and level matches
3. If disabled: return immediately (no-op)
4. If enabled: summarize values
5. Build JSON structure
6. Add to ringbuffer
7. Emit to stdout/file
```

**Failure Capture Flow:**
```
1. Unhandled exception occurs
2. sys.excepthook triggered
3. Extract frame locals
4. Summarize all local variables
5. Build structured error context
6. Emit JSON line
7. Call original excepthook
```

## Integration Points

### Input
- Environment variables: `AGENTLOG`, `AGENTLOG_LEVEL`
- Programmatic API: `enable()`, `configure()`
- Automatic: `sys.excepthook` for exceptions

### Output
- stdout: Single-line JSON (default)
- File: JSONL sink via `to_file()`
- Memory: Ringbuffer for `get_context()`

### No External Integrations
- No framework hooks (Django, Flask, FastAPI)
- No cloud services (AWS, GCP, Azure)
- No databases or message queues
- No distributed tracing systems

## Design Principles

### Simplicity First
- Single file, single module
- Functions over classes
- Global state over complex patterns
- Explicit over implicit

### Zero Cost When Disabled
- Early return in all functions
- No computation if disabled
- No memory allocation
- No I/O operations

### Token Efficiency
- Compact JSON schema
- Short key names (`t`, `v`, `n`, `k`)
- Value summarization (truncate, preview)
- No verbose messages

### Failure Safety
- Never crash on bad input
- Catch all exceptions in helpers
- Safe value serialization
- Graceful degradation

## Non-Goals

### What We Don't Build
- **No plugin system**: No extensibility framework
- **No middleware**: No framework integration layer
- **No async runtime**: Works with sync and async, but no special handling
- **No distributed coordination**: No cross-process communication
- **No schema versioning**: Single schema, no migrations

## AI Agent Guidelines

- Keep architecture simple and flat
- Resist adding layers or abstractions
- Maintain single-file structure as long as possible
- Question any addition that increases complexity
- Prioritize function count reduction over feature addition
