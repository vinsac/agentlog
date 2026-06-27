# agentlog Success Metrics

The v2 product should be measured by whether compact runtime context improves
agent-assisted debugging. Avoid unverified "10X" or guaranteed one-shot-fix
claims in public docs.

## Primary Metrics

### Time to first diagnosis

Definition: time from incident detection to a plausible root-cause hypothesis.

Measure:

- without agentlog: engineer or agent starts from logs, traceback, and source
- with agentlog: engineer or agent starts from `get_debug_context()`

Target:

- lower median time to first diagnosis on benchmark and beta-team incidents

### Agent turns to valid patch

Definition: number of agent interactions from first handoff to a patch that
passes the relevant tests.

Measure:

- number of prompts/replies before the patch is accepted
- whether the agent asked for additional logs, inputs, or reproduction context

Target:

- fewer turns with agentlog context than with raw logs or traceback alone

### Tokens consumed during debugging

Definition: total input and output tokens spent from incident handoff to accepted
patch or diagnosis.

Measure:

- context bundle tokens
- follow-up debugging prompts
- agent responses

Target:

- lower total token use than workflows based on raw logs or full traces

### Cannot-reproduce rate

Definition: percentage of incidents where debugging stalls because the runtime
state cannot be reconstructed.

Measure:

- incidents marked "cannot reproduce"
- incidents requiring manual log scraping
- incidents requiring extra instrumentation after failure

Target:

- fewer cannot-reproduce outcomes for instrumented services

### Handoff time

Definition: time for an on-call engineer to create a useful coding-agent task
from a production failure.

Measure:

- manual collection time
- bundle export time
- amount of context copied from external tools

Target:

- one bounded incident bundle attached to the task or ticket

## Measurement Template

```python
import time
import agentlog


def record_debug_handoff(error, request_id):
    started = time.time()

    agentlog.log_error("request failed", error, request_id=request_id)
    context = agentlog.get_debug_context(max_tokens=4000)

    return {
        "handoff_seconds": time.time() - started,
        "context_chars": len(context),
        "context_tokens_estimate": len(context) // 4,
        "request_id": request_id,
        "error_type": type(error).__name__,
    }
```

## Reporting Template

For each benchmark or beta-team incident, record:

- incident type
- baseline workflow used for comparison
- whether agentlog context was available
- time to first diagnosis
- agent turns to valid patch
- tokens consumed
- tests run
- whether additional logs were requested
- final outcome

## Product Guardrail

If a proposed feature cannot plausibly improve one of these metrics, it should
not be part of the core v2 product. It may still belong in an adapter, example,
or experimental workflow.
