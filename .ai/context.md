# Project Context

## Domain

Agent Runtime Visibility Toolkit for AI-native development.

## Problem Statement

AI coding agents (Cursor, Windsurf, Claude Code, Codex, Copilot) can read source code but cannot see runtime state. This causes:

- Agents hallucinate about variable values and execution paths
- Debugging loops where agents propose incorrect fixes
- Context window overflow with noisy, human-readable logs
- Wasted developer time re-running experiments

**Core Gap:** No lightweight, token-efficient runtime visibility layer exists for AI agents to reason over.

## Target Users

- Solo founders using AI coding tools for rapid development
- AI-heavy startups building with agent-driven workflows
- Backend teams experimenting with AI-assisted debugging
- Developers building agentic applications

**Not targeting:** Conservative enterprises, traditional ops teams, or dashboard-focused organizations.

## Success Metrics

- % reduction in agent debugging loops (primary)
- Faster time-to-fix when using coding agents
- Adoption by AI-native developers
- Community contributions from agent users
- GitHub stars from AI-first builders

## What This Is NOT

- Not a general logging framework (structlog, loguru)
- Not an enterprise observability platform (Datadog, New Relic)
- Not LLM call tracing (Langfuse, LangSmith)
- Not distributed tracing infrastructure (OpenTelemetry)
- Not a dashboard or monitoring product

## AI Agent Guidelines

- This is a failure-boundary runtime truth layer for AI agents
- Optimize for token efficiency, not human readability
- Focus on what agents cannot infer from static code analysis
- Maintain zero/minimal dependencies
- Stay lightweight and embeddable
