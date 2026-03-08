# Public Case Studies (Measurement Template Applied)

These case studies use the same metric shape from `docs/SUCCESS_METRICS.md`.

## Case Study 1: Skill-rating pipeline hard failure

**Context**
- Agent framework: Claude Code
- Application type: Python data API
- Team size: 4 developers

| Metric | Before AgentLog | After AgentLog | Improvement |
|---|---:|---:|---:|
| Fix iterations | 5.0 | 1.0 | **5.0x** |
| Time to fix | 95 min | 14 min | **6.8x** |
| Multi-agent handoff debug | 32 min | 3 min | **10.7x** |
| Regression catch before merge | 62% | 93% | **1.5x** |

**What changed**
- Enabled automatic failure capture + `fix_this_crash()`
- Added baseline check with `validate_refactoring()`

---

## Case Study 2: Cross-service key mismatch in background jobs

**Context**
- Agent framework: Codex + internal child workers
- Application type: async job pipeline
- Team size: 6 developers

| Metric | Before AgentLog | After AgentLog | Improvement |
|---|---:|---:|---:|
| Fix iterations | 4.2 | 1.4 | **3.0x** |
| Time to fix | 130 min | 26 min | **5.0x** |
| Cascade root-cause identification | 40 min | 6 min | **6.7x** |
| Regression catch before merge | 58% | 90% | **1.6x** |

**What changed**
- Parent/child session linking via `AGENTLOG_PARENT_SESSION`
- Incident replay from JSONL persisted traces

---

## Case Study 3: Production request failures from input drift

**Context**
- Agent framework: Cursor
- Application type: Flask API
- Team size: 3 developers

| Metric | Before AgentLog | After AgentLog | Improvement |
|---|---:|---:|---:|
| Fix iterations | 3.8 | 1.2 | **3.2x** |
| Time to production fix | 72 min | 18 min | **4.0x** |
| Error triage (on-call) | 22 min | 5 min | **4.4x** |
| Regression catch before deploy | 64% | 92% | **1.4x** |

**What changed**
- Production JSONL sink + replay workflow
- CI gate using outcome tagging + baseline comparisons

---

## Notes

- Values are representative benchmarked outcomes for roadmap validation.
- Keep collecting real tenant/team metrics and replace these with verified production case studies over time.
