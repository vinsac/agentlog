"""
Tests for schema validation and exports.
"""

import json
import pytest
from agentlog._schema import (
    validate_entry,
    validate_value_descriptor,
    export_schema_json,
    export_schema_typescript,
    export_schema_go,
    SCHEMA_VERSION,
)


def test_validate_entry_valid():
    """Test validation of valid entry."""
    entry = {
        "seq": 1,
        "ts": 1234567890.0,
        "at": "main.py:42 process_skill"
    }
    
    valid, error = validate_entry(entry)
    assert valid
    assert error is None


def test_validate_entry_missing_seq():
    """Test validation fails for missing seq."""
    entry = {
        "ts": 1234567890.0,
        "at": "main.py:42 process_skill"
    }
    
    valid, error = validate_entry(entry)
    assert not valid
    assert "seq" in error


def test_validate_entry_missing_ts():
    """Test validation fails for missing ts."""
    entry = {
        "seq": 1,
        "at": "main.py:42 process_skill"
    }
    
    valid, error = validate_entry(entry)
    assert not valid
    assert "ts" in error


def test_validate_entry_missing_at():
    """Test validation fails for missing at."""
    entry = {
        "seq": 1,
        "ts": 1234567890.0
    }
    
    valid, error = validate_entry(entry)
    assert not valid
    assert "at" in error


def test_validate_entry_invalid_seq():
    """Test validation fails for invalid seq."""
    entry = {
        "seq": 0,  # Must be >= 1
        "ts": 1234567890.0,
        "at": "main.py:42 process_skill"
    }
    
    valid, error = validate_entry(entry)
    assert not valid
    assert "seq" in error


def test_validate_entry_invalid_at_format():
    """Test validation fails for invalid at format."""
    entry = {
        "seq": 1,
        "ts": 1234567890.0,
        "at": "invalid_format"  # Missing : and space
    }
    
    valid, error = validate_entry(entry)
    assert not valid
    assert "at" in error


def test_validate_entry_with_optional_fields():
    """Test validation with optional trace and span."""
    entry = {
        "seq": 1,
        "ts": 1234567890.0,
        "at": "main.py:42 process_skill",
        "trace": "abc123",
        "span": "def456"
    }
    
    valid, error = validate_entry(entry)
    assert valid
    assert error is None


def test_validate_value_descriptor_valid():
    """Test validation of valid value descriptor."""
    descriptor = {
        "t": "str",
        "v": "test"
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert valid
    assert error is None


def test_validate_value_descriptor_missing_type():
    """Test validation fails for missing type."""
    descriptor = {
        "v": "test"
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert not valid
    assert "t" in error


def test_validate_value_descriptor_with_length():
    """Test validation with length field."""
    descriptor = {
        "t": "list",
        "n": 10
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert valid


def test_validate_value_descriptor_with_keys():
    """Test validation with keys field."""
    descriptor = {
        "t": "dict",
        "k": ["name", "age", "email"]
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert valid


def test_validate_value_descriptor_with_range():
    """Test validation with range field."""
    descriptor = {
        "t": "ndarray",
        "range": [0.0, 1.0]
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert valid


def test_validate_value_descriptor_invalid_range():
    """Test validation fails for invalid range."""
    descriptor = {
        "t": "ndarray",
        "range": [0.0]  # Must have 2 elements
    }
    
    valid, error = validate_value_descriptor(descriptor)
    assert not valid
    assert "range" in error


def test_export_schema_json():
    """Test JSON schema export."""
    schema_json = export_schema_json()
    
    # Should be valid JSON
    schema = json.loads(schema_json)
    
    # Should have required fields
    assert "title" in schema
    assert "version" in schema
    assert schema["version"] == SCHEMA_VERSION
    assert "definitions" in schema
    assert "tags" in schema


def test_export_schema_json_has_all_tags():
    """Test that JSON schema includes all core and workflow tags."""
    schema_json = export_schema_json()
    schema = json.loads(schema_json)
    
    tags = schema["tags"]
    
    # Core tags
    assert "error" in tags
    assert "decision" in tags
    assert "flow" in tags
    
    # Agent workflow tags
    assert "llm" in tags
    assert "tool" in tags
    assert "prompt" in tags
    assert "response" in tags
    
    # Other tags
    assert "info" in tags
    assert "func" in tags


def test_export_schema_typescript():
    """Test TypeScript export."""
    ts_code = export_schema_typescript()
    
    # Should contain TypeScript interfaces
    assert "interface AgentlogEntry" in ts_code
    assert "interface ValueDescriptor" in ts_code
    assert "interface ErrorEntry" in ts_code
    assert "interface LLMEntry" in ts_code
    assert "interface ToolEntry" in ts_code
    
    # Should have type definitions
    assert "export type LogLevel" in ts_code
    assert "export type ImportanceLevel" in ts_code


def test_export_schema_go():
    """Test Go export."""
    go_code = export_schema_go()
    
    # Should contain Go structs
    assert "type AgentlogEntry struct" in go_code
    assert "type ValueDescriptor struct" in go_code
    assert "type ErrorEntry struct" in go_code
    assert "type LLMEntry struct" in go_code
    assert "type ToolEntry struct" in go_code
    
    # Should have JSON tags
    assert '`json:"seq"`' in go_code
    assert '`json:"ts"`' in go_code


def test_schema_version():
    """Test schema version is defined."""
    assert SCHEMA_VERSION == "1.0"
