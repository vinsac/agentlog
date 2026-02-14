# AgentLog Product Roadmap - Clear Winners Focus

**Status:** Strategic Pivot Complete  
**Version:** 3.0 (Focused)  
**Date:** 2026-02-14  
**Strategy:** Deep, not broad. One-shot fixes, not observability.

---

## The Winning Position

> **AgentLog = The tool that fixes production crashes in one shot.**

Not an observability platform. Not a monitoring solution. Just: **reduce debugging iterations from 5 to 1.**

---

## Clear Winner Features (Only These)

### Feature 1: `fix_this_crash()` - One-Shot Debugger ⭐

**The 10X Promise:** Go from crash → fix in one function call. No guessing. No iterations.

**API:**
```python
code, explanation = agentlog.fix_this_crash(
    max_attempts=3,
    auto_commit=True
)
```

**Why It Wins:**
- Eliminates the 3-5 debug iterations that kill agent productivity
- Captures state, analyzes root cause, generates fix, validates
- Single function call = complete solution

**Implementation:** `_fixer.py`

---

### Feature 2: Multi-Agent Flow Visualizer 🌊

**The 10X Promise:** Make multi-agent cascade debugging tractable instead of impossible.

**API:**
```python
flow = agentlog.visualize_agent_flow(
    session_id="sess_abc123",
    format="agent_readable"
)
```

**Why It Wins:**
- Current tools show individual agent traces, not emergent behavior
- Shows data flow: Agent A → Agent B → Error in Agent C
- Text-based, optimized for LLM consumption

**Implementation:** `_flow.py`

---

### Feature 3: Regression Validator ✅

**The 10X Promise:** Validate agent refactoring automatically instead of manual review.

**API:**
```python
result = agentlog.validate_refactoring(
    baseline_session="sess_stable",
    new_session="sess_refactored"
)
# Returns: safe_to_merge, confidence_score, blocking_issues
```

**Why It Wins:**
- Replaces manual review of 10K line diffs
- Opinionated safe/unsafe decision
- Clear confidence score

**Implementation:** `_validate.py`

---

## What We Delete / Deprecate

**Feature Bloat to Remove:**
- ❌ Team analytics (built, not core to 10X)
- ❌ Visual diff rendering (built, nice-to-have)
- ❌ Context pruning (built, not the 10X feature)
- ❌ Phase 4+ integrations beyond MCP (OTEL, D1 — keep but don't enhance)

**Keep but Freeze:**
- ✅ Phase 1-2 core (sessions, failures, patterns)
- ✅ MCP server (distribution channel)
- ✅ Basic regression detection (Feature 3 builds on this)

---

## Success Metrics

| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| **Fix Attempts per Crash** | 5 | 1 | Instrument `fix_this_crash()` usage |
| **Time to Fix (Production)** | 30 min | 2 min | User-reported + auto-tracked |
| **Multi-Agent Debug Time** | "Impossible" | <10 min | Synthetic benchmark |
| **Regression Detection Accuracy** | 0% | 90% | Labeled dataset testing |
| **Agent Adoption** | 0 | 3 teams | Weekly active users |

---

## Implementation Plan

### Week 1: `fix_this_crash()` MVP
- [ ] Create `_fixer.py` module
- [ ] Implement 5 most common crash pattern fixers:
  - ValueError (type/range issues)
  - KeyError (dict access)
  - AttributeError (object access)
  - IndexError (list access)
  - TypeError (function calls)
- [ ] Integration with `_failure.py` for auto-capture
- [ ] Basic validation (syntax check)
- [ ] Dogfood on AgentLog codebase

### Week 2: Multi-Agent Flow Visualizer
- [ ] Create `_flow.py` module
- [ ] Parse session correlation data
- [ ] Build text-based flow diagram
- [ ] Optimize for LLM readability
- [ ] Test with 2-3 agent scenarios

### Week 3: Regression Validator
- [ ] Create `_validate.py` module
- [ ] Build on existing `_regression.py`
- [ ] Opinionated safe/unsafe scoring algorithm
- [ ] Confidence score calculation
- [ ] Integration with git workflow

### Week 4: Integration & Polish
- [ ] Export all three from `__init__.py`
- [ ] Comprehensive tests
- [ ] Documentation with examples
- [ ] Beta user outreach

---

## Why This Wins

### Before (Current State)
```
1. Agent sees error: "ValueError in validate_score"
2. Agent guesses fix #1: "Add try/except"
3. Fix fails
4. Agent guesses fix #2: "Change validation logic"
5. Fix fails
6. Agent guesses fix #3: "Add logging"
7. Fix fails
8. Human wakes up and fixes it
```

### After (With Clear Winners)
```
1. Agent calls fix_this_crash()
2. Sees exact variable values + root cause
3. Gets validated fix in one shot
4. Crisis resolved in 2 minutes
```

**10X Factor:** 5 iterations → 1 iteration = 10X improvement

---

## Go-to-Market (Focused)

### Target
AI-heavy startups using Cursor/Claude Code for production systems.

### Message
"When your agent crashes at 3am, fix it in one shot instead of five attempts."

### Killer Demo
1. Show code crash
2. Show agent guessing 3 times, failing
3. Enable AgentLog, call `fix_this_crash()`
4. Show one-shot fix
5. "That's AgentLog."

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-14 | Pivot to "one-shot fixes" | Depth over breadth, clear 10X advantage |
| 2026-02-14 | Build only 3 features | Narrow focus, clear winners only |
| 2026-02-14 | Deprecate analytics/pruning | Nice-to-have, not 10X features |
| 2026-02-14 | Success metric = fix attempts | Measurable, directly shows value |

---

## The Path Forward

**Stop building features. Start proving 10X.**

1. Build `fix_this_crash()` MVP (Week 1)
2. Dogfood on AgentLog's own codebase
3. Find 3 beta users with production agent systems
4. Measure actual fix iteration reduction
5. Prove 5 → 1, then expand

**The market doesn't need more observability. It needs less debugging.**
