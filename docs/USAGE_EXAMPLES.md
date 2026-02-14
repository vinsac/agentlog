# AgentLog Usage Examples

Real-world integration patterns for AI coding agents.

---

## Cursor Integration

### Setup

Add to your `.cursorrules` or project instructions:

```
When debugging crashes in this codebase:
1. Check if agentlog has captured the crash context
2. Use agentlog.fix_this_crash() to get automatic fix suggestions
3. Review the generated fix before applying
```

### Pattern 1: Automatic Crash Recovery

```python
# In your main application entry point
import agentlog

agentlog.start_session("cursor", "feature implementation")

# Your application code here
def main():
    try:
        run_feature()
    except Exception:
        # AgentLog has already captured locals automatically
        # Now get the fix
        code, explanation = agentlog.fix_this_crash()
        
        print(f"\n🔧 Auto-generated fix:\n{code}")
        print(f"\n💡 Explanation: {explanation}")
        
        # Log the fix attempt
        agentlog.log("fix_attempt", fix_code=code[:200])
        raise
    finally:
        agentlog.end_session()
```

### Pattern 2: Multi-Agent Debugging

When Cursor calls another agent (e.g., via API or subprocess):

```python
import agentlog

# Parent session (Cursor)
agentlog.start_session("cursor", "parent task")
parent_session = agentlog.get_session_id()

# When spawning child agent (Codex, GPT, etc.)
import subprocess
env = os.environ.copy()
env["AGENTLOG_PARENT_SESSION"] = parent_session

# Child will pick up parent and link sessions
result = subprocess.run(
    ["python", "child_agent.py"],
    env=env,
    capture_output=True
)

# After child completes, check for cascades
if result.returncode != 0:
    summary = agentlog.get_cascade_summary()
    if summary["has_cascade"]:
        print("🌊 Multi-agent cascade detected!")
        print(summary["full_analysis"])
        print(f"\n👉 {summary['recommendation']}")

agentlog.end_session()
```

### Pattern 3: Refactoring Validation

```python
# Before starting refactoring
agentlog.start_session("cursor", "refactor auth module")
baseline_session = agentlog.get_session_id()

# Mark current state as baseline
agentlog.set_baseline("pre-refactor", baseline_session)

# ... do refactoring work ...

# After refactoring, validate before commit
new_session = agentlog.get_session_id()
result = agentlog.validate_refactoring(baseline_session, new_session)

if result["safe_to_merge"]:
    print(f"✅ Safe to commit! Confidence: {result['confidence_score']}%")
    print("\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"  {rec}")
else:
    print(f"⚠️  Issues found (confidence: {result['confidence_score']}%)")
    print("\nBlocking issues:")
    for issue in result["blocking_issues"]:
        print(f"  ❌ {issue}")
    
    print("\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"  {rec}")
    
    # Detailed analysis
    analysis = result["detailed_analysis"]
    print(f"\n📊 Overall score: {analysis['overall_score']}/100")
    print(f"   - Error score: {analysis['component_scores']['error_score']}")
    print(f"   - Outcome score: {analysis['component_scores']['outcome_score']}")
    print(f"   - Behavior score: {analysis['component_scores']['behavior_score']}")

agentlog.end_session()
```

---

## Claude Code Integration

### Setup

Add to your Claude Code project context:

```
This project uses agentlog for debugging. Key commands:
- agentlog.fix_this_crash() — Get automatic fix for current crash
- agentlog.visualize_agent_flow() — Debug multi-agent cascades  
- agentlog.validate_refactoring(baseline, new) — Check if refactoring is safe
```

### Pattern 1: Debug Loop Reduction

