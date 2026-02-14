# agentlog Future Roadmap - Lean MVP

**Status:** Planning Phase  
**Goal:** Minimal system that immediately improves AI agent debugging  
**Constraint:** Maximum 2 D1 tables, 5 event types, zero new dependencies

---

## Design Principles

1. **Ruthlessly minimal** - Remove all non-essential features
2. **Token-efficient** - Compact JSON, no verbose payloads
3. **CLI-first** - Works out-of-the-box in terminal sessions
4. **Zero dependencies** - Python stdlib only
5. **No dashboards** - Logs are for agents, not humans

---

## D1 Schema (2 Tables Maximum)

### Table 1: `agent_sessions`

Tracks agent work sessions for correlation.

```sql
CREATE TABLE agent_sessions (
  session_id TEXT PRIMARY KEY,
  start_ts REAL NOT NULL,
  end_ts REAL,
  agent_name TEXT,
  task TEXT,
  total_tokens INTEGER DEFAULT 0
);
```

### Table 2: `events`

Single unified event table for all event types.

```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  ts REAL NOT NULL,
  event_type TEXT NOT NULL,  -- failure, llm_call, tool_output, git_diff, decision
  payload TEXT NOT NULL,      -- JSON blob with event-specific data
  FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id)
);

CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_ts ON events(ts);
```

---

## Event Types (5 Maximum)

### 1. `failure` - Enhanced Failure Context

**What:** Capture exception with locals at failure point only (bottom frame)  
**Why:** Agents need to see actual runtime values when code fails  
**Inline Redaction:** API keys/tokens redacted before storage

```json
{
  "event_type": "failure",
  "id": "fail_abc123",
  "session_id": "sess_xyz789",
  "ts": 1771090420.123,
  "error": {
    "type": "ValueError",
    "msg": "Invalid confidence: 1.5"
  },
  "location": {
    "file": "main.py",
    "line": 42,
    "function": "process_skill"
  },
  "locals": {
    "confidence": {"t": "float", "v": 1.5},
    "threshold": {"t": "float", "v": 1.0},
    "user_id": {"t": "str", "v": "u_123"},
    "api_key": {"t": "str", "v": "***REDACTED***"}
  }
}
```

### 2. `llm_call` - Token Usage Tracking

**What:** Log LLM calls with token counts and session aggregation  
**Why:** Agents need to track cost and context window usage  
**Enhancement:** Add session_id to existing log_llm_call()

```json
{
  "event_type": "llm_call",
  "id": "llm_5c0cec57",
  "session_id": "sess_xyz789",
  "ts": 1771090420.354,
  "call_id": "5c0cec57",
  "model": "gpt-4",
  "tokens_in": 1250,
  "tokens_out": 450,
  "tokens_total": 1700,
  "duration_ms": 2340.5,
  "prompt": {"t": "str", "v": "Fix bug in process_skill", "truncated": 250},
  "response": {"t": "str", "v": "The issue is...", "truncated": 500}
}
```

### 3. `tool_output` - Isolated stdout/stderr

**What:** Capture tool execution output streams separately  
**Why:** Debug tool failures without mixing with agent logs  
**Limit:** Truncate at 10KB per stream

```json
{
  "event_type": "tool_output",
  "id": "tool_8c28c2ab",
  "session_id": "sess_xyz789",
  "ts": 1771090420.567,
  "call_id": "8c28c2ab",
  "tool": "run_tests",
  "stdout": "test_process_skill PASSED\ntest_validate FAILED\n",
  "stderr": "AssertionError: Expected [0,1], got 1.5\n",
  "exit_code": 1,
  "duration_ms": 234.5
}
```

### 4. `git_diff` - Lightweight Change Tracking

**What:** Capture git diff output between agent turns  
**Why:** Show what changed without complex workspace tracking  
**Limit:** First 50 lines of diff only

```json
{
  "event_type": "git_diff",
  "id": "diff_def456",
  "session_id": "sess_xyz789",
  "ts": 1771090420.789,
  "turn_number": 5,
  "files_changed": 2,
  "lines_added": 8,
  "lines_removed": 3,
  "diff": "diff --git a/src/main.py b/src/main.py\n@@ -42,1 +42,3 @@\n-    if confidence > 1.0:\n+    if confidence < 0 or confidence > 1.0:\n+        raise ValueError(f'Must be [0,1], got {confidence}')\n",
  "truncated": false
}
```

### 5. `decision` - Control Flow Decisions (Optional)

**What:** Log branching decisions if already implemented  
**Why:** Helps agents understand why certain paths were taken  
**Note:** Only include if zero additional complexity

```json
{
  "event_type": "decision",
  "id": "dec_ghi789",
  "session_id": "sess_xyz789",
  "ts": 1771090420.234,
  "question": "Should retry failed request?",
  "answer": true,
  "reason": "error_count < 3",
  "context": {
    "error_count": {"t": "int", "v": 1},
    "max_retries": {"t": "int", "v": 3}
  }
}
```

---

## Implementation Plan

### Phase 1: Session Management (Week 1)

**Files to Modify:**
- `src/agentlog/_core.py` - Add session_id to global state
- `src/agentlog/__init__.py` - Export session functions

**New Files:**
- `src/agentlog/_session.py` - Session lifecycle (start, end, get_current)

