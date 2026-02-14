# Product Strategy

## 1. Vision

agentlog exists to make runtime state visible to AI coding agents.

AI coding agents can read source code but cannot see runtime state. Agents fail because they hallucinate about execution paths, variable values, and failures. Developers increasingly rely on AI agents for debugging and refactoring. agentlog gives AI agents structured, token-efficient runtime visibility. The goal is not dashboards — it is machine-readable context export.

**Core Idea:** "Logs designed for machines to reason over, not dashboards for humans."

## 2. Market Dynamics

**Current Trends:**
- Rapid adoption of AI coding agents
- Increasing reliance on agents for debugging and code modification
- Friction caused by runtime blindness
- Existing tools focus on:
  - Human-readable logs
  - LLM call tracing
  - Enterprise observability
- There is no lightweight, language-agnostic runtime visibility layer optimized for AI reasoning

**Ideal Customer Profile (ICP):**
- Solo founders using AI coding tools
- AI-heavy startups
- Backend teams experimenting with agent-driven development
- Teams building agentic workflows

This is an early but accelerating market. We are targeting early adopters, not conservative enterprises.

## 3. Problem Statement

AI agents are blind to:
- Variable values at runtime
- Execution paths
- Decision logic
- State transitions
- Failures and stack traces in structured form

**As a result:**
- Agents loop during debugging
- Agents propose incorrect fixes
- Developers waste time re-running experiments
- Context windows overflow with noisy logs

## 4. Product Principles

**Guardrails:**
- AI-first, not human-first
- Token-efficient structured output
- Zero or minimal dependencies
- Works in development and production
- Lightweight and embeddable
- Language-agnostic design (schema first, SDK second)
- No dashboards as core product
- Not competing with enterprise APM tools

## 5. Core Feature Set (Phase 1 Focus)

**What we WILL build:**
- Structured JSON runtime events optimized for AI parsing
- Token-aware context export
- Ringbuffer memory
- Decision logging
- State diffs
- Function entry/exit tracing
- Error capture with structured metadata
- AI-friendly compact schema

**What we will NOT build yet:**
- Hosted SaaS platform
- Heavy UI dashboards
- Enterprise monitoring
- Full OpenTelemetry replacement

## 6. Roadmap

**Phase 1 – AI Debugging Foundation**
- Finalize schema
- Python + TypeScript SDKs
- Context export for agents
- Decision and flow tracing
- Runtime error structuring

**Phase 2 – Agent Workflow Optimization**
- Tool call tracing
- Prompt/response correlation
- Span grouping
- Context filtering by importance
- Better token compression strategies

**Phase 3 – Multi-language Expansion**
- Java / Scala / Go SDKs
- Unified schema validation
- Lightweight adapters for common frameworks

**Phase 4 – AI-Assisted Debugging Layer**
- Automated log summarization
- AI-ready context bundles
- Replay support
- Agent feedback loops

We expand only after product-market pull is validated.

## 7. Strategic Positioning

agentlog is:
- Infrastructure for AI-native development
- A debugging accelerator for agent workflows
- A runtime visibility layer

**NOT:**
- An enterprise logging vendor
- A monitoring dashboard product
- A cloud observability company

## 8. Success Metrics

**Early validation metrics:**
- % reduction in agent debugging loops
- Faster time-to-fix when using coding agents
- Adoption by AI-heavy developers
- Community contributions
- GitHub stars from AI-native builders
