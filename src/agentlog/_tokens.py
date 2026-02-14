"""
Token estimation for AI context windows.

Provides better token counting than the simple char/4 heuristic.
Uses a lightweight approximation based on common tokenization patterns.
"""

import re
from typing import Any


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a string.
    
    Uses a more accurate approximation than char/4:
    - Splits on whitespace and punctuation
    - Accounts for common subword patterns
    - Handles JSON structure efficiently
    
    This is still an approximation but closer to actual tokenizers
    like tiktoken (GPT) or Claude's tokenizer.
    
    Args:
        text: String to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Quick estimate for very short strings
    if len(text) < 10:
        return max(1, len(text) // 4)
    
    # Split on whitespace and common punctuation
    # This approximates subword tokenization
    tokens = 0
    
    # Split on whitespace first
    words = text.split()
    
    for word in words:
        # Short words are usually 1 token
        if len(word) <= 4:
            tokens += 1
        # Medium words might be 1-2 tokens
        elif len(word) <= 8:
            tokens += 1 + (len(word) > 6)
        # Long words get split into subwords
        else:
            # Approximate subword tokenization
            # Every ~4-6 chars is roughly a token
            tokens += max(1, len(word) // 5)
    
    # Add tokens for common JSON structure characters
    # These are often separate tokens
    structure_chars = text.count('{') + text.count('}') + \
                     text.count('[') + text.count(']') + \
                     text.count(':') + text.count(',')
    tokens += structure_chars // 2  # Rough approximation
    
    return max(1, tokens)


def estimate_tokens_dict(data: Any) -> int:
    """
    Estimate tokens for a dictionary or JSON-serializable object.
    
    Args:
        data: Dictionary or object to estimate
        
    Returns:
        Estimated token count
    """
    import json
    try:
        text = json.dumps(data, default=str, separators=(',', ':'))
        return estimate_tokens(text)
    except Exception:
        # Fallback to string representation
        return estimate_tokens(str(data))


def fit_entries_to_budget(entries: list, max_tokens: int) -> list:
    """
    Select entries that fit within a token budget.
    
    Works backwards from most recent (most relevant) and stops
    when budget is exceeded.
    
    Args:
        entries: List of log entries (dicts)
        max_tokens: Maximum token budget
        
    Returns:
        List of entries that fit within budget (chronological order)
    """
    selected = []
    total_tokens = 0
    
    # Work backwards from most recent
    for entry in reversed(entries):
        entry_tokens = estimate_tokens_dict(entry)
        
        if total_tokens + entry_tokens > max_tokens:
            break
            
        selected.append(entry)
        total_tokens += entry_tokens
    
    # Restore chronological order
    selected.reverse()
    
    return selected
