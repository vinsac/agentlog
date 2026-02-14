# AgentLog Success Metrics & Case Studies

Track and document the 10X improvement claims.

---

## The 10X Claim

> **AgentLog reduces debugging iterations from 5 → 1**

This document provides templates for measuring and validating this claim.

---

## Key Metrics

### Primary Metric: Fix Iterations Per Crash

**Definition:** Number of agent attempts to fix a crash from first detection to resolution.

**Measurement:**
```python
# In your debug workflow
import agentlog
import time

fix_iterations = []

def debug_crash_with_agentlog():
    """Track fix iterations with AgentLog."""
    
    agentlog.start_session("measurement", "fix iteration tracking")
    start_time = time.time()
    
    # Attempt 1: Use fix_this_crash()
    code, explanation = agentlog.fix_this_crash()
    
    # Record the attempt
    agentlog.log("fix_attempt", attempt=1, method="fix_this_crash")
    
    # Check if fix worked (you would apply and test here)
    fix_worked = test_fix(code)  # Your test function
    
    iterations = 1
    
    if not fix_worked:
        # This shouldn't happen often with AgentLog
        # But track it if it does
        iterations += manual_debug_iterations()
    
    duration = time.time() - start_time
    
    # Record metrics
    metrics = {
        "iterations": iterations,
        "duration_seconds": duration,
        "error_type": get_last_error_type(),
        "used_auto_fix": True,
        "fix_worked_first_try": fix_worked
    }
    
    agentlog.tag_outcome("success" if fix_worked else "failure", 1.0)
    agentlog.end_session()
    
    return metrics

# Collect metrics
metrics = debug_crash_with_agentlog()
fix_iterations.append(metrics)
```

**Target:** 80% of crashes fixed in 1 iteration

---

### Secondary Metrics

#### Time to Fix (Production)

**Definition:** Time from crash detection to deployed fix.

**Measurement:**
```python
import time

# Crash detected at 3am
crash_time = time.time()

# Agent wakes up, uses fix_this_crash()
fix_code, _ = agentlog.fix_this_crash()

# Apply fix and deploy
deploy_fix(fix_code)
deploy_time = time.time()

time_to_fix = deploy_time - crash_time
print(f"Time to fix: {time_to_fix/60:.1f} minutes")
```

**Target:** < 10 minutes for 80% of crashes

---

#### Multi-Agent Debug Time

**Definition:** Time to identify root cause in multi-agent cascade failures.

**Measurement:**
```python
# Before AgentLog: Manual trace through logs
start = time.time()

# Use cascade visualizer
summary = agentlog.get_cascade_summary()
if summary["has_cascade"]:
    print(summary["full_analysis"])
    # Root cause identified immediately

debug_time = time.time() - start

# Compare to manual debugging
manual_time_estimate = 30 * 60  # 30 minutes typical
improvement = manual_time_estimate / debug_time
print(f"Debug time improvement: {improvement:.1f}x faster")
```

**Target:** 10x faster than manual log analysis

---

#### Regression Detection Accuracy

**Definition:** Percentage of true regressions caught by validator.

**Measurement:**
```python
# Test scenarios
test_cases = [
    {"baseline": "stable_v1", "new": "broken_v2", "expected": "UNSAFE"},
    {"baseline": "stable_v1", "new": "improved_v2", "expected": "SAFE"},
]

correct = 0
total = len(test_cases)

for case in test_cases:
    result = agentlog.quick_validate(case["baseline"], case["new"])
    if result == case["expected"]:
        correct += 1

accuracy = correct / total * 100
print(f"Validation accuracy: {accuracy:.1f}%")
```

**Target:** > 90% accuracy

---

## Case Study Template

### Case Study: [Company/Project Name]

**Context:**
- Agent framework: [Cursor/Codex/Claude Code/Custom]
- Application type: [Web API/Data Pipeline/ML Service/etc.]
- Team size: [Number of developers]
- Scale: [Requests per day/Records processed/etc.]

**Before AgentLog:**
- Average debug iterations per crash: [X]
- Average time to production fix: [Y hours]
- Multi-agent debugging approach: [Manual log analysis/Shared context/etc.]
- Regression detection: [Code review/Tests/None]

**After AgentLog:**
- Average debug iterations per crash: [X]
- Average time to production fix: [Y hours]
- Multi-agent debugging approach: [fix_this_crash/visualize_agent_flow]
- Regression detection: [validate_refactoring/quick_validate]

**Measured Improvements:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Fix iterations | 5 | 1 | **5x** |
| Time to fix | 2 hours | 15 min | **8x** |
| Multi-agent debug | 30 min | 2 min | **15x** |
| Regression catch | 60% | 95% | **1.6x** |

**Specific Incidents:**

*Incident 1: [Date]*
- Error: [Type and description]
- Traditional approach: [What would have happened]
- With AgentLog: [What actually happened]
- Result: [Outcome]

*Incident 2: [Date]*
- [Same structure]

**Key Learnings:**
1. [Learning 1]
2. [Learning 2]
3. [Learning 3]

**Recommendation:**
[Would they recommend AgentLog to others? Why/why not?]

---

## Data Collection Template

### For Beta Users