```python
# Traditional: 5 iterations of guess-and-check
# With AgentLog: 1 iteration with full context

import agentlog

agentlog.start_session("claude", "debug production issue")

# Simulate or reproduce the crash
try:
    reproduce_issue()
except Exception as e:
    # Get everything in one call
    analysis = agentlog.analyze_crash()
    
    if analysis["has_error"]:
        print(f"\n🔍 Crash Analysis:")
        print(f"   Type: {analysis['error_type']}")
        print(f"   Location: {analysis['location']['file']}:{analysis['location']['line']}")
        print(f"   Times seen before: {analysis['times_seen_before']}")
        
        if analysis["is_new_error"]:
            print("   ⚠️  This is a NEW error pattern")
        else:
            print(f"   📝 Seen {analysis['times_seen_before']} times before")
        
        print(f"\n   Variables at crash: {', '.join(analysis['variables_at_crash'])}")
        
        if analysis["suggested_fix"]:
            print(f"\n💡 Suggested fix:\n{analysis['suggested_fix']}")

agentlog.end_session()
```

### Pattern 2: CI/CD Integration

```python
# In your CI pipeline (GitHub Actions, etc.)

import agentlog
import sys

agentlog.start_session("ci", f"test run {os.environ.get('GITHUB_RUN_ID', 'local')}")

# Run tests
exit_code = pytest.main(["-x", "tests/"])

# Auto-tag outcome
if exit_code == 0:
    agentlog.tag_outcome("success", 1.0, "All tests passed")
else:
    agentlog.tag_outcome("failure", 1.0, f"Tests failed with exit code {exit_code}")
    
    # In CI, we can still get fix suggestions for logged errors
    context = agentlog.get_debug_context(max_tokens=2000)
    print("\n📋 Debug context for failed run:")
    print(context)

agentlog.end_session()
sys.exit(exit_code)
```

### Pattern 3: Production Monitoring

```python
# In a long-running service

import agentlog
from flask import Flask

app = Flask(__name__)

@app.before_request
def before_request():
    agentlog.start_session("production", f"{request.method} {request.path}")

@app.after_request
def after_request(response):
    # Tag based on response status
    if response.status_code < 400:
        agentlog.tag_outcome("success", 1.0)
    elif response.status_code < 500:
        agentlog.tag_outcome("partial", 0.7, f"Client error {response.status_code}")
    else:
        agentlog.tag_outcome("failure", 1.0, f"Server error {response.status_code}")
    
    agentlog.end_session()
    return response

@app.errorhandler(Exception)
def handle_error(error):
    # Automatically captured by agentlog
    # Log additional context
    agentlog.log_error(
        "Unhandled exception in request",
        error,
        endpoint=request.endpoint,
        method=request.method,
        path=request.path
    )
    
    # Get fix suggestion (for logged errors)
    code, explanation = agentlog.fix_this_crash()
    
    # In production, you might send this to your error tracking
    # service along with the fix suggestion
    
    raise error
```

---

## Windsurf Integration

### Setup

Add to `.windsurfrules`:

```
When AgentLog is enabled (AGENTLOG=true):
- Use agentlog.fix_this_crash() after any exception
- Check agentlog.get_cascade_summary() when debugging multi-file issues
- Validate refactors with agentlog.quick_validate() before completing
```

### Pattern 1: Quick Validation

```python
# Fast feedback during development

import agentlog

# After making changes, quick check
result = agentlog.quick_validate()

if result == "SAFE":
    print("✅ Changes look good, safe to continue")
elif result == "CAUTION":
    print("⚠️  Minor changes detected, review recommended")
elif result == "REVIEW":
    print("🔍 Significant changes, please review before proceeding")
elif result == "UNSAFE":
    print("❌ Issues detected! Check recent changes")
    
    # Get detailed analysis
    detailed = agentlog.validate_refactoring(
        baseline_session=None,  # Uses "stable" baseline
        new_session=None        # Uses current session
    )
    
    print("\nDetailed breakdown:")
    for issue in detailed["blocking_issues"]:
        print(f"  • {issue}")
```

### Pattern 2: Session Correlation

```python
# When working across multiple files simultaneously

import agentlog

# Start parent session
agentlog.start_session("windsurf", "cross-file refactoring")
parent = agentlog.get_session_id()

# In file A
agentlog.start_session("windsurf_file_a", "update models", parent_session_id=parent)
# ... make changes ...
agentlog.end_session()

# In file B  
agentlog.start_session("windsurf_file_b", "update controllers", parent_session_id=parent)
# ... make changes ...
errors_in_b = agentlog.get_debug_context()
agentlog.end_session()

# Back to parent, check for cascades
agentlog.start_session("windsurf", "verify cross-file changes", parent_session_id=parent)

if errors_in_b:
    flow = agentlog.visualize_agent_flow()
    print("Checking for multi-file cascade issues:")
    print(flow)

agentlog.end_session()
```

