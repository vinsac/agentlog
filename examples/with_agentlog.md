# With agentlog: What the AI agent sees

## The Crash + agentlog Context

The agent gets the traceback **plus** the output of `get_debug_context()`:

```
# agentlog debug context (session: sess_10a491b4)
# git: main@2c53442 dirty
# tokens: 230 total (gpt-4: 150in/80out)

{"tag":"error","msg":"Rating processing crashed","err":"ValueError","err_msg":"Confidence 1.5 out of valid range [0, 1]","tb":"...normalize_score..."}

{"tag":"tool","tool":"validate_rating","args":{"confidence":{"t":"float","v":0.95},"threshold":{"t":"float","v":0.7}},"success":true}
{"tag":"tool","tool":"validate_rating","args":{"confidence":{"t":"float","v":0.45},"threshold":{"t":"float","v":0.7}},"success":true}
{"tag":"tool","tool":"validate_rating","args":{"confidence":{"t":"float","v":1.5},"threshold":{"t":"float","v":0.7}},"success":true}
```

## What The Agent Does (1 turn)

**Turn 1**: "I can see:
1. `normalize_score` crashed on confidence=1.5 (out of [0,1] range)
2. `validate_rating` was called with confidence=1.5 and returned `true` (success=true)
3. The bug is in `validate_rating` — it checks `confidence > threshold` but doesn't validate the range [0, 1]
4. Fix: add `confidence <= 1.0` check to `validate_rating`"

→ Correct fix on the first try ✅

**Total: 1 turn. Zero guessing.**

## Why It Works

| Signal | What It Tells The Agent |
|--------|------------------------|
| `err_msg: "Confidence 1.5 out of valid range [0, 1]"` | Exact failure reason |
| `tool: validate_rating, confidence: 1.5, success: true` | The validator **accepted** an invalid value |
| `git: main@2c53442 dirty` | Which code version is running |
| `tokens: 230 total` | LLM cost so far |

The agent doesn't need to read source files, add print statements, or guess. The runtime context is right there.
