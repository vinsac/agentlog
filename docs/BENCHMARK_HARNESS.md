# AgentLog Benchmark Harness

This document explains the reproducible benchmark harness for measuring:

- iterations to fix
- time to generate a fix
- first-try success rate

## Script

- `examples/benchmark_fix_iterations.py`

## What it does

The harness runs deterministic synthetic crash scenarios and captures failures through AgentLog:

1. ValueError range violation
2. KeyError missing key
3. AttributeError None access

For each run, it:

- starts a session
- triggers a controlled crash
- captures structured failure context
- calls `fix_this_crash()`
- validates the suggested fix with scenario-specific checks
- records:
  - `iterations_to_fix`
  - `time_to_fix_ms`
  - `first_try_success`

## Run

```bash
python3 examples/benchmark_fix_iterations.py --repeat 3
```

Optional output path:

```bash
python3 examples/benchmark_fix_iterations.py --repeat 5 --output ./benchmark_report.json
```

## Output

The script writes a JSON report with:

- `meta`
- `summary`
- `results` (per scenario per run)

Key summary fields:

- `first_try_success_rate`
- `average_iterations_to_fix`
- `average_time_to_fix_ms`
- `improvement_vs_baseline_iterations_x`

## Reproducibility notes

- Scenarios are deterministic and local.
- Baseline without AgentLog is modeled as `5` iterations.
- If first-try validation fails, the harness records a manual fallback iteration count.

## Interpretation

Use this harness to compare branch-to-branch improvements in crash-fix loops and to track progress toward the roadmap target of reducing fix iterations.
