# AI Agent Integration Guide

This guide helps AI coding agents (Cursor, Windsurf, Claude Code, Codex, Copilot) integrate with agentlog for better debugging and development.

## Quick Start for AI Agents

When you encounter a Python project using agentlog:

1. **Check if enabled**: Look for `AGENTLOG=true` in environment or `enable()` calls
2. **Read logs**: Parse `[AGENTLOG:*]` lines from stdout
3. **Use context export**: Call `get_context()` to get token-budgeted logs
4. **Understand failures**: Automatic capture provides structured error context

## Why agentlog Exists

**Problem:** You can read source code but cannot see runtime state. You hallucinate about:
- Variable values at decision points
- Execution paths taken
- Data transformations through pipelines
- Why exceptions occurred

**Solution:** agentlog provides structured, token-efficient runtime visibility designed specifically for AI consumption.

## Reading agentlog Output

### Output Format

All logs are single-line JSON with a tag prefix:

```
[AGENTLOG:tag] {"seq":1,"ts":1771089547.42,"at":"main.py:42 func",...}
```

### Parsing Strategy

```python
import json
import re

def parse_agentlog_line(line: str):
    """Parse an agentlog output line."""
    match = re.match(r'\[AGENTLOG:(\w+)\] (.+)', line)
    if match:
        tag = match.group(1)
        data = json.loads(match.group(2))
        return tag, data
    return None, None

# Example
tag, data = parse_agentlog_line('[AGENTLOG:error] {"seq":1,...}')
```

### Key Tags to Watch

| Tag | When to Use | What It Tells You |
|-----|-------------|-------------------|
| `error` | Debugging failures | Actual error with local variables |
| `decision` | Understanding control flow | Why a branch was taken |
| `flow` | Tracing data pipelines | How data transforms |
| `diff` | Understanding state changes | What actually changed |
| `check` | Finding assertion failures | Runtime validation failures |
| `func` | Performance analysis | Function timing and args |

## Common Debugging Workflows

### Workflow 1: Debugging an Exception

**User reports:** "Function `process_skill` is failing with ValueError"

**Your approach:**

1. **Look for automatic failure capture:**
   ```
   [AGENTLOG:error] {"fn":"process_skill","error":{"type":"ValueError","msg":"Invalid confidence: 1.5"},"locals":{...}}
   ```

2. **Extract actual runtime values:**
   - `confidence`: `{"t":"float","v":1.5}` (actual value, not assumption)
   - `threshold`: `{"t":"float","v":1.0}`
   - `user_id`: `{"t":"str","v":"u_123"}`

3. **Identify root cause:**
   - Confidence is 1.5, which exceeds valid range [0, 1]
   - Validation logic is correct, input data is invalid

4. **Propose fix:**
   - Add input validation before processing
   - Or fix upstream data source

**Without agentlog:** You would guess at variable values and propose fixes for the wrong problem.

### Workflow 2: Understanding Control Flow

**User asks:** "Why isn't the merge happening?"

**Your approach:**

1. **Look for decision logs:**
   ```
   [AGENTLOG:decision] {"question":"Should merge?","answer":{"t":"bool","v":false},"reason":"confidence 0.85 < threshold 0.9","ctx":{...}}
   ```

2. **See actual decision:**
   - Decision: `false` (merge did not happen)
   - Reason: confidence (0.85) below threshold (0.9)
   - Actual values: confidence=0.85, threshold=0.9

3. **Explain to user:**
   - Merge didn't happen because confidence score was too low
   - Need to either lower threshold or improve confidence calculation

**Without agentlog:** You would read the code and guess why the condition was false.

### Workflow 3: Tracing Data Transformations

**User asks:** "Why is the output wrong?"

**Your approach:**

1. **Look for flow logs:**
   ```
   [AGENTLOG:flow] {"pipeline":"skill_creation","step":"raw_input","value":{"t":"str","v":"  Python  "}}
   [AGENTLOG:flow] {"pipeline":"skill_creation","step":"normalized","value":{"t":"str","v":"python"}}
   [AGENTLOG:flow] {"pipeline":"skill_creation","step":"enriched","value":{"t":"dict",...}}
   ```

2. **Trace transformation:**
   - Input: `"  Python  "` (with spaces)
   - After normalize: `"python"` (lowercase, trimmed)
   - After enrich: `{"name":"python","category":"programming"}`

3. **Identify issue:**
   - Normalization is working correctly
   - Problem is in enrichment step (wrong category)

**Without agentlog:** You would trace through code manually, guessing at intermediate values.

## Token Budget Management

AI agents have limited context windows. agentlog helps you stay within budget.

### Using get_context()

```python
from agentlog import get_context, summary

# Get recent logs within token budget
context = get_context(max_tokens=4000, tags=["error", "decision", "check"])

# Get quick summary
s = summary()
# {"total": 142, "by_tag": {"info": 80, "error": 2}, "errors": [...]}
```

