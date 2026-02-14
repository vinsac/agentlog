# Project Constraints

## Purpose

Defines hard boundaries that prevent scope creep and maintain product focus.

## Technical Constraints

### Zero/Minimal Dependencies
- **Python**: Standard library only (3.9+)
- **TypeScript**: Node stdlib only (future)
- **No frameworks**: No Django, Flask, FastAPI coupling
- **No databases**: No persistent storage requirements
- **No external services**: No cloud dependencies

### Performance Requirements
- **Zero overhead when disabled**: All calls must be no-ops
- **Minimal runtime cost**: < 1ms per log call
- **Memory bounded**: Ringbuffer with configurable size (default 500)
- **No blocking I/O**: Async-friendly, non-blocking writes

### Output Format
- **Structured JSON only**: No human-readable text logs
- **Compact schema**: Short keys (`t`, `v`, `n`, `k`) for token efficiency
- **Single-line JSONL**: Greppable, parseable output
- **Deterministic**: Same input always produces same output

## Strategic Constraints

### What We Will NOT Build
- **No dashboards**: No UI, no web interfaces
- **No SaaS platform**: No hosted service, no cloud backend
- **No enterprise features**: No RBAC, SSO, audit logs
- **No APM tools**: Not competing with Datadog/New Relic
- **No distributed tracing**: Not replacing OpenTelemetry
- **No LLM tracing**: Not competing with Langfuse

### Scope Boundaries
- **Phase 1**: Python only, no multi-language abstractions
- **Development focus**: Optimize for AI debugging, not production monitoring
- **Failure-centric**: Capture runtime truth at failure boundaries
- **Token-aware**: All features must consider LLM context windows

## Design Constraints

### AI-First Principles
- **Machine-readable over human-readable**: JSON over prose
- **Token efficiency**: Minimize tokens per log entry
- **Structured data**: Type descriptors, not string dumps
- **Context export**: Built-in token-budgeted export

### Integration Constraints
- **No decorators required**: Must work with zero code changes
- **No framework coupling**: Works in any Python environment
- **No configuration files**: Environment variables only
- **Reversible**: Easy to enable/disable without code changes

## Market Constraints

### Target Market
- **Early adopters only**: AI-native developers
- **Not enterprises**: No enterprise sales motion
- **Developer-led adoption**: Bottom-up, not top-down
- **Open source first**: Community-driven development

### Validation Gates
- **Phase 1 validation required**: Prove value before Phase 2
- **Product-market pull**: Expand only after demand is clear
- **No premature optimization**: Build minimal, validate, iterate

## Anti-Patterns to Avoid

### Scope Creep Risks
- **General logging framework**: Adding human-readable formats
- **Enterprise observability**: Building monitoring dashboards
- **Multi-language overexpansion**: Supporting 10+ languages
- **Plugin systems**: Complex extensibility frameworks
- **Configuration complexity**: YAML files, config management

### Feature Bloat
- **Success path logging**: Only log failures and decisions
- **Verbose output**: Keep JSON compact and minimal
- **Framework integrations**: No Django middleware, Flask extensions
- **Cloud integrations**: No AWS/GCP/Azure connectors

## AI Agent Guidelines

- Reject any feature that violates these constraints
- Question any addition that increases complexity
- Prioritize simplicity and focus over completeness
- Validate alignment with "Agent Runtime Visibility Toolkit" vision