**Functions:**
```python
def start_session(agent_name: str, task: str) -> str
def end_session() -> None
def get_session_id() -> Optional[str]
```

**Validation:** Session ID appears in all new events

---

### Phase 2: Enhanced Failure Context (Week 1-2)

**Files to Modify:**
- `src/agentlog/_failure.py` - Add inline redaction, session_id
- `src/agentlog/_describe.py` - Add redact_secrets() function

**Inline Redaction Patterns:**
```python
REDACTION_PATTERNS = [
    (r'sk-[A-Za-z0-9]{48}', 'openai_api_key'),
    (r'Bearer [A-Za-z0-9\-._~+/]+=*', 'bearer_token'),
    (r'[A-Za-z0-9]{32,}', 'generic_token'),
    (r'password["\']?\s*[:=]\s*["\']([^"\']+)', 'password')
]
```

**Validation:** Failures include session_id and redacted secrets

---

### Phase 3: Token Usage Aggregation (Week 2)

**Files to Modify:**
- `src/agentlog/_agent.py` - Add session_id parameter to log_llm_call()
- `src/agentlog/_buffer.py` - Add token_summary() function

**New Function:**
```python
def token_summary(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns:
    {
      "total_tokens": 15420,
      "by_model": {
        "gpt-4": {"calls": 12, "tokens": 14200},
        "gpt-3.5-turbo": {"calls": 3, "tokens": 1220}
      }
    }
    """
```

**Validation:** Can query total tokens for current session

---

### Phase 4: Tool Output Isolation (Week 2-3)

**Files to Modify:**
- `src/agentlog/_agent.py` - Enhance tool_call() to capture stdout/stderr

**New Files:**
- `src/agentlog/_capture.py` - Context manager for stream capture

**Implementation:**
```python
@contextmanager
def capture_output():
    """Capture stdout/stderr during tool execution"""
    import io, sys
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
```

**Validation:** Tool failures show actual output streams

---

### Phase 5: Git Diff Tracking (Week 3)

**Files to Modify:**
- None (pure addition)

**New Files:**
- `src/agentlog/_git.py` - Lightweight git diff capture

**Functions:**
```python
def log_git_diff(turn_number: int) -> None:
    """Run 'git diff' and log first 50 lines"""
    import subprocess
    result = subprocess.run(['git', 'diff'], capture_output=True, text=True)
    diff_lines = result.stdout.split('\n')[:50]
    # ... emit event
```

**Validation:** Diffs show between agent turns

---

## Files Summary

### Modified (5 files)
1. `src/agentlog/_core.py` - Session state
2. `src/agentlog/_failure.py` - Redaction + session_id
3. `src/agentlog/_describe.py` - Redaction patterns
4. `src/agentlog/_agent.py` - Session_id + output capture
5. `src/agentlog/_buffer.py` - Token aggregation

### New (3 files)
1. `src/agentlog/_session.py` - Session management (~100 lines)
2. `src/agentlog/_capture.py` - Stream capture (~50 lines)
3. `src/agentlog/_git.py` - Git diff logging (~80 lines)

**Total:** 8 files, ~230 new lines of code

---

## Success Metrics

1. **Failure debugging:** Agent can see actual variable values at crash
2. **Token awareness:** Agent knows cumulative token usage per session
3. **Tool debugging:** Agent sees what tools actually output
4. **Change visibility:** Agent sees what files changed between turns
5. **Zero friction:** Works immediately in CLI with `AGENTLOG=true`

---

## What We're NOT Building

❌ Full stack trace with all frames  
❌ Per-file workspace snapshots  
❌ Redaction audit tables  
❌ Multi-language support  
❌ Dashboards or UI  
❌ SaaS or cloud services  
❌ Complex diff engines  
❌ AST-based analysis  
❌ Enterprise features  

---

## D1 Integration (Optional)

If using Cloudflare D1 for persistence:

```python
# src/agentlog/_d1.py (optional)
def emit_to_d1(event: Dict[str, Any]) -> None:
    """Write event to D1 if configured"""
    if not D1_ENABLED:
        return
    
    # Insert into events table
    cursor.execute(
        "INSERT INTO events (id, session_id, ts, event_type, payload) VALUES (?, ?, ?, ?, ?)",
        (event['id'], event['session_id'], event['ts'], event['event_type'], json.dumps(event))
    )
```

**Note:** D1 integration is optional. Default is JSONL file output.

---

## CLI Usage

```bash
# Start agent session
export AGENTLOG=true
python -c "import agentlog; agentlog.start_session('cursor', 'fix validation bug')"

# Run your code (failures auto-captured)
python main.py

# Check token usage
python -c "import agentlog; print(agentlog.token_summary())"

# End session
python -c "import agentlog; agentlog.end_session()"

# View logs
cat .agentlog/session_*.jsonl | jq 'select(.event_type=="failure")'
```

---

## Timeline

- **Week 1:** Session management + enhanced failures
- **Week 2:** Token aggregation + tool output capture
- **Week 3:** Git diff tracking + integration testing
- **Week 4:** Documentation + examples

**Total:** 4 weeks to production-ready MVP

---

## Next Steps

1. Review and approve this roadmap
2. Create GitHub issues for each phase
3. Implement Phase 1 (sessions + failures)
4. Validate with real agent debugging scenarios
5. Iterate based on feedback

---

**Last Updated:** 2026-02-14  
**Status:** Awaiting approval
