"""
Tests for Clear Winner Feature 1: fix_this_crash() - One-Shot Debugger
"""

import pytest
from agentlog._fixer import (
    _detect_valueerror_pattern,
    _detect_keyerror_pattern,
    _detect_attributeerror_pattern,
    _detect_indexerror_pattern,
    _detect_typeerror_pattern,
    _generate_fix,
    fix_this_crash,
    analyze_crash,
)


class TestValueErrorDetection:
    """Test ValueError pattern detection."""
    
    def test_detect_range_violation(self):
        """Detect 'out of range' pattern."""
        error_msg = "Confidence 1.5 out of range [0, 1]"
        locals_dict = {"confidence": {"t": "float", "v": 1.5}}
        
        result = _detect_valueerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'range_violation'
        assert result['variable'] == 'confidence'
        assert result['value'] == 1.5
        assert result['min'] == 0
        assert result['max'] == 1
    
    def test_detect_type_conversion(self):
        """Detect type conversion error."""
        error_msg = "invalid literal for int() with base 10: 'abc'"
        locals_dict = {}
        
        result = _detect_valueerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'type_conversion'
        assert result['target_type'] == 'int'


class TestKeyErrorDetection:
    """Test KeyError pattern detection."""
    
    def test_detect_missing_key(self):
        """Detect missing dictionary key."""
        error_msg = "'user_id'"
        locals_dict = {"data": {"t": "dict", "v": {"name": "test"}}}
        
        result = _detect_keyerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'missing_key'
        assert result['key'] == 'user_id'


class TestAttributeErrorDetection:
    """Test AttributeError pattern detection."""
    
    def test_detect_none_attribute(self):
        """Detect NoneType attribute access."""
        error_msg = "'NoneType' object has no attribute 'name'"
        locals_dict = {"user": {"t": "NoneType", "v": None}}
        
        result = _detect_attributeerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'none_attribute'
        assert result['attribute'] == 'name'
    
    def test_detect_wrong_type_attribute(self):
        """Detect wrong type attribute access."""
        error_msg = "'str' object has no attribute 'append'"
        locals_dict = {}
        
        result = _detect_attributeerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'wrong_type_attribute'
        assert result['object_type'] == 'str'
        assert result['attribute'] == 'append'


class TestIndexErrorDetection:
    """Test IndexError pattern detection."""
    
    def test_detect_index_out_of_range(self):
        """Detect index out of range."""
        error_msg = "list index out of range"
        locals_dict = {
            "i": {"t": "int", "v": 5},
            "items": {"t": "list", "v": [1, 2, 3]}
        }
        
        result = _detect_indexerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'index_out_of_range'


class TestTypeErrorDetection:
    """Test TypeError pattern detection."""
    
    def test_detect_operand_mismatch(self):
        """Detect type mismatch in operation."""
        error_msg = "unsupported operand type(s) for +: 'int' and 'str'"
        locals_dict = {}
        
        result = _detect_typeerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'operand_type_mismatch'
        assert result['operator'] == '+'
        assert result['type1'] == 'int'
        assert result['type2'] == 'str'
    
    def test_detect_not_callable(self):
        """Detect calling non-callable object."""
        error_msg = "'int' object is not callable"
        locals_dict = {}
        
        result = _detect_typeerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'not_callable'
        assert result['object_type'] == 'int'
    
    def test_detect_wrong_arg_count(self):
        """Detect wrong argument count."""
        error_msg = "process() takes 2 positional arguments but 3 were given"
        locals_dict = {}
        
        result = _detect_typeerror_pattern(error_msg, locals_dict)
        
        assert result is not None
        assert result['type'] == 'wrong_arg_count'
        assert result['expected'] == 2
        assert result['given'] == 3


class TestFixGeneration:
    """Test fix code generation."""
    
    def test_generate_bounds_check(self):
        """Generate bounds check fix."""
        detection = {
            'type': 'range_violation',
            'variable': 'score',
            'value': 150,
            'min': 0,
            'max': 100,
            'fix_type': 'add_bounds_check',
            'explanation': 'score is out of range'
        }
        context = {}
        
        fix_code, explanation = _generate_fix(detection, context)
        
        assert 'if not (0 <= score <= 100)' in fix_code
        assert 'score=150' in explanation
    
    def test_generate_key_fix(self):
        """Generate dict key fix."""
        detection = {
            'type': 'missing_key',
            'key': 'user_id',
            'fix_type': 'use_get_or_check',
            'explanation': "Key 'user_id' not found"
        }
        context = {}
        
        fix_code, explanation = _generate_fix(detection, context)
        
        assert '.get(' in fix_code
        assert 'user_id' in fix_code
    
    def test_generate_null_check(self):
        """Generate null check fix."""
        detection = {
            'type': 'none_attribute',
            'attribute': 'name',
            'fix_type': 'add_null_check',
            'explanation': 'Object is None'
        }
        context = {}
        
        fix_code, explanation = _generate_fix(detection, context)
        
        assert 'if obj is not None' in fix_code
        assert '.name' in fix_code


class TestFixThisCrash:
    """Test fix_this_crash() public API."""
    
    def test_fix_this_crash_no_context(self):
        """Handle no debug context."""
        # When no crash has occurred, should return appropriate message
        code, explanation = fix_this_crash()
        
        assert isinstance(code, str)
        assert isinstance(explanation, str)
    
    def test_analyze_crash_structure(self):
        """Analyze crash returns proper structure."""
        result = analyze_crash()
        
        assert 'has_error' in result
        assert isinstance(result['has_error'], bool)


class TestIntegration:
    """Integration tests for the fixer."""
    
    def test_end_to_end_detection_and_fix(self):
        """Test detection → fix generation pipeline."""
        # Simulate a range violation error
        error_msg = "Value 1.5 out of range [0.0, 1.0]"
        locals_dict = {"value": {"t": "float", "v": 1.5}}
        
        detection = _detect_valueerror_pattern(error_msg, locals_dict)
        assert detection is not None
        
        fix_code, explanation = _generate_fix(detection, {})
        assert fix_code is not None
        assert len(fix_code) > 0
        assert 'if not' in fix_code
