# Incident Replay Workflow

This workflow operationalizes:

`JSONL trace -> crash analysis -> suggested fix -> regression validation`

## Script

- `examples/incident_replay_workflow.py`

## Prerequisites

1. AgentLog trace file exists (`AGENTLOG_FILE` or explicit path)
2. Trace contains at least one `tag=error` entry
3. (Optional) baseline + new session IDs for regression validation

## Basic replay

```bash
python3 examples/incident_replay_workflow.py --input .agentlog/sessions.jsonl
```

## Replay + validation

```bash
python3 examples/incident_replay_workflow.py \
  --input .agentlog/sessions.jsonl \
  --baseline-session sess_baseline123 \
  --new-session sess_current456 \
  --strict
```

## Output

The script writes a JSON report (default `./agentlog_incident_replay_report.json`) containing:

- parsed incident summary (type/message/location)
- detected pattern metadata
- generated fix candidate
- optional `validate_refactoring` decision payload

## Operational usage

1. Persist traces in production:
   - `AGENTLOG=true`
   - `AGENTLOG_FILE=/var/log/agentlog/sessions.jsonl`
2. Replay incidents from the collected trace file.
3. Route generated report to issue tracker or on-call runbook.
4. Validate fix against baseline before merge/deploy.
