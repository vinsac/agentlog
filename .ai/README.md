# AI Contract Layer

This folder is the AI contract for agentlog.

## Critical: Read Before Making Changes

All AI coding agents must read these files before generating code:

1. **`strategy.md`** - Product vision, market positioning, and what NOT to build
2. **`context.md`** - Problem statement, target users, and project boundaries
3. **`memory/constraints.md`** - Hard constraints and anti-patterns to avoid
4. **`coding-standards.md`** - Python standards and simplicity rules
5. **`architecture.md`** - System architecture and design principles
6. **`patterns.md`** - Proven patterns and critical anti-patterns

## What agentlog Is

**Agent Runtime Visibility Toolkit** - A failure-boundary runtime truth layer for AI coding agents.

- Makes runtime state visible to AI agents (Cursor, Windsurf, Claude Code, Codex)
- Token-efficient structured JSON output optimized for LLM context windows
- Zero/minimal dependencies, lightweight and embeddable
- Captures failures automatically with structured context

## What agentlog Is NOT

- ❌ Not a general logging framework (structlog, loguru)
- ❌ Not an enterprise observability platform (Datadog, New Relic)
- ❌ Not LLM call tracing (Langfuse, LangSmith)
- ❌ Not distributed tracing infrastructure (OpenTelemetry)
- ❌ Not a dashboard or monitoring product
- ❌ Not a SaaS platform or cloud service

## Core Principles

- **AI-first, not human-first**: Machine-readable over human-readable
- **Token efficiency**: Compact JSON with short keys (`t`, `v`, `n`, `k`)
- **Zero dependencies**: Python stdlib only
- **Failure-centric**: Capture runtime truth at failure boundaries
- **Zero cost when disabled**: All calls are no-ops
- **Simplicity**: Functions over classes, no OOP complexity

## Folder Structure

- **`strategy.md`** - Product vision, roadmap, and strategic positioning
- **`context.md`** - Domain, problem statement, and target users
- **`architecture.md`** - System architecture and component structure
- **`coding-standards.md`** - Python coding standards and quality rules
- **`patterns.md`** - Development patterns and anti-patterns
- **`agents/`** - Platform-specific configurations (Codex, Claude, Windsurf)
- **`prompts/`** - Structured prompt templates for common tasks
- **`specs/`** - Feature and PRD templates
- **`memory/`** - Decisions, constraints, roadmap, technical debt
- **`evaluation/`** - Quality benchmarks and checklists

## Scope Creep Prevention

Reject any feature that:
- Adds external dependencies
- Requires dashboards or UI
- Couples to specific frameworks
- Expands to multiple languages prematurely
- Adds configuration complexity
- Violates the "Agent Runtime Visibility Toolkit" vision

## AI Agent Guidelines

- Optimize for simplicity and focus over completeness
- Question any addition that increases complexity
- Prioritize token efficiency in all outputs
- Maintain zero-dependency constraint
- Keep architecture flat and functional
- Validate alignment with strategy.md before implementing
