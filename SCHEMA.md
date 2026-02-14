# agentlog JSON Schema

This document defines the JSON schema for agentlog output. All log entries follow this structure for consistent AI agent consumption.

## Core Structure

Every log entry has this base structure:

```json
{
  "seq": 1,
  "ts": 1771089547.42,
  "at": "main.py:42 function_name",
  "trace": "optional_trace_id",
  "span": "optional_span_id",
  ...tag-specific fields...
}
```

### Base Fields

| Field | Type | Description |
|-------|------|-------------|
| `seq` | int | Monotonically increasing sequence number |
| `ts` | float | Unix timestamp (seconds since epoch) |
| `at` | string | Location: `filename:line function_name` |
| `trace` | string | Optional trace ID for distributed tracing |
| `span` | string | Optional span ID for nested operations |

## Value Descriptors

All values are described using compact descriptors to minimize tokens:

```json
{
  "t": "str",           // type name
  "v": "value",         // actual value (for scalars)
  "n": 42,              // length/count (for collections)
  "k": ["key1", "key2"], // keys (for dicts)
  "it": "dict",         // item type (for homogeneous collections)
  "sh": "(768,)",       // shape (for numpy/torch/pandas)
  "dt": "float32",      // dtype (for numpy/torch)
  "range": [0.0, 1.0],  // min/max (for numeric arrays)
  "preview": [1, 2, 3], // first items of large collections
  "truncated": 5000     // original length if string was cut
}
```

### Descriptor Examples

**Scalar:**
```json
{"t": "str", "v": "Python"}
{"t": "int", "v": 42}
{"t": "float", "v": 0.95}
{"t": "bool", "v": true}
{"t": "NoneType", "v": null}
```

**Collections:**
```json
{"t": "list", "n": 3, "it": "str", "v": ["a", "b", "c"]}
{"t": "list", "n": 100, "it": "dict", "preview": [{"id": 1}, {"id": 2}, {"id": 3}]}
{"t": "dict", "n": 5, "k": ["name", "age", "email"], "v": {"name": "Alice", "age": 30, "email": "alice@example.com"}}
```

**Arrays:**
```json
{"t": "ndarray", "sh": "(1000, 768)", "dt": "float32", "range": [-0.5, 0.5]}
{"t": "DataFrame", "sh": "(100, 10)", "cols": ["id", "name", "score"]}
```

## Tag-Specific Schemas

### `info` - General Log

```json
{
  "seq": 1,
  "ts": 1771089547.42,
  "at": "main.py:42 process_request",
  "msg": "Processing request",
  "ctx": {
    "user_id": {"t": "str", "v": "u_123"},
    "skill_name": {"t": "str", "v": "Python"}
  }
}
```

### `error` - Error with Context

```json
{
  "seq": 2,
  "ts": 1771089547.42,
  "at": "main.py:45 process_skill",
  "fn": "process_skill",
  "error": {
    "type": "ValueError",
    "msg": "Invalid confidence: 1.5"
  },
  "locals": {
    "confidence": {"t": "float", "v": 1.5},
    "threshold": {"t": "float", "v": 1.0},
    "user_id": {"t": "str", "v": "u_123"}
  }
}
```

### `decision` - Decision Logging

```json
{
  "seq": 3,
  "ts": 1771089547.42,
  "at": "main.py:50 should_merge",
  "question": "Should merge with existing skill?",
  "answer": {"t": "bool", "v": false},
  "reason": "confidence 0.85 < threshold 0.9",
  "ctx": {
    "confidence": {"t": "float", "v": 0.85},
    "threshold": {"t": "float", "v": 0.9}
  }
}
```

### `flow` - Data Flow Tracing

```json
{
  "seq": 4,
  "ts": 1771089547.42,
  "at": "main.py:60 normalize",
  "pipeline": "skill_creation",
  "step": "normalized",
  "value": {"t": "str", "v": "python programming"},
  "ctx": {
    "confidence": {"t": "float", "v": 0.95}
  }
}
```

### `diff` - State Diffing

