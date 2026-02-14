# Development Patterns

## Purpose

Defines proven patterns for agentlog development and critical anti-patterns to avoid.

## Core Patterns

### 1. Early Return Pattern

**Always check enabled flag first:**
```python
def log(msg, **ctx):
    if not _enabled:
        return
    # ... rest of implementation
```

**Why:** Zero cost when disabled, no computation waste.

### 2. Safe Value Summarization

**Always wrap in try/except:**
```python
def _summarize_value(value):
    try:
        # summarization logic
    except Exception:
        return {"t": "object", "error": "unrepresentable"}
```

**Why:** Never crash on bad input, graceful degradation.

### 3. Compact JSON Output

**Use short keys and compact format:**
```python
json.dumps(data, separators=(',', ':'))
# Not: json.dumps(data, indent=2)
```

**Why:** Token efficiency for AI agents.

### 4. Ringbuffer Memory Management

**Bounded buffer with automatic eviction:**
```python
if len(_buffer) >= _config['buffer_size']:
    _buffer.pop(0)
_buffer.append(entry)
```

**Why:** Prevents unbounded memory growth.

### 5. Module-Level State

**Use global variables, not classes:**
```python
_enabled = False
_buffer = []
_config = {}

def enable():
    global _enabled
    _enabled = True
```

**Why:** Simplicity, no OOP complexity.

## Implementation Patterns

### Error Capture Pattern

**Automatic via sys.excepthook:**
```python
def capture_failure(exc_type, exc_value, exc_traceback):
    frame = exc_traceback.tb_frame
    locals_dict = {k: _summarize_value(v) for k, v in frame.f_locals.items()}
    # emit structured error

sys.excepthook = capture_failure
```

**Why:** Zero instrumentation, works on any code.

### Value Descriptor Pattern

**Type + minimal metadata:**
```python
# Scalar
{"t": "str", "v": "value"}

# Collection
{"t": "list", "n": 100, "preview": [1, 2, 3]}

# Dict
{"t": "dict", "n": 5, "keys": ["id", "name"]}
```

**Why:** AI agents understand structure without full data dump.

### Token-Budgeted Export Pattern

**Filter and limit by token count:**
```python
def get_context(max_tokens=4000, tags=None):
    entries = _buffer[:]
    if tags:
        entries = [e for e in entries if e.get('tag') in tags]
    # estimate tokens and truncate
    return entries
```

**Why:** Fits in LLM context windows.

## Anti-Patterns

### ❌ Adding Classes

**Don't:**
```python
class Logger:
    def __init__(self):
        self.enabled = False
```

**Do:**
```python
_enabled = False

def enable():
    global _enabled
    _enabled = True
```

**Why:** Unnecessary complexity, harder to use.

### ❌ Verbose Output

**Don't:**
```python
{"type": "string", "value": "test", "length": 4}
```

**Do:**
```python
{"t": "str", "v": "test"}
```

**Why:** Token efficiency matters.

### ❌ Success Path Logging

**Don't:**
```python
log("Function started")
log("Processing item")
log("Function completed")
```

**Do:**
```python
# Only log failures or decisions
if error:
    log_error("Processing failed", error=e)
```

**Why:** Reduces noise, focuses on failures.

### ❌ Framework Coupling

**Don't:**
```python
class DjangoMiddleware:
    def process_request(self, request):
        log_http(...)
```

**Do:**
```python
# Let users call directly
log_http(method, url, status, duration)
```

**Why:** Stay framework-agnostic.

### ❌ Configuration Complexity

**Don't:**
```python
config = yaml.load('agentlog.yml')
configure(**config)
```

**Do:**
```python
# Environment variable only
if os.getenv('AGENTLOG'):
    enable()
```

**Why:** Zero-config philosophy.

### ❌ Premature Abstraction

**Don't:**
```python
class ValueSerializer:
    def serialize(self, value):
        return self.strategy.serialize(value)
```

**Do:**
```python
def _summarize_value(value):
    if isinstance(value, str):
        return {"t": "str", "v": value}
    # ...
```

**Why:** Simple and direct beats abstract and flexible.

## Testing Patterns

### Test Public API Only

**Focus on behavior, not implementation:**
```python
def test_log_when_disabled():
    disable()
    log("test")  # Should be no-op
    assert len(_buffer) == 0
```

### Test Failure Capture

**Verify automatic exception handling:**
```python
def test_unhandled_exception():
    enable()
    try:
        raise ValueError("test")
    except:
        pass
    # Verify error was captured
```

## AI Agent Guidelines

- Use these patterns consistently
- Reject code that violates anti-patterns
- Keep implementations simple and direct
- Question any abstraction or complexity
- Optimize for readability and token efficiency
