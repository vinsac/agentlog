# AgentLog API Reference

Complete reference for all AgentLog functions.

---

## 🎯 Clear Winner Features (10X Improvements)

### fix_this_crash()

**One-shot crash fixer** — Detects error patterns and generates validated fix code.

```python
code, explanation = agentlog.fix_this_crash(
    max_attempts=3,      # Maximum fix attempts to generate
    auto_commit=False    # Whether to apply fix automatically (not implemented)
)
```

**Returns:** `(str, str)` — (fix_code, explanation)

**Supported Error Patterns:**
- `ValueError` — Range violations, type conversion errors, invalid choices
- `KeyError` — Missing dictionary keys
- `AttributeError` — NoneType access, wrong type attribute access
- `IndexError` — List index out of range
- `TypeError` — Operand type mismatch, not callable, wrong arg count

**Example:**
```python
# When a crash occurs:
# ValueError: Confidence 1.5 out of range [0, 1]

code, explanation = agentlog.fix_this_crash()
# Returns:
# code = """
# if not (0 <= confidence <= 1):
#     raise ValueError(f"confidence must be between 0 and 1, got {confidence}")
# """
# explanation = "confidence=1.5 is outside valid range [0, 1]. Add bounds check."
```

---

### analyze_crash()

**Detailed crash analysis** — Returns comprehensive diagnostic information.

```python
analysis = agentlog.analyze_crash(
    session_id=None  # Session to analyze (default: current)
)
```

**Returns:** `dict` with keys:
- `has_error` (bool) — Whether an error was found
- `error_type` (str) — Exception type
- `error_message` (str) — Exception message
- `location` (dict) — File, line, function where crash occurred
- `is_new_error` (bool) — Whether this is first occurrence
- `times_seen_before` (int) — How many times this error pattern seen
- `variables_at_crash` (list) — Variable names captured at crash point
- `suggested_fix` (str) — Generated fix code

---

### analyze_and_validate_refactoring()

**Integrated crash + regression gate** — Runs crash analysis and regression validation in one call.

```python
result = agentlog.analyze_and_validate_refactoring(
    baseline_session=None,  # Auto-resolve from saved baselines (prefers "stable")
    new_session=None,       # Defaults to current active session
    strict_mode=False       # Passed to validate_refactoring
)
```

**Returns:** `dict` with keys:
- `crash_analysis` (dict) — Output of `analyze_crash()`
- `regression_validation` (dict|None) — Output of `validate_refactoring()` when baseline/session exist
- `baseline_session_used` (str|None)
- `new_session_used` (str|None)
- `recommendation` (str)

---

### visualize_agent_flow()

**Multi-agent flow visualizer** — Shows data flow between agents.

```python
flow = agentlog.visualize_agent_flow(
    session_id=None,        # Starting session (default: current)
    format="agent_readable", # Output format
    lookback_sessions=10    # How many recent sessions to include
)
```

**Returns:** `str` — Text visualization optimized for LLM consumption

**Shows:**
- Session list with agents and tasks
- Parent-child relationships
- Failure cascade chains
- Data flow diagrams
- Root cause analysis

**Example Output:**
```
============================================================
MULTI-AGENT FLOW ANALYSIS
============================================================

Sessions: 3
Connections: 2
Failure Cascades Detected: 1

...

Cascade #1:
  cursor started 'data processing' → codex processed 'transform'
  → cursor FAILED: 'validate output'
  Chain: abc123 → def456 → ghi789
  
  ROOT CAUSE: abc123 (data originated here)
  FAILURE POINT: ghi789 (error manifested here)
  
  → Data corrupted in early session, caused failure downstream
```

---

### get_cascade_summary()

**Quick cascade detection** — Returns summary of failure cascades.

```python
summary = agentlog.get_cascade_summary(
    session_id=None  # Session to check (default: current)
)
```

**Returns:** `dict` with keys:
- `has_cascade` (bool) — Whether cascade detected
- `summary` (str) — Brief description
- `full_analysis` (str) — Complete flow analysis (if cascade detected)
- `recommendation` (str) — Action recommendation