```json
{
  "seq": 5,
  "ts": 1771089547.42,
  "at": "main.py:70 update_profile",
  "label": "user_profile",
  "added": {
    "verified": {"t": "bool", "v": true}
  },
  "removed": {
    "temp_token": {"t": "str", "v": "abc123"}
  },
  "changed": {
    "age": {
      "from": {"t": "int", "v": 30},
      "to": {"t": "int", "v": 31}
    }
  }
}
```

### `func` - Function Entry/Exit

```json
{
  "seq": 6,
  "ts": 1771089547.42,
  "at": "main.py:80 create_skill",
  "fn": "create_skill",
  "ev": "entry",
  "args": {
    "name": {"t": "str", "v": "Python"},
    "source": {"t": "str", "v": "user_input"}
  }
}
```

```json
{
  "seq": 7,
  "ts": 1771089547.52,
  "at": "main.py:80 create_skill",
  "fn": "create_skill",
  "ev": "exit",
  "ms": 100.5,
  "ret": {"t": "dict", "n": 3, "k": ["id", "name", "status"]}
}
```

### `span` - Named Span

```json
{
  "seq": 8,
  "ts": 1771089547.42,
  "at": "main.py:90 process",
  "span_name": "normalize_skill",
  "ev": "start",
  "ctx": {
    "input": {"t": "str", "v": "  Python  "}
  }
}
```

### `query` - Database/External Query

```json
{
  "seq": 9,
  "ts": 1771089547.42,
  "at": "main.py:100 fetch_skills",
  "op": "SELECT",
  "target": "skills",
  "ms": 12.3,
  "rows": 42,
  "ctx": {
    "where": {"t": "str", "v": "category='ml'"}
  }
}
```

### `perf` - Performance Snapshot

```json
{
  "seq": 10,
  "ts": 1771089547.42,
  "at": "main.py:110 compute_embeddings",
  "label": "after_batch",
  "rss_mb": 245.3,
  "threads": 8,
  "pid": 12345,
  "ctx": {
    "batch_size": {"t": "int", "v": 100}
  }
}
```

### `check` - Runtime Assertion

```json
{
  "seq": 11,
  "ts": 1771089547.42,
  "at": "main.py:120 validate",
  "msg": "Expected non-empty results",
  "passed": false,
  "ctx": {
    "query": {"t": "str", "v": "SELECT * FROM skills"},
    "result_count": {"t": "int", "v": 0}
  }
}
```

### `http` - HTTP Request/Response

```json
{
  "seq": 12,
  "ts": 1771089547.42,
  "at": "main.py:130 api_call",
  "method": "POST",
  "url": "/api/skills",
  "status": 201,
  "ms": 45.2,
  "ctx": {
    "body": {"t": "dict", "n": 3, "k": ["name", "category", "confidence"]}
  }
}
```

## Log Levels

Tags are mapped to log levels for filtering:

| Level | Tags |
|-------|------|
| `debug` | vars, state, flow, diff, perf |
| `info` | info, http, query, func, decision, span, trace |
| `warn` | check (failed) |
| `error` | error |

Set `AGENTLOG_LEVEL=info` to only emit info and above.

## Token Efficiency

The schema is optimized for token efficiency:

- Short keys: `t`, `v`, `n`, `k` instead of `type`, `value`, `length`, `keys`
- Compact format: `separators=(',', ':')` with no whitespace
- Value summarization: Large collections show `preview` instead of full data
- String truncation: Long strings are cut with `truncated` field

**Example token savings:**

```json
// Human-friendly (wasteful)
{"type": "string", "value": "Python", "length": 6}

// AI-first (agentlog)
{"t": "str", "v": "Python"}
```

~40% fewer tokens per value descriptor.

## Context Export Format

`get_context()` returns JSONL (JSON Lines) format:

```
{"seq":1,"ts":1771089547.42,"at":"main.py:42","msg":"Processing"}
{"seq":2,"ts":1771089547.43,"at":"main.py:45","error":{"type":"ValueError"}}
{"seq":3,"ts":1771089547.44,"at":"main.py:50","question":"Should merge?"}
```

Each line is a complete JSON object. AI agents can:
- Parse line-by-line
- Filter by tag
- Fit within token budgets
- Process chronologically

## Version

Schema version: 1.0 (Phase 1 - AI Debugging Foundation)
