"""
Lightweight framework adapters for agentlog.

Provides simple integration patterns for common Python frameworks
without creating hard dependencies.
"""

from typing import Any, Callable, Optional
from functools import wraps

from ._core import is_enabled
from ._api import log_http


# ---------------------------------------------------------------------------
# FastAPI Adapter
# ---------------------------------------------------------------------------

def fastapi_middleware():
    """
    Create a FastAPI middleware for automatic HTTP request/response logging.
    
    Returns:
        Middleware function for FastAPI
        
    Example:
        from fastapi import FastAPI
        from agentlog import fastapi_middleware
        
        app = FastAPI()
        app.middleware("http")(fastapi_middleware())
    """
    async def middleware(request, call_next):
        if not is_enabled():
            return await call_next(request)
        
        import time
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        log_http(
            request.method,
            str(request.url.path),
            response.status_code,
            duration_ms
        )
        
        return response
    
    return middleware


# ---------------------------------------------------------------------------
# Flask Adapter
# ---------------------------------------------------------------------------

def flask_before_request():
    """
    Flask before_request handler to store request start time.
    
    Example:
        from flask import Flask
        from agentlog import flask_before_request, flask_after_request
        
        app = Flask(__name__)
        app.before_request(flask_before_request)
        app.after_request(flask_after_request)
    """
    if not is_enabled():
        return
    
    import time
    from flask import g
    g._agentlog_start_time = time.time()


def flask_after_request(response):
    """
    Flask after_request handler to log HTTP request/response.
    
    Example:
        from flask import Flask
        from agentlog import flask_before_request, flask_after_request
        
        app = Flask(__name__)
        app.before_request(flask_before_request)
        app.after_request(flask_after_request)
    """
    if not is_enabled():
        return response
    
    import time
    from flask import g, request
    
    if hasattr(g, '_agentlog_start_time'):
        duration_ms = (time.time() - g._agentlog_start_time) * 1000
        
        log_http(
            request.method,
            request.path,
            response.status_code,
            duration_ms
        )
    
    return response


# ---------------------------------------------------------------------------
# Django Adapter
# ---------------------------------------------------------------------------

class DjangoMiddleware:
    """
    Django middleware for automatic HTTP request/response logging.
    
    Example:
        # In settings.py
        MIDDLEWARE = [
            'agentlog.DjangoMiddleware',
            # ... other middleware
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not is_enabled():
            return self.get_response(request)
        
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        log_http(
            request.method,
            request.path,
            response.status_code,
            duration_ms
        )
        
        return response


# ---------------------------------------------------------------------------
# Generic Decorator
# ---------------------------------------------------------------------------

def log_endpoint(
    method: Optional[str] = None,
    path: Optional[str] = None
):
    """
    Generic decorator for logging HTTP endpoints.
    
    Works with any framework or plain functions.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Endpoint path
        
    Example:
        @log_endpoint(method="POST", path="/api/users")
        def create_user(data):
            return {"id": 123}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not is_enabled():
                return func(*args, **kwargs)
            
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Try to extract status from result
                status = 200
                if isinstance(result, tuple) and len(result) > 1:
                    status = result[1]
                elif hasattr(result, 'status_code'):
                    status = result.status_code
                
                log_http(
                    method or "UNKNOWN",
                    path or func.__name__,
                    status,
                    duration_ms
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_http(
                    method or "UNKNOWN",
                    path or func.__name__,
                    500,
                    duration_ms
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not is_enabled():
                return await func(*args, **kwargs)
            
            import time
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                status = 200
                if isinstance(result, tuple) and len(result) > 1:
                    status = result[1]
                elif hasattr(result, 'status_code'):
                    status = result.status_code
                
                log_http(
                    method or "UNKNOWN",
                    path or func.__name__,
                    status,
                    duration_ms
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_http(
                    method or "UNKNOWN",
                    path or func.__name__,
                    500,
                    duration_ms
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ---------------------------------------------------------------------------
# ASGI/WSGI Adapters
# ---------------------------------------------------------------------------

def asgi_middleware(app):
    """
    Generic ASGI middleware for logging HTTP requests.
    
    Works with FastAPI, Starlette, and other ASGI frameworks.
    
    Example:
        from agentlog import asgi_middleware
        
        app = FastAPI()
        app = asgi_middleware(app)
    """
    async def middleware(scope, receive, send):
        if scope["type"] != "http" or not is_enabled():
            return await app(scope, receive, send)
        
        import time
        start_time = time.time()
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.time() - start_time) * 1000
            log_http(
                scope["method"],
                scope["path"],
                status_code,
                duration_ms
            )
    
    return middleware


def wsgi_middleware(app):
    """
    Generic WSGI middleware for logging HTTP requests.
    
    Works with Flask, Django, and other WSGI frameworks.
    
    Example:
        from agentlog import wsgi_middleware
        
        app = Flask(__name__)
        app.wsgi_app = wsgi_middleware(app.wsgi_app)
    """
    def middleware(environ, start_response):
        if not is_enabled():
            return app(environ, start_response)
        
        import time
        start_time = time.time()
        status_code = 200
        
        def start_response_wrapper(status, headers, exc_info=None):
            nonlocal status_code
            status_code = int(status.split()[0])
            return start_response(status, headers, exc_info)
        
        try:
            result = app(environ, start_response_wrapper)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            log_http(
                environ.get("REQUEST_METHOD", "UNKNOWN"),
                environ.get("PATH_INFO", "/"),
                status_code,
                duration_ms
            )
    
    return middleware
