"""
Redaction policies for runtime context.

The descriptor layer calls into this module before values are emitted or handed
to agents. Defaults are intentionally conservative and dependency-free.
"""

import re
from typing import Any, Dict, Iterable, List, Optional, Pattern, Tuple


_DEFAULT_SECRET_FIELD_HINTS = {
    "api_key",
    "apikey",
    "authorization",
    "auth_token",
    "bearer",
    "client_secret",
    "cookie",
    "credential",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "session_token",
    "token",
}

_DEFAULT_PII_FIELD_HINTS = {
    "email",
    "phone",
    "ssn",
}

_DEFAULT_PATTERNS: List[Tuple[Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OPENAI_API_KEY"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "BEARER_TOKEN"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "GITHUB_TOKEN"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_ACCESS_KEY"),
    (re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"\s,}]+)"), "PASSWORD"),
]

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

_deny_fields = set(_DEFAULT_SECRET_FIELD_HINTS)
_pii_fields = set(_DEFAULT_PII_FIELD_HINTS)
_allow_fields: Optional[set] = None
_patterns = list(_DEFAULT_PATTERNS)
_redact_pii = True


def reset_redaction() -> None:
    """Reset redaction configuration to defaults."""
    global _deny_fields, _pii_fields, _allow_fields, _patterns, _redact_pii
    _deny_fields = set(_DEFAULT_SECRET_FIELD_HINTS)
    _pii_fields = set(_DEFAULT_PII_FIELD_HINTS)
    _allow_fields = None
    _patterns = list(_DEFAULT_PATTERNS)
    _redact_pii = True


def configure_redaction(
    *,
    deny_fields: Optional[Iterable[str]] = None,
    allow_fields: Optional[Iterable[str]] = None,
    pii_fields: Optional[Iterable[str]] = None,
    patterns: Optional[Iterable[str]] = None,
    redact_pii: Optional[bool] = None,
) -> None:
    """
    Configure field and pattern redaction.

    Args:
        deny_fields: Field names or substrings to redact.
        allow_fields: If set, only these field names can keep scalar values.
        pii_fields: Field names or substrings treated as PII.
        patterns: Additional regular expressions to redact.
        redact_pii: Enable or disable default PII redaction.
    """
    global _allow_fields, _redact_pii

    if deny_fields is not None:
        _deny_fields.update(_normalize_fields(deny_fields))
    if pii_fields is not None:
        _pii_fields.update(_normalize_fields(pii_fields))
    if allow_fields is not None:
        _allow_fields = _normalize_fields(allow_fields)
    if patterns is not None:
        for pattern in patterns:
            _patterns.append((re.compile(pattern), "CUSTOM_SECRET"))
    if redact_pii is not None:
        _redact_pii = redact_pii


def redact_string(value: str, field_name: Optional[str] = None) -> str:
    """Redact sensitive content from a string."""
    if _field_is_blocked(field_name):
        return "***REDACTED_FIELD***"

    redacted = value
    for pattern, label in _patterns:
        redacted = pattern.sub(f"***{label}***", redacted)

    if _redact_pii:
        if _field_matches(field_name, _pii_fields):
            return "***REDACTED_PII***"
        redacted = _EMAIL_PATTERN.sub("***EMAIL***", redacted)

    return redacted


def sanitize(value: Any, field_name: Optional[str] = None) -> Any:
    """Recursively sanitize JSON-like data before output."""
    if _field_is_blocked(field_name):
        return "***REDACTED_FIELD***"

    if isinstance(value, str):
        return redact_string(value, field_name)
    if isinstance(value, dict):
        return {str(k): sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, field_name) for v in value]
    if isinstance(value, tuple):
        return [sanitize(v, field_name) for v in value]
    return value


def redaction_summary() -> Dict[str, Any]:
    """Return non-sensitive policy metadata for debug-context headers."""
    return {
        "deny_fields": len(_deny_fields),
        "pii_fields": len(_pii_fields),
        "allowlist_enabled": _allow_fields is not None,
        "patterns": len(_patterns),
        "redact_pii": _redact_pii,
    }


def _normalize_fields(fields: Iterable[str]) -> set:
    return {str(field).strip().lower() for field in fields if str(field).strip()}


def _field_matches(field_name: Optional[str], fields: set) -> bool:
    if not field_name:
        return False
    name = field_name.lower()
    return any(field in name for field in fields)


def _field_is_blocked(field_name: Optional[str]) -> bool:
    if not field_name:
        return False
    name = field_name.lower()
    if _allow_fields is not None and name not in _allow_fields:
        return True
    return _field_matches(name, _deny_fields)