---

## Generic Integration Patterns

### Pattern 1: The Debug Context Pattern

```python
# Export everything an AI agent needs to debug

import agentlog

def get_ai_debug_info(max_tokens=4000):
    """Export debug info optimized for AI agents."""
    
    # Get failure-prioritized context
    context = agentlog.get_debug_context(max_tokens=max_tokens)
    
    # Get fix suggestion if there's an error
    fix_code, fix_explanation = agentlog.fix_this_crash()
    
    # Check for multi-agent issues
    cascade = agentlog.get_cascade_summary()
    
    # Build complete debug package
    return {
        "context": context,
        "fix": {
            "code": fix_code,
            "explanation": fix_explanation
        },
        "cascade": cascade,
        "session_id": agentlog.get_session_id()
    }

# Use with any AI agent
debug_info = get_ai_debug_info()
# Pass debug_info to Claude/Cursor/GPT/etc.
```

### Pattern 2: The Baseline Pattern

```python
# Establish and compare baselines

import agentlog

def with_baseline(name, work_fn):
    """Run work with baseline comparison."""
    
    # Establish baseline
    agentlog.start_session("baseline", name)
    baseline_id = agentlog.get_session_id()
    agentlog.set_baseline(name, baseline_id)
    agentlog.end_session()
    
    # Do the work
    agentlog.start_session("work", name)
    try:
        result = work_fn()
        
        # Validate against baseline
        validation = agentlog.validate_refactoring(
            baseline_session=baseline_id,
            new_session=agentlog.get_session_id()
        )
        
        if not validation["safe_to_merge"]:
            print("⚠️  Work introduced regressions!")
            print(validation["blocking_issues"])
            
        return result, validation
        
    finally:
        agentlog.end_session()

# Usage
result, validation = with_baseline(
    "auth-refactor",
    lambda: refactor_auth_module()
)
```

### Pattern 3: The Error Recovery Pattern

```python
# Automatic recovery from known error patterns

import agentlog

KNOWN_ERRORS = {
    "missing_import": lambda ctx: f"import {ctx.get('module', 'unknown')}",
    "type_mismatch": lambda ctx: f"# Add type check for {ctx.get('var', 'value')}",
}

def attempt_auto_recovery():
    """Try to auto-recover from known errors."""
    
    analysis = agentlog.analyze_crash()
    
    if not analysis["has_error"]:
        return None
    
    error_type = analysis["error_type"]
    
    # Check if this is a known pattern
    if error_type in KNOWN_ERRORS:
        fix = KNOWN_ERRORS[error_type](analysis)
        
        # Log the auto-recovery attempt
        agentlog.log(
            "auto_recovery",
            error_type=error_type,
            fix_applied=fix,
            confidence="high" if analysis["times_seen_before"] > 5 else "medium"
        )
        
        return fix
    
    # Fall back to general fix suggestion
    return agentlog.fix_this_crash()[0]
```

---

## Environment Variables

```bash
# Enable agentlog
export AGENTLOG=true

# Optional: Set parent session for multi-agent chains
export AGENTLOG_PARENT_SESSION=sess_abc123

# Optional: Custom buffer size
export AGENTLOG_BUFFER_SIZE=1000

# Optional: File output
export AGENTLOG_FILE=./logs/agentlog.jsonl
```

---

## Best Practices

1. **Always use sessions** — Correlates all events in a logical unit
2. **End sessions properly** — Ensures data is flushed and tagged
3. **Use the 10X features** — They're the reason AgentLog exists
4. **Set baselines before refactoring** — Enables automatic validation
5. **Check cascades in multi-agent setups** — Finds root causes faster
6. **Export debug context to AI agents** — One function call = complete context