```python
#!/usr/bin/env python3
"""AgentLog metrics collection for beta users."""

import json
import agentlog
from datetime import datetime
from pathlib import Path

METRICS_FILE = Path("./agentlog_metrics.jsonl")

def record_crash_metrics(error_type, iterations_to_fix, used_fix_this_crash, time_to_fix_minutes):
    """Record metrics for each crash event."""
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "iterations_to_fix": iterations_to_fix,
        "used_fix_this_crash": used_fix_this_crash,
        "time_to_fix_minutes": time_to_fix_minutes,
        "session_id": agentlog.get_session_id()
    }
    
    with open(METRICS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def generate_weekly_report():
    """Generate weekly metrics report."""
    
    if not METRICS_FILE.exists():
        return "No metrics collected yet"
    
    crashes = []
    with open(METRICS_FILE) as f:
        for line in f:
            crashes.append(json.loads(line))
    
    if not crashes:
        return "No crashes recorded"
    
    total_crashes = len(crashes)
    
    # Fix iterations
    iterations = [c["iterations_to_fix"] for c in crashes]
    avg_iterations = sum(iterations) / len(iterations)
    fixed_in_one = sum(1 for i in iterations if i == 1)
    one_shot_rate = fixed_in_one / total_crashes * 100
    
    # Time to fix
    times = [c["time_to_fix_minutes"] for c in crashes if c["time_to_fix_minutes"]]
    avg_time = sum(times) / len(times) if times else 0
    
    # Used auto-fix
    used_auto = sum(1 for c in crashes if c["used_fix_this_crash"])
    auto_usage_rate = used_auto / total_crashes * 100
    
    report = f"""
# AgentLog Weekly Metrics Report

## Summary
- Total crashes: {total_crashes}
- Fixed in 1 iteration: {fixed_in_one} ({one_shot_rate:.1f}%)
- Used fix_this_crash: {used_auto} ({auto_usage_rate:.1f}%)
- Avg iterations: {avg_iterations:.1f}
- Avg time to fix: {avg_time:.1f} minutes

## Goal Tracking
- Target: 80% fixed in 1 iteration
- Current: {one_shot_rate:.1f}%
- Status: {"✅ On track" if one_shot_rate >= 80 else "⚠️ Below target"}

## Error Types
"""
    
    # Group by error type
    from collections import Counter
    error_types = Counter(c["error_type"] for c in crashes)
    for error_type, count in error_types.most_common():
        report += f"- {error_type}: {count}\n"
    
    return report

# Run weekly report
if __name__ == "__main__":
    print(generate_weekly_report())
```

---

## Success Criteria

### Beta Validation Goals

**Phase 1: Internal Dogfooding (Week 1-2)**
- [ ] Use AgentLog on AgentLog's own codebase
- [ ] Measure fix iterations on 3+ real crashes
- [ ] Document any failures of fix_this_crash()

**Phase 2: Private Beta (Week 3-6)**
- [ ] 3 teams actively using AgentLog
- [ ] 20+ crashes processed through fix_this_crash()
- [ ] 80% one-shot fix rate achieved

**Phase 3: Public Validation (Week 7+)**
- [ ] 10+ case studies documented
- [ ] Published metrics showing 10x improvement
- [ ] Testimonials from production users

---

## Benchmark Scenarios

### Scenario 1: ValueError Range Violation

**Setup:**
```python
# Code with bug
confidence = 1.5  # Should be [0, 1]
if confidence > 0:  # Wrong check
    process(confidence)
```

**Expected AgentLog Behavior:**
1. Detect `ValueError: 1.5 out of range [0, 1]`
2. Identify `confidence` variable with value 1.5
3. Generate bounds check fix
4. **Result:** Fixed in 1 iteration

---

### Scenario 2: KeyError Missing Dictionary Key

**Setup:**
```python
data = {"name": "test"}
user_id = data["user_id"]  # Key doesn't exist
```

**Expected AgentLog Behavior:**
1. Detect `KeyError: 'user_id'`
2. Suggest `.get()` with default or `in` check
3. **Result:** Fixed in 1 iteration

---

### Scenario 3: AttributeError NoneType Access

**Setup:**
```python
user = None  # From failed lookup
name = user.name  # NoneType has no attribute 'name'
```

**Expected AgentLog Behavior:**
1. Detect `AttributeError: 'NoneType' object has no attribute 'name'`
2. Identify `user` is None
3. Generate null check fix
4. **Result:** Fixed in 1 iteration

---

## Feedback Template

For beta users to submit feedback:

```
## AgentLog Feedback

**User:** [Name/Handle]
**Date:** [YYYY-MM-DD]
**Agent Framework:** [Cursor/Codex/Claude/Windsurf/Other]

### Feature Used
- [ ] fix_this_crash()
- [ ] visualize_agent_flow()
- [ ] validate_refactoring()
- [ ] Other: _____

### Did It Work?
- [ ] Yes, worked perfectly
- [ ] Yes, but needed adjustments
- [ ] Partially
- [ ] No, didn't help

### Iterations Saved
Traditional debugging would have taken: [X] iterations
With AgentLog took: [Y] iterations
**Saved: [X-Y] iterations**

### Specifics
Error type: [ValueError/KeyError/etc.]
What happened: [Brief description]
AgentLog output: [Paste relevant output]

### Suggestions
[What would make this better?]

### Would Recommend?
[Yes/No/Maybe - why?]
```

---

## Publishing Results

When ready to publish case studies:

1. **Aggregate anonymized metrics** (no company names)
2. **Quote specific improvements** ("Reduced from 5 to 1 iteration")
3. **Include error types** that worked well
4. **Note limitations** (be honest about what doesn't work)
5. **Get permission** before using company names

---

## Next Steps

1. **Recruit beta users** with production agent systems
2. **Deploy metrics collection** script
3. **Collect 10+ incidents** with AgentLog
4. **Document case studies** using template above
5. **Publish results** when 10x claim is validated
