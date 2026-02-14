# Coding Standards

## Purpose

Defines Python coding standards for agentlog to maintain simplicity and consistency.

## Python Standards

### Language Requirements
- **Python 3.9+**: Minimum version for compatibility
- **Type hints**: Use for public APIs only
- **Standard library only**: No external dependencies
- **No async required**: Support both sync and async patterns

### Naming Conventions
- **Functions**: `snake_case` (e.g., `log_error`, `get_context`)
- **Variables**: `snake_case` (e.g., `trace_id`, `buffer_size`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_BUFFER_SIZE`)
- **Private functions**: Prefix with `_` (e.g., `_summarize_value`)
- **No classes**: Functional approach, avoid OOP complexity

### Code Organization
- **Single module**: Keep all code in one file initially
- **Function order**: Public API first, private helpers last
- **Max function length**: 50 lines
- **Max file length**: 500 lines (split if exceeded)

### Documentation Requirements
- **Docstrings**: Only for public API functions
- **Format**: Simple one-line descriptions, no elaborate docs
- **No inline comments**: Code should be self-explanatory
- **README examples**: Show usage, not implementation

## Code Quality Standards

### Simplicity Rules
- **No classes**: Use functions and module-level state
- **No inheritance**: No complex type hierarchies
- **No metaclasses**: No magic, no clever tricks
- **No decorators**: Except for `@log_func` (part of API)
- **Minimal abstraction**: Prefer duplication over wrong abstraction

### Performance Standards
- **< 1ms per call**: When enabled
- **Zero cost when disabled**: No-op functions
- **No blocking I/O**: Use buffering for file writes
- **Memory bounded**: Ringbuffer prevents unbounded growth

### Testing Requirements
- **Test coverage**: Focus on public API, not internals
- **No mocking**: Test real behavior
- **Fast tests**: < 1 second total test suite
- **Deterministic**: No flaky tests

### Security Guidelines
- **No secrets in logs**: Never log credentials or tokens
- **Safe value summarization**: Truncate large values
- **Exception safety**: Never crash on bad input
- **No eval/exec**: No dynamic code execution

## Output Format Standards

### JSON Schema
- **Short keys**: `t`, `v`, `n`, `k` for token efficiency
- **Consistent types**: Same key always same type
- **No null values**: Omit keys instead of null
- **Compact format**: No pretty-printing, use `separators=(',', ':')`

### Value Descriptors
- **Type**: Always include `t` (type name)
- **Value**: Include `v` for scalars and small collections
- **Length**: Include `n` for collections
- **Keys**: Include `k` for dicts (first 5 keys)
- **Truncation**: Max 100 chars for strings, 3 items for previews

## Anti-Patterns

### Avoid
- **Classes and inheritance**: Keep it functional
- **Complex configuration**: No YAML, no config objects
- **Framework coupling**: No Django/Flask/FastAPI integration
- **Verbose output**: No human-readable formatting
- **Success path logging**: Only log failures and decisions
- **Premature optimization**: Build simple first

## AI Agent Guidelines

- Write minimal, focused code
- Prefer stdlib over external packages
- Keep functions small and single-purpose
- Optimize for token efficiency in output
- Maintain zero-dependency constraint
- Question any addition that increases complexity
