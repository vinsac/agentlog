# Without agentlog: What the AI agent sees

## The Crash

```
Traceback (most recent call last):
  File "app.py", line 71, in main
    result = process_skill_ratings(ratings)
  File "app.py", line 49, in process_skill_ratings
    score = normalize_score(confidence)
  File "app.py", line 30, in normalize_score
    raise ValueError(
ValueError: Confidence 1.5 out of valid range [0, 1]
```

## What The Agent Does (5+ turns)

**Turn 1**: "The error is in `normalize_score`. Let me add input validation."
→ Adds `try/except` around `normalize_score` — **wrong fix** ❌

**Turn 2**: "Hmm, the error still happens. Let me check what calls `normalize_score`."
→ Reads more source code

**Turn 3**: "I see `validate_rating` is called first. Let me check if it rejects invalid values."
→ Reads `validate_rating` and notices it only checks `> threshold`

**Turn 4**: "The bug is that `validate_rating` doesn't check the upper bound. But what actual value caused this?"
→ Still guessing. Adds print statements.

**Turn 5**: "Now I can see confidence=1.5 was passed. The fix is to add range validation."
→ Finally proposes the correct fix ✅

**Total: 5 turns, reading through multiple files, adding debug prints.**
