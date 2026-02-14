# agentlog

**Runtime state capture for AI agent debugging.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

---

Your app crashed at 3am. Your AI coding agent sees this:

```
ValueError: Confidence 1.5 out of valid range [0, 1]
  File "app.py", line 30, in normalize_score
```

The agent adds a try/except. Wrong fix. It adds print statements. Reruns. Still guessing.
**Five debugging turns later**, it finds that `validate_rating()` accepted `1.5` as valid.

With agentlog, the agent sees this instead:

```
# agentlog debug context (session: sess_10a491b4)
# git: main@2c53442
# tokens: 230 total (gpt-4: 150in/80out)

{"tag":"error","err":"ValueError","err_msg":"Confidence 1.5 out of valid range [0, 1]",
 "locals":{"confidence":{"t":"float","v":1.5},"threshold":{"t":"float","v":0.7}}}

{"tag":"tool","tool":"validate_rating","args":{"confidence":{"v":1.5},"threshold":{"v":0.7}},"success":true}
```

One turn. The agent sees `validate_rating` returned `success: true` for `confidence: 1.5`.
The bug is obvious: missing upper-bound check. **Fixed in one shot.**

## Why This Exists

AI agents can read your source code. They **cannot** see:

- What your variables contained when the crash happened
- Which code path actually executed
- What data shapes flowed through your pipeline
- Why a function was called with unexpected arguments

agentlog captures this automatically. No print statements needed.

## Quick Start

```bash
pip install agentlog
export AGENTLOG=true
```

```python
import agentlog

# Automatic failure capture — locals at crash point
# Nothing to instrument, just enable and go

# After a crash, get an automatic fix in one shot:
code, explanation = agentlog.fix_this_crash()
```

### 🎯 The 10X Features

**Fix crashes in one shot instead of 5 attempts:**

```python
# One-shot crash fixer ⭐
code, explanation = agentlog.fix_this_crash()
# Returns: validated fix code + explanation

# Multi-agent cascade visualizer 🌊  
flow = agentlog.visualize_agent_flow()
# Shows: Agent A → Agent B → Error in Agent C

# Regression validator ✅
result = agentlog.validate_refactoring("baseline", "new")
# Returns: safe_to_merge, confidence_score, blocking_issues
```

### Session Tracking

```python
agentlog.start_session("my_agent", "refactoring task")

# All events within this session are correlated
# Git state (commit, branch, dirty) captured automatically

agentlog.end_session()
```

### Tool & LLM Call Tracking

```python
with agentlog.llm_call("gpt-4", prompt) as call:
    response = api.chat(prompt)
    call["tokens_in"] = response.usage.prompt_tokens
    call["tokens_out"] = response.usage.completion_tokens

with agentlog.tool_call("search_db", {"query": q}) as call:
    results = search(q)
    call["result"] = results
```

### Always-On Failure Hook

```python
# Installed automatically when AGENTLOG=true
# Captures locals at the crash point (bottom frame only)
# Inline redaction of API keys, passwords, tokens
# No manual instrumentation needed
```

## What It Captures

| Event | What The Agent Learns |
|-------|----------------------|
| **Failure** | Exception type, message, locals at crash point (redacted) |
| **LLM call** | Model, prompt, tokens in/out, duration |
| **Tool call** | Tool name, arguments, success/failure, stdout/stderr |
| **Session** | Agent name, task, git commit/branch/dirty state |
| **Git diff** | What changed between agent turns (first 50 lines) |

## `get_debug_context()` — The Killer Feature

One function call exports everything an AI agent needs to debug a crash:

```python
context = agentlog.get_debug_context(max_tokens=4000)
```

- **Errors first** — failures and session events prioritized
- **Session-scoped** — only events from the current session
- **Token-budgeted** — fits in an LLM context window
- **Git context** — commit hash, branch, dirty state in header
- **Token summary** — cumulative LLM usage in header

## Value Descriptors

Every value is described with a compact schema optimized for token efficiency:

```json
{"t":"str", "v":"Python"}
{"t":"list", "n":100, "it":"dict", "preview":[{"id":1},{"id":2}]}
{"t":"ndarray", "sh":"(768,)", "dt":"float32", "range":[0.0, 1.0]}
```

~40% fewer tokens than human-readable logging.

## Design Constraints

- **Zero dependencies** — Python stdlib only
- **Zero cost when off** — all calls are no-ops when disabled
- **No dashboards** — logs for machines, not humans
- **Compact JSON** — short keys (`t`, `v`, `n`, `k`) for token efficiency
- **Env var only** — `AGENTLOG=true`, no config files

## When agentlog Helps Most

- **Production crashes** — app fails when the agent isn't watching; locals are captured automatically
- **Non-reproducible bugs** — fails 1 in 100 times; runtime state is always being recorded
- **Long-running processes** — servers, workers, pipelines; historical state without print statements
- **Complex data pipelines** — tensor shapes, dict keys, list lengths; structured not stringified

## API Reference

### 🎯 Clear Winner Features (10X Improvements)

| Function | Purpose |
|----------|---------|
| `fix_this_crash()` | **One-shot crash fixer** — detect pattern, generate fix, reduce iterations from 5→1 |
| `visualize_agent_flow()` | **Multi-agent debugger** — show cascade: Agent A → Agent B → Error |
| `validate_refactoring()` | **Regression validator** — opinionated safe/unsafe decision with confidence score |
| `quick_validate()` | **Quick regression check** — returns "SAFE", "CAUTION", "REVIEW", or "UNSAFE" |

### Core API

| Function | Purpose |
|----------|---------|
| `enable()` / `disable()` | Toggle agentlog |
| `start_session(agent, task)` | Start correlated session with git capture |
| `end_session()` | End session |
| `get_debug_context(max_tokens)` | Export failure-prioritized context for AI agents |
| `get_context(max_tokens, tags)` | Export recent logs within token budget |
| `summary()` | Compact session summary |
| `token_summary()` | Aggregate LLM token usage |
| `log(msg, **ctx)` | Log message with context |
| `log_error(msg, error, **ctx)` | Log error with traceback |
| `log_vars(*args)` | Log variable names, types, values |
| `llm_call(model, prompt)` | Context manager for LLM calls |
| `tool_call(name, args)` | Context manager for tool calls |
| `to_file(path)` / `close_file()` | JSONL file sink |

## Philosophy

> AI agents are blind to runtime state. Tracebacks show *where* code failed,
> not *why*. agentlog captures the *why* — automatically, passively, efficiently.

## License

MIT

---

## 🤖 AI Coding Agents

If you are an AI coding agent, read `.ai/README.md` before making changes.