### Token Estimation

agentlog uses improved token estimation:
- Splits on whitespace and punctuation
- Accounts for JSON structure
- More accurate than simple char/4 heuristic

### Filtering Strategy

**Priority order for debugging:**
1. `error` - Failures with context
2. `check` - Failed assertions
3. `decision` - Control flow decisions
4. `flow` - Data transformations
5. `diff` - State changes

Filter by tags to get most relevant logs:
```python
# Focus on errors and decisions
context = get_context(max_tokens=2000, tags=["error", "decision"])
```

## Value Descriptors

All values use compact descriptors. Here's how to interpret them:

### Basic Types

```json
{"t": "str", "v": "Python"}        // String value
{"t": "int", "v": 42}              // Integer
{"t": "float", "v": 0.95}          // Float
{"t": "bool", "v": true}           // Boolean
{"t": "NoneType", "v": null}       // None
```

### Collections

```json
{"t": "list", "n": 3, "v": [1,2,3]}                    // Small list
{"t": "list", "n": 100, "preview": [1,2,3]}            // Large list (preview only)
{"t": "dict", "n": 5, "k": ["a","b","c"]}              // Dict with keys
{"t": "dict", "n": 3, "v": {"a":1,"b":2}}              // Small dict (full value)
```

### Arrays

```json
{"t": "ndarray", "sh": "(1000,768)", "dt": "float32", "range": [-0.5, 0.5]}
{"t": "DataFrame", "sh": "(100,10)", "cols": ["id","name","score"]}
```

### Interpreting Descriptors

- `t`: Type name (always present)
- `v`: Actual value (scalars and small collections)
- `n`: Length/count (collections)
- `k`: Keys (dicts, first 20)
- `preview`: First 3 items (large collections)
- `sh`: Shape (numpy/torch/pandas)
- `dt`: Data type (arrays)
- `range`: Min/max (numeric arrays)
- `truncated`: Original length if string was cut

## Best Practices

### DO

✅ **Parse logs systematically**
- Look for `[AGENTLOG:error]` first
- Then `[AGENTLOG:decision]` for control flow
- Then `[AGENTLOG:flow]` for data transformations

✅ **Use actual runtime values**
- Don't guess variable values
- Read from `locals`, `ctx`, or `value` fields
- Trust the runtime data over assumptions

✅ **Explain your reasoning**
- Show the user what runtime values you found
- Explain how they led to the issue
- Provide evidence-based fixes

✅ **Use token budget wisely**
- Filter by relevant tags
- Use `summary()` for quick overview
- Use `get_context()` for detailed logs

### DON'T

❌ **Don't ignore runtime data**
- If logs show `confidence=0.3`, don't assume it's `0.9`
- If logs show `user_id=null`, don't assume it exists

❌ **Don't propose fixes without evidence**
- Read the actual error context first
- Understand the actual execution path
- Base fixes on runtime reality

❌ **Don't overflow context windows**
- Use token budgets
- Filter to relevant tags
- Prioritize recent logs

❌ **Don't assume success paths**
- Just because code exists doesn't mean it executed
- Check decision logs to see which branches ran
- Verify with flow logs

## Integration Examples

### Example 1: Cursor/Copilot

When debugging in Cursor:
1. Run code with `AGENTLOG=true`
2. Copy `[AGENTLOG:*]` lines from terminal
3. Paste into Cursor chat
4. Ask: "Analyze these agentlog entries and explain the failure"

### Example 2: Claude Code

```
User: The skill creation is failing

Claude: Let me check the agentlog output...

[Reads AGENTLOG:error entry]

I can see from the runtime logs that:
- confidence = 1.5 (actual value from locals)
- threshold = 1.0
- The error is "Invalid confidence: 1.5"

The issue is that confidence exceeds the valid range [0, 1]. 
This suggests the input data is malformed. Let me check the 
data source...
```

### Example 3: Windsurf

In Windsurf workflows:
1. Enable agentlog in test environment
2. Run failing scenario
3. Export context: `get_context(max_tokens=4000, tags=["error", "decision"])`
4. Feed to debugging agent
5. Agent analyzes with actual runtime data

## Schema Reference

See [SCHEMA.md](SCHEMA.md) for complete JSON schema documentation.

## Phase 1 Features

Current features available:
- ✅ Automatic failure capture (sys.excepthook)
- ✅ Decision logging (`log_decision`)
- ✅ Flow tracing (`log_flow`)
- ✅ State diffing (`log_diff`)
- ✅ Context export (`get_context`)
- ✅ Token-aware budgeting
- ✅ Runtime error structuring

## Support

For issues or questions:
- GitHub: https://github.com/vinsac/agentlog
- Read `.ai/README.md` in the repo for AI agent guidelines
- Check `examples/` for working demonstrations

## Remember

**agentlog exists to make you better at debugging.**

You can read source code. Now you can also see runtime state. Use both together for accurate, evidence-based debugging.
