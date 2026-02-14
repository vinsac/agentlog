"""
Agent workflow optimization features.

Provides: log_llm_call, log_tool_call, log_prompt, log_response
for tracing AI agent interactions.
"""

import time
import uuid
from typing import Any, Dict, Optional
from contextlib import contextmanager

from ._core import is_enabled
from ._describe import describe
from ._emit import emit
from ._session import get_session_id
from ._capture import capture_io

_MAX_TOOL_OUTPUT = 10240


def log_llm_call(
    model: str,
    prompt: str,
    response: Optional[str] = None,
    duration_ms: Optional[float] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    **kwargs: Any
) -> str:
    """
    Log an LLM API call with prompt/response correlation.
    
    Args:
        model: Model name (e.g., "gpt-4", "claude-3-opus")
        prompt: Input prompt text
        response: Output response text (optional, can log separately)
        duration_ms: Call duration in milliseconds
        tokens_in: Input token count
        tokens_out: Output token count
        **kwargs: Additional context (temperature, max_tokens, etc.)
    
    Returns:
        Correlation ID for linking prompt and response
        
    Example:
        call_id = log_llm_call(
            "gpt-4",
            "Explain Python decorators",
            response="A decorator is...",
            duration_ms=1250.5,
            tokens_in=10,
            tokens_out=150,
            temperature=0.7
        )
    """
    if not is_enabled():
        return ""
    
    call_id = str(uuid.uuid4())[:8]
    
    data: Dict[str, Any] = {
        "call_id": call_id,
        "model": model,
        "prompt": describe(prompt),
    }

    session_id = get_session_id()
    if session_id:
        data["session_id"] = session_id
    
    if response is not None:
        data["response"] = describe(response)
    
    if duration_ms is not None:
        data["ms"] = round(duration_ms, 1)
    
    if tokens_in is not None:
        data["tokens_in"] = tokens_in
    
    if tokens_out is not None:
        data["tokens_out"] = tokens_out
    
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    
    emit("llm", data)
    return call_id


def log_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Optional[Any] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    **kwargs: Any
) -> str:
    """
    Log an AI agent tool/function call.
    
    Args:
        tool_name: Name of the tool being called
        arguments: Tool arguments/parameters
        result: Tool execution result (optional)
        duration_ms: Execution duration in milliseconds
        success: Whether the tool call succeeded
        **kwargs: Additional context
    
    Returns:
        Correlation ID for the tool call
        
    Example:
        call_id = log_tool_call(
            "search_database",
            {"query": "Python skills", "limit": 10},
            result={"count": 5, "items": [...]},
            duration_ms=45.2,
            success=True
        )
    """
    if not is_enabled():
        return ""
    
    call_id = str(uuid.uuid4())[:8]
    
    data: Dict[str, Any] = {
        "call_id": call_id,
        "tool": tool_name,
        "args": {k: describe(v) for k, v in arguments.items()},
        "success": success,
    }
    
    if result is not None:
        data["result"] = describe(result)
    
    if duration_ms is not None:
        data["ms"] = round(duration_ms, 1)
    
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    
    emit("tool", data)
    return call_id