---

### validate_refactoring()

**Regression validator** — Opinionated safe/unsafe decision for refactoring.

```python
result = agentlog.validate_refactoring(
    baseline_session,  # Stable baseline session ID
    new_session,        # New refactored session ID
    strict_mode=False  # If True, requires perfect match
)
```

**Returns:** `dict` with keys:
- `safe_to_merge` (bool) — Whether refactoring is safe
- `confidence_score` (float) — 0-100 confidence in decision
- `decision` (str) — "safe", "caution", "review_required", or "unsafe"
- `blocking_issues` (list) — List of problems preventing merge
- `recommendations` (list) — Suggested actions
- `detailed_analysis` (dict) — Full breakdown:
  - `overall_score` — Combined safety score
  - `component_scores` — Error, outcome, behavior scores
  - `error_delta` — New vs resolved errors
  - `outcome_analysis` — Baseline vs current outcome
  - `behavior_analysis` — Token efficiency, error rate changes

**Scoring Weights:**
- Error delta: 40%
- Outcome: 35%
- Behavior: 25%

---

### quick_validate()

**Quick regression check** — Simple yes/no/maybe result.

```python
result = agentlog.quick_validate(
    baseline_session=None,  # Default: "stable" baseline
    new_session=None        # Default: current session
)
```

**Returns:** `str` — "SAFE", "CAUTION", "REVIEW", "UNSAFE", "NO_BASELINE", or "NO_SESSION"

---

## Core API

### Configuration

#### enable()
```python
agentlog.enable()
```
Enable agentlog at runtime.

#### disable()
```python
agentlog.disable()
```
Disable agentlog at runtime.

#### is_enabled()
```python
enabled = agentlog.is_enabled()
```
Check if agentlog is enabled.

**Returns:** `bool`

---

### Session Management

#### start_session()
```python
agentlog.start_session(
    agent_name,  # Name of the agent (e.g., "cursor", "codex")
    task,        # Description of the task
    parent_session_id=None  # For multi-agent chains
)
```
Start a new correlated session. Captures git state automatically.

#### end_session()
```python
agentlog.end_session()
```
End the current session.

#### get_session_id()
```python
session_id = agentlog.get_session_id()
```
**Returns:** `str` — Current session ID or None

#### get_parent_session_id()
```python
parent_id = agentlog.get_parent_session_id()
```
**Returns:** `str` — Parent session ID or None

---

### Context Export

#### get_debug_context()
```python
context = agentlog.get_debug_context(
    max_tokens=4000,  # Maximum tokens to return
    session_id=None   # Specific session (default: current)
)
```
**Returns:** `str` — Token-budgeted debug context

Prioritizes: errors → session events → traces → logs

#### get_context_smart()
```python
context = agentlog.get_context_smart(
    max_tokens=4000,
    tags=None,       # Filter by tags (e.g., ["error", "llm"])
    priority_tags=None  # Tags to prioritize
)
```
**Returns:** `str` — Smart context with importance weighting

#### summary()
```python
s = agentlog.summary()
```
**Returns:** `dict` — Session summary with counts

---

### Logging

#### log()
```python
agentlog.log(
    message,      # Log message
    tag=None,     # Event tag (e.g., "custom", "milestone")
    **context     # Additional context key-value pairs
)
```

#### log_vars()
```python
agentlog.log_vars(
    var1, var2,  # Variable names as strings
    **extra      # Additional context
)
```
Log variable names, types, and values.

#### log_error()
```python
agentlog.log_error(
    message,           # Error message
    error=None,        # Exception object
    capture_locals=True, # Capture local variables
    **context          # Additional context
)
```

#### log_state()
```python
agentlog.log_state(
    name,   # State name
    value,  # State value
    **context
)
```

#### log_check()
```python
agentlog.log_check(
    condition,  # Boolean condition
    name=None,  # Check name
    **context
)
```

---

