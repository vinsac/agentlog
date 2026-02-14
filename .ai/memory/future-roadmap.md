# Future Roadmap - Lean MVP

**Purpose:** This document outlines the next evolution of agentlog from a transcript logger into an AI-native Traceability & State Engine.

**Constraint:** Ruthlessly minimal - 2 D1 tables max, 5 event types, zero new dependencies.

---

## Core Constraints

1. **Maximum 2 tables** in D1: `agent_sessions` + `events`
2. **Maximum 5 event types**: failure, llm_call, tool_output, git_diff, decision
3. **No per-file diff tables** - use git diff output only
4. **Bottom frame only** - capture locals at failure point, not full stack
5. **Inline redaction** - no audit tables
6. **Zero new dependencies** - Python stdlib only
7. **Token-efficient** - compact JSON payloads
8. **CLI-first** - works out-of-the-box
9. **No dashboards** - logs for agents, not humans
10. **Minimal files** - modify existing core files only

---

## D1 Schema (2 Tables)

### agent_sessions
- session_id (PK)
- start_ts, end_ts
- agent_name, task
- total_tokens

### events
- id (PK)
- session_id (FK)
- ts, event_type
- payload (JSON blob)

---

## Event Types (5 Maximum)

1. **failure** - Exception with locals at bottom frame (inline redaction)
2. **llm_call** - Token usage tracking with session aggregation
3. **tool_output** - Isolated stdout/stderr (10KB limit)
4. **git_diff** - Lightweight change tracking (50 lines max)
5. **decision** - Control flow decisions (optional, if zero complexity)

---

## Implementation Phases

### Phase 1: Session Management
- Add session_id to global state
- Create `_session.py` module
- Functions: start_session(), end_session(), get_session_id()

### Phase 2: Enhanced Failure Context
- Modify `_failure.py` for inline redaction
- Add redaction patterns to `_describe.py`
- Include session_id in failure events

### Phase 3: Token Usage Aggregation
- Add session_id parameter to log_llm_call()
- Create token_summary() in `_buffer.py`
- Track cumulative tokens per session

### Phase 4: Tool Output Isolation
- Enhance tool_call() to capture stdout/stderr
- Create `_capture.py` for stream capture
- Truncate at 10KB per stream

### Phase 5: Git Diff Tracking
- Create `_git.py` for lightweight diff capture
- Run 'git diff' and log first 50 lines
- Track between agent turns

---

## Files Modified/Added

**Modified (5):**
1. `_core.py` - Session state
2. `_failure.py` - Redaction + session_id
3. `_describe.py` - Redaction patterns
4. `_agent.py` - Session_id + output capture
5. `_buffer.py` - Token aggregation

**New (3):**
1. `_session.py` - Session management (~100 lines)
2. `_capture.py` - Stream capture (~50 lines)
3. `_git.py` - Git diff logging (~80 lines)

**Total:** 8 files, ~230 new lines

---

## Success Metrics

1. Agent sees actual variable values at crash
2. Agent knows cumulative token usage per session
3. Agent sees what tools actually output
4. Agent sees what files changed between turns
5. Works immediately with `AGENTLOG=true`

---

## What We're NOT Building

- Full stack trace with all frames
- Per-file workspace snapshots
- Redaction audit tables
- Multi-language support
- Dashboards or UI
- SaaS or cloud services
- Complex diff engines
- AST-based analysis
- Enterprise features

---

## Timeline

- Week 1: Sessions + enhanced failures
- Week 2: Token aggregation + tool output
- Week 3: Git diff + integration testing
- Week 4: Documentation + examples

**Total:** 4 weeks to MVP

---

## AI Agent Guidelines

When implementing this roadmap:
- Prioritize simplicity over features
- Each feature must provide immediate debugging value
- No feature should add complexity without clear ROI
- Maintain zero-dependency constraint
- Keep token efficiency as primary design goal
- Test with real agent debugging scenarios
- Remove any feature that doesn't prove essential

---

**Status:** Planning Phase  
**Last Updated:** 2026-02-14