def log_prompt(
    prompt: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Log a prompt being sent to an LLM.
    
    Use this for prompt-only logging, then log_response() separately.
    
    Args:
        prompt: The prompt text
        model: Model name (optional)
        system: System message (optional)
        **kwargs: Additional context (temperature, etc.)
    
    Returns:
        Correlation ID to link with response
        
    Example:
        prompt_id = log_prompt(
            "Explain decorators",
            model="gpt-4",
            temperature=0.7
        )
        # ... make API call ...
        log_response(prompt_id, response_text, tokens_out=150)
    """
    if not is_enabled():
        return ""
    
    prompt_id = str(uuid.uuid4())[:8]
    
    data: Dict[str, Any] = {
        "prompt_id": prompt_id,
        "prompt": describe(prompt),
    }
    
    if model:
        data["model"] = model
    
    if system:
        data["system"] = describe(system)
    
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    
    emit("prompt", data)
    return prompt_id


def log_response(
    prompt_id: str,
    response: str,
    duration_ms: Optional[float] = None,
    tokens_out: Optional[int] = None,
    **kwargs: Any
) -> None:
    """
    Log a response from an LLM, correlated with a prompt.
    
    Args:
        prompt_id: ID from log_prompt() to correlate
        response: The response text
        duration_ms: Time taken for response
        tokens_out: Output token count
        **kwargs: Additional context
        
    Example:
        prompt_id = log_prompt("Explain decorators", model="gpt-4")
        response = call_llm_api(...)
        log_response(prompt_id, response, duration_ms=1250, tokens_out=150)
    """
    if not is_enabled():
        return
    
    data: Dict[str, Any] = {
        "prompt_id": prompt_id,
        "response": describe(response),
    }
    
    if duration_ms is not None:
        data["ms"] = round(duration_ms, 1)
    
    if tokens_out is not None:
        data["tokens_out"] = tokens_out
    
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    
    emit("response", data)


@contextmanager
def llm_call(model: str, prompt: str, **kwargs: Any):
    """
    Context manager for LLM calls with automatic timing and correlation.
    
    Args:
        model: Model name
        prompt: Input prompt
        **kwargs: Additional context
        
    Yields:
        Dictionary to store response in
        
    Example:
        with llm_call("gpt-4", "Explain decorators") as call:
            response = api.chat.completions.create(...)
            call["response"] = response.choices[0].message.content
            call["tokens_out"] = response.usage.completion_tokens
    """
    if not is_enabled():
        yield {}
        return
    
    call_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    call_data = {"call_id": call_id}
    
    try:
        yield call_data
        
        duration_ms = (time.time() - start_time) * 1000
        
        data: Dict[str, Any] = {
            "call_id": call_id,
            "model": model,
            "prompt": describe(prompt),
            "ms": round(duration_ms, 1),
        }
        
        session_id = get_session_id()
        if session_id:
            data["session_id"] = session_id
        
        if "response" in call_data:
            data["response"] = describe(call_data["response"])
        
        if "tokens_in" in call_data:
            data["tokens_in"] = call_data["tokens_in"]
        
        if "tokens_out" in call_data:
            data["tokens_out"] = call_data["tokens_out"]
        
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        
        emit("llm", data)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        data = {
            "call_id": call_id,
            "model": model,
            "prompt": describe(prompt),
            "ms": round(duration_ms, 1),
            "error": {"type": type(e).__name__, "msg": str(e)},
        }

        session_id = get_session_id()
        if session_id:
            data["session_id"] = session_id
        
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        
        emit("llm", data)
        raise


@contextmanager
def tool_call(tool_name: str, arguments: Dict[str, Any], **kwargs: Any):
    """
    Context manager for tool calls with automatic timing and correlation.
    
    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        **kwargs: Additional context
        
    Yields:
        Dictionary to store result in
        
    Example:
        with tool_call("search_db", {"query": "Python"}) as call:
            results = search_database(query="Python")
            call["result"] = results
    """
    if not is_enabled():
        yield {}
        return
    
    call_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    call_data = {"call_id": call_id}
    
    # Capture IO during execution
    captured_out = ""
    captured_err = ""
    
    try:
        with capture_io() as (out_stream, err_stream):
            yield call_data
            captured_out = out_stream.getvalue()
            captured_err = err_stream.getvalue()
        
        duration_ms = (time.time() - start_time) * 1000
        
        data: Dict[str, Any] = {
            "call_id": call_id,
            "tool": tool_name,
            "args": {k: describe(v) for k, v in arguments.items()},
            "ms": round(duration_ms, 1),
            "success": True,
        }

        if captured_out or captured_err:
            data["sys"] = {}
            if captured_out:
                data["sys"]["stdout"] = captured_out[:_MAX_TOOL_OUTPUT]
                if len(captured_out) > _MAX_TOOL_OUTPUT:
                    data["sys"]["stdout_truncated"] = len(captured_out)
            if captured_err:
                data["sys"]["stderr"] = captured_err[:_MAX_TOOL_OUTPUT]
                if len(captured_err) > _MAX_TOOL_OUTPUT:
                    data["sys"]["stderr_truncated"] = len(captured_err)
        
        if "result" in call_data:
            data["result"] = describe(call_data["result"])
        
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        
        emit("tool", data)
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        data = {
            "call_id": call_id,
            "tool": tool_name,
            "args": {k: describe(v) for k, v in arguments.items()},
            "ms": round(duration_ms, 1),
            "success": False,
            "error": {"type": type(e).__name__, "msg": str(e)},
        }

        # Partial IO may have been captured before the exception;
        # include whatever was written before the crash.
        if captured_out or captured_err:
            data["sys"] = {}
            if captured_out:
                data["sys"]["stdout"] = captured_out[:_MAX_TOOL_OUTPUT]
                if len(captured_out) > _MAX_TOOL_OUTPUT:
                    data["sys"]["stdout_truncated"] = len(captured_out)
            if captured_err:
                data["sys"]["stderr"] = captured_err[:_MAX_TOOL_OUTPUT]
                if len(captured_err) > _MAX_TOOL_OUTPUT:
                    data["sys"]["stderr_truncated"] = len(captured_err)
        
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        
        emit("tool", data)
        raise