### Tracing

#### trace()
```python
with agentlog.trace(
    name,          # Trace name
    trace_id=None, # Custom trace ID
    **context
):
    # Code to trace
    pass
```

#### span()
```python
with agentlog.span(
    name,      # Span name
    parent=None,  # Parent span
    **context
):
    # Code in span
    pass
```

---

### LLM & Tool Tracking

#### llm_call()
```python
with agentlog.llm_call(
    model,      # Model name (e.g., "gpt-4")
    prompt,     # Prompt or prompt hash
    **context
) as call:
    response = api.chat(prompt)
    call["tokens_in"] = response.usage.prompt_tokens
    call["tokens_out"] = response.usage.completion_tokens
    call["response"] = response.content[:100]  # Preview only
```

#### tool_call()
```python
with agentlog.tool_call(
    name,   # Tool name
    args,   # Arguments dict
    **context
) as call:
    result = tool(**args)
    call["result"] = result
    call["success"] = True
```

---

### File Output

#### to_file()
```python
agentlog.to_file(
    path,           # Output file path (.jsonl)
    buffer_size=100 # Buffer flush threshold
)
```
Enable file output sink.

#### close_file()
```python
agentlog.close_file()
```
Close file sink.

---

### Error Pattern Correlation

#### hash_error()
```python
error_hash = agentlog.hash_error(
    error_type,  # Exception type name
    file,        # File path
    line         # Line number
)
```
**Returns:** `str` — Error pattern hash

#### correlate_error()
```python
correlation = agentlog.correlate_error(
    error_type,
    file,
    line
)
```
**Returns:** `dict` with keys:
- `is_new` (bool) — First occurrence
- `times_seen_before` (int)
- `other_sessions` (list) — Sessions with same error
- `has_fix` (bool) — Whether fix recorded

#### get_all_patterns()
```python
patterns = agentlog.get_all_patterns()
```
**Returns:** `dict` — All recorded error patterns

---

### Workspace Snapshots

#### snapshot_workspace()
```python
snapshot = agentlog.snapshot_workspace(
    files=None,        # Specific files (default: tracked git files)
    max_size_mb=10     # Max total size
)
```
**Returns:** `dict` — File hashes and metadata

#### compare_snapshots()
```python
diff = agentlog.compare_snapshots(
    baseline_snapshot,
    current_snapshot
)
```
**Returns:** `dict` — Added, removed, modified files

---

### Outcome Tagging

#### tag_outcome()
```python
agentlog.tag_outcome(
    outcome,      # "success", "failure", "partial"
    confidence,   # 0.0-1.0
    reason=None,  # Explanation
    **context
)
```

#### tag_session_outcome()
```python
agentlog.tag_session_outcome(
    session_id,
    outcome,
    confidence,
    reason=None
)
```

#### auto_tag_session()
```python
outcome = agentlog.auto_tag_session(
    session_id=None,
    confidence_threshold=0.7
)
```
Auto-detect outcome from logs.

**Returns:** `dict` with detected outcome

---

### Regression Detection

#### set_baseline()
```python
agentlog.set_baseline(
    name,          # Baseline name (e.g., "stable")
    session_id=None # Session to baseline (default: current)
)
```

#### detect_regression()
```python
regression = agentlog.detect_regression(
    baseline_name="stable",
    current_session_id=None
)
```
**Returns:** `dict` — Regression analysis

#### compare_to_baseline()
```python
comparison = agentlog.compare_to_baseline(
    baseline_name="stable"
)
```
**Returns:** `dict` — Detailed comparison

---

### Token Management

#### token_summary()
```python
summary = agentlog.token_summary()
```
**Returns:** `dict` — Aggregated LLM token usage

---

## Constants

### Outcome Values
```python
agentlog.OUTCOME_SUCCESS  # "success"
agentlog.OUTCOME_FAILURE  # "failure"
agentlog.OUTCOME_PARTIAL  # "partial"
agentlog.OUTCOME_UNKNOWN  # None
```
