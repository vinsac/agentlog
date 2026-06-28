# How To Use agentlog

agentlog is for one workflow: turning runtime behavior into a compact, redacted
debug bundle for a coding agent.

It is useful when the runtime has the facts but the agent needs a smaller,
safer, more structured artifact.

## Positioning

Use this sentence:

> agentlog turns live runtime behavior into compact, redactable debug context
> that coding agents can actually use.

Shorter:

> agentlog is a context compiler for debugging agents.

Do not position it as a logging platform, trace backend, dashboard, prompt
manager, eval suite, or autonomous fixing system.

## Basic Setup

```bash
export AGENTLOG=true
export AGENTLOG_INCIDENT_STORE=.agentlog/incidents.jsonl
export AGENTLOG_INCIDENT_STORE_MAX_BYTES=52428800
```

```python
import agentlog

agentlog.configure_redaction(
    deny_fields=["authorization", "api_key", "password"],
    pii_fields=["email", "phone"],
)
agentlog.configure_incident_store(".agentlog/incidents.jsonl", max_bytes=52_428_800)
```

## Use Case 1: Crash To Agent Context

```python
import agentlog

def handle_request(request_id: str, payload: dict) -> dict:
    incident_id = f"inc_{request_id}"
    agentlog.start_session("checkout-api", f"request {request_id}")

    try:
        return authorize_payment(payload)
    except Exception as error:
        agentlog.log_error(
            "authorization failed",
            error,
            request_id=request_id,
            incident_id=incident_id,
            payload_summary={"keys": list(payload.keys()), "size": len(str(payload))},
        )
        raise
    finally:
        agentlog.end_session()
```

Export for a coding agent:

```bash
agentlog incidents export inc_req_123 --tokens 4000 --format markdown
```

## Use Case 2: Bad Decision Reconstruction

```python
import agentlog

def choose_route(request_id: str, score: float, threshold: float) -> str:
    chosen = "manual_review" if score < threshold else "approve"

    agentlog.capture_decision(
        "payment_route",
        chosen,
        candidates=["approve", "manual_review"],
        score=score,
        threshold=threshold,
        reason="score below threshold" if chosen == "manual_review" else "score passed",
        request_id=request_id,
        incident_id=f"inc_{request_id}",
    )

    return chosen
```

This gives the agent the reason a system chose a path, not only the fact that a
request failed.

## Use Case 3: Flaky Tool Workflow

```python
import agentlog

def sync_customer(customer_id: str) -> None:
    incident_id = f"inc_customer_{customer_id}"
    agentlog.breadcrumb("sync started", customer_id=customer_id, incident_id=incident_id)

    try:
        response = call_crm(customer_id)
        agentlog.capture_tool_call(
            "crm.lookup",
            input={"customer_id": customer_id},
            output={"status": response.status_code},
            incident_id=incident_id,
        )
        update_local_record(response)
    except Exception as error:
        agentlog.capture_tool_call("crm.lookup", error=error, incident_id=incident_id)
        agentlog.log_error("customer sync failed", error, incident_id=incident_id)
        raise
```

Export the latest scoped bundle:

```bash
agentlog incidents export --latest --tokens 3000 --format json
```

## What The Agent Gets

The bundle includes:

- selected event lines as JSONL
- redaction metadata
- filter and scope notes
- budget usage
- selected and dropped counts
- git/session metadata when available

The goal is not exhaustive replay. The goal is the smallest safe subset that
helps the coding agent diagnose and patch the issue.
