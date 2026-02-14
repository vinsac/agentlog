"""
One-shot crash fixer for agentlog (Clear Winner Feature #1).

The 10X feature: Go from crash → fix in one function call.
No guessing. No iterations. Just results.
"""

import ast
import json
import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Crash Pattern Detectors
# ---------------------------------------------------------------------------

def _detect_valueerror_pattern(error_msg: str, locals_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect ValueError patterns and suggest fixes.
    
    Common patterns:
    - "X out of range [min, max]" → add bounds checking
    - "invalid literal for int()" → add type validation
    - "could not convert string to float" → add try/except or validation
    """
    patterns = [
        # Range violation: "X out of range [0, 1]"
        (r'([\d.]+)\s+out\s+of\s+(valid\s+)?range\s*\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]',
         'range_violation'),
        # Type conversion: "invalid literal for int()"
        (r'invalid\s+literal\s+for\s+(int|float)\(\)',
         'type_conversion'),
        # Enum/value not in choices
        (r'([\w]+)\s+is\s+not\s+a\s+valid\s+([\w]+)',
         'invalid_choice'),
    ]
    
    for pattern, pattern_type in patterns:
        match = re.search(pattern, error_msg, re.IGNORECASE)
        if match:
            if pattern_type == 'range_violation':
                value = float(match.group(1))
                min_val = float(match.group(3))
                max_val = float(match.group(4))
                
                # Find variable with this value
                var_name = None
                for name, desc in locals_dict.items():
                    if isinstance(desc, dict) and desc.get('v') == value:
                        var_name = name
                        break
                
                return {
                    'type': 'range_violation',
                    'variable': var_name or 'value',
                    'value': value,
                    'min': min_val,
                    'max': max_val,
                    'fix_type': 'add_bounds_check',
                    'explanation': f'{var_name or "value"}={value} is outside valid range [{min_val}, {max_val}]'
                }
            
            elif pattern_type == 'type_conversion':
                target_type = match.group(1)
                return {
                    'type': 'type_conversion',
                    'target_type': target_type,
                    'fix_type': 'add_type_validation',
                    'explanation': f'Invalid value for {target_type}() conversion'
                }
    
    return None


def _detect_keyerror_pattern(error_msg: str, locals_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect KeyError patterns and suggest fixes.
    
    Pattern: "'key'" → use .get() or check existence
    """
    # Extract key name from error message
    match = re.search(r"'([^']+)'", error_msg)
    if match:
        key = match.group(1)
        return {
            'type': 'missing_key',
            'key': key,
            'fix_type': 'use_get_or_check',
            'explanation': f"Dictionary key '{key}' not found. Use .get() or check with 'in'"
        }
    return None


def _detect_attributeerror_pattern(error_msg: str, locals_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect AttributeError patterns and suggest fixes.
    
    Pattern: "'NoneType' object has no attribute 'X'" → add null check
    Pattern: "'Type' object has no attribute 'X'" → wrong object type
    """
    none_match = re.search(r"'NoneType'\s+object\s+has\s+no\s+attribute\s+'([^']+)'", error_msg)
    if none_match:
        attr = none_match.group(1)
        return {
            'type': 'none_attribute',
            'attribute': attr,
            'fix_type': 'add_null_check',
            'explanation': f"Object is None when accessing .{attr}. Add null check."
        }
    
    type_match = re.search(r"'([^']+)'\s+object\s+has\s+no\s+attribute\s+'([^']+)'", error_msg)
    if type_match:
        obj_type = type_match.group(1)
        attr = type_match.group(2)
        return {
            'type': 'wrong_type_attribute',
            'object_type': obj_type,
            'attribute': attr,
            'fix_type': 'check_type_or_attr',
            'explanation': f"{obj_type} doesn't have .{attr}. Check object type or attribute name."
        }
    
    return None


def _detect_indexerror_pattern(error_msg: str, locals_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect IndexError patterns and suggest fixes.
    
    Pattern: "list index out of range" → check length first
    """
    if 'index out of range' in error_msg.lower():
        # Try to find the index and list in locals
        index_val = None
        list_name = None
        
        for name, desc in locals_dict.items():
            if isinstance(desc, dict):
                if desc.get('t') == 'int' and index_val is None:
                    index_val = desc.get('v')
                elif desc.get('t') in ('list', 'tuple') and list_name is None:
                    list_name = name
        
        return {
            'type': 'index_out_of_range',
            'index': index_val,
            'list': list_name,
            'fix_type': 'check_length',
            'explanation': f"Index {index_val} out of range. Check len({list_name or 'list'}) first."
        }
    
    return None


def _detect_typeerror_pattern(error_msg: str, locals_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect TypeError patterns and suggest fixes.
    
    Common patterns:
    - "unsupported operand type(s)" → type mismatch
    - "takes X positional arguments but Y were given" → wrong arg count
    - "'NoneType' object is not callable" → calling None as function
    """
    if 'unsupported operand type' in error_msg.lower():
        match = re.search(r"unsupported\s+operand\s+type\(s\)\s+for\s+(\+|-|\*|/):\s+'([^']+)'\s+and\s+'([^']+)'", error_msg)
        if match:
            op = match.group(1)
            type1 = match.group(2)
            type2 = match.group(3)
            return {
                'type': 'operand_type_mismatch',
                'operator': op,
                'type1': type1,
                'type2': type2,
                'fix_type': 'convert_types',
                'explanation': f"Can't {op} {type1} and {type2}. Convert to compatible types."
            }
    
    if 'object is not callable' in error_msg.lower():
        match = re.search(r"'([^']+)'\s+object\s+is\s+not\s+callable", error_msg)
        if match:
            obj_type = match.group(1)
            return {
                'type': 'not_callable',
                'object_type': obj_type,
                'fix_type': 'remove_call',
                'explanation': f"{obj_type} is not callable. Remove () or check variable."
            }
    
    arg_match = re.search(r"takes\s+(\d+)\s+positional\s+argument\s+but\s+(\d+)\s+were\s+given", error_msg)
    if arg_match:
        expected = int(arg_match.group(1))
        given = int(arg_match.group(2))
        return {
            'type': 'wrong_arg_count',
            'expected': expected,
            'given': given,
            'fix_type': 'fix_arg_count',
            'explanation': f"Function expects {expected} args but got {given}."
        }
    
    return None


# ---------------------------------------------------------------------------
# Fix Generators
# ---------------------------------------------------------------------------

def _generate_fix(detection: Dict[str, Any], context: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate a fix based on the detected pattern.
    
    Returns:
        (fix_code, explanation)
    """
    pattern_type = detection['type']
    fix_type = detection['fix_type']
    
    if fix_type == 'add_bounds_check':
        var = detection['variable']
        min_val = detection['min']
        max_val = detection['max']
        
        fix_code = f"""
if not ({min_val} <= {var} <= {max_val}):
    raise ValueError(f"{var} must be between {min_val} and {max_val}, got {{{var}}}")
""".strip()
        
        explanation = f"{var}={detection['value']} is outside valid range [{min_val}, {max_val}]. Add bounds check before using the value."
    
    elif fix_type == 'use_get_or_check':
        key = detection['key']
        
        fix_code = f"""
# Option 1: Use .get() with default
value = my_dict.get('{key}', default_value)

# Option 2: Check key exists
if '{key}' in my_dict:
    value = my_dict['{key}']
else:
    # handle missing key
    pass
""".strip()
        
        explanation = f"Dictionary key '{key}' doesn't exist. Use .get() with default or check key existence with 'in'."
    
    elif fix_type == 'add_null_check':
        attr = detection['attribute']
        
        fix_code = f"""
if obj is not None:
    result = obj.{attr}
else:
    # handle None case
    result = default_value
""".strip()
        
        explanation = f"Object is None when accessing .{attr}. Add null check before accessing attributes."
    
    elif fix_type == 'check_length':
        list_name = detection.get('list', 'my_list')
        index = detection.get('index', 'i')
        
        fix_code = f"""
if {index} < len({list_name}):
    value = {list_name}[{index}]
else:
    # handle index out of range
    pass
""".strip()
        
        explanation = f"Index {index} is out of range for {list_name}. Check length before accessing."
    
    elif fix_type == 'convert_types':
        type1 = detection['type1']
        type2 = detection['type2']
        
        fix_code = f"""
# Convert to compatible types before operation
if isinstance(a, str):
    a = float(a)  # or int(a)
if isinstance(b, str):
    b = float(b)  # or int(b)
result = a + b
""".strip()
        
        explanation = f"Can't operate on {type1} and {type2}. Convert to compatible numeric types first."
    
    elif fix_type == 'add_type_validation':
        target_type = detection.get('target_type', 'int')
        
        fix_code = f"""
try:
    value = {target_type}(input_value)
except (ValueError, TypeError):
    # handle invalid input
    value = default_value
""".strip()
        
        explanation = f"Invalid value for {target_type}() conversion. Add try/except or validate before converting."
    
    else:
        fix_code = "# No automatic fix available for this pattern"
        explanation = detection.get('explanation', 'Unknown error pattern')
    
    return fix_code, explanation


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fix_this_crash(
    max_attempts: int = 3,
    auto_commit: bool = False
) -> Tuple[str, str]:
    """
    Fix a crash in one shot.
    
    The 10X feature: Go from crash → fix in one function call.
    
    Args:
        max_attempts: Maximum fix attempts to generate
        auto_commit: Whether to apply the fix automatically (not implemented)
        
    Returns:
        Tuple of (fix_code, explanation)
        
    Example:
        >>> code, explanation = agentlog.fix_this_crash()
        >>> print(code)
        >>> # Apply the fix
    """
    from ._buffer import get_debug_context
    from ._session import get_session_id
    
    # Get the debug context
    context_str = get_debug_context(max_tokens=4000)
    
    if not context_str:
        return "# No debug context available. Enable AGENTLOG=true and reproduce the crash.", "No crash detected"
    
    # Parse the context to find error information
    # This is a simplified version - in production would parse structured data
    error_info = None
    locals_dict = {}
    
    lines = context_str.split('\n')
    for line in lines:
        if line.startswith('{'):
            try:
                entry = json.loads(line)
                if entry.get('tag') == 'error':
                    error_info = entry
                    locals_dict = entry.get('locals', {})
                    break
            except json.JSONDecodeError:
                continue
    
    if not error_info:
        return "# No error found in recent logs.", "No crash detected"
    
    error_type = error_info.get('error', {}).get('type', '')
    error_msg = error_info.get('error', {}).get('msg', '')
    
    # Detect pattern
    detection = None
    
    if error_type == 'ValueError':
        detection = _detect_valueerror_pattern(error_msg, locals_dict)
    elif error_type == 'KeyError':
        detection = _detect_keyerror_pattern(error_msg, locals_dict)
    elif error_type == 'AttributeError':
        detection = _detect_attributeerror_pattern(error_msg, locals_dict)
    elif error_type == 'IndexError':
        detection = _detect_indexerror_pattern(error_msg, locals_dict)
    elif error_type == 'TypeError':
        detection = _detect_typeerror_pattern(error_msg, locals_dict)
    
    if detection:
        fix_code, explanation = _generate_fix(detection, error_info)
        
        # Add context header
        full_fix = f"""# Fix for {error_type}: {error_msg[:50]}
# Location: {error_info.get('file', 'unknown')}:{error_info.get('line', '?')}
# 
# Root cause: {explanation}
#
{fix_code}
"""
        return full_fix, explanation
    else:
        return f"# No pattern detected for {error_type}. Manual debugging required.", f"Error: {error_msg}"


def analyze_crash(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a crash and return detailed diagnostic information.
    
    Args:
        session_id: Session to analyze (default: current)
        
    Returns:
        Dict with crash analysis
    """
    from ._correlation import correlate_error
    from ._buffer import get_debug_context
    from ._session import get_session_id
    
    if session_id is None:
        session_id = get_session_id()
    
    # Get error context
    context_str = get_debug_context(max_tokens=4000)
    
    error_info = None
    for line in context_str.split('\n'):
        if line.startswith('{'):
            try:
                entry = json.loads(line)
                if entry.get('tag') == 'error':
                    error_info = entry
                    break
            except:
                continue
    
    if not error_info:
        return {
            'has_error': False,
            'message': 'No error found in recent logs'
        }
    
    # Get correlation info
    correlation = correlate_error(
        error_info.get('error', {}).get('type', 'Unknown'),
        error_info.get('file', 'unknown'),
        error_info.get('line', 0)
    )
    
    return {
        'has_error': True,
        'error_type': error_info.get('error', {}).get('type'),
        'error_message': error_info.get('error', {}).get('msg'),
        'location': {
            'file': error_info.get('file'),
            'line': error_info.get('line'),
            'function': error_info.get('fn')
        },
        'is_new_error': correlation.get('is_new', True),
        'times_seen_before': correlation.get('times_seen_before', 0),
        'variables_at_crash': list(error_info.get('locals', {}).keys()),
        'suggested_fix': fix_this_crash()[0] if error_info else None
    }
