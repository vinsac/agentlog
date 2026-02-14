"""
Tests for OpenTelemetry bridge module (Phase 4).
"""

import pytest
import json
from agentlog._otel import (
    to_otlp_logs,
    to_otlp_spans,
    export_otlp_json,
    export_spans_json,
    _convert_to_otel_attributes,
    _map_severity,
    _to_otel_value,
)


class TestSeverityMapping:
    """Test severity level mapping."""
    
    def test_map_severity_levels(self):
        """Test severity mapping."""
        assert _map_severity("debug") == 5
        assert _map_severity("info") == 9
        assert _map_severity("warn") == 13
        assert _map_severity("error") == 17
        assert _map_severity("fatal") == 21
        assert _map_severity("unknown") == 9  # Default


class TestOtelValueConversion:
    """Test OTEL value conversion."""
    
    def test_string_value(self):
        """Convert string."""
        result = _to_otel_value("test")
        assert result == {"stringValue": "test"}
    
    def test_bool_value(self):
        """Convert bool."""
        result = _to_otel_value(True)
        assert result == {"boolValue": True}
    
    def test_int_value(self):
        """Convert int."""
        result = _to_otel_value(42)
        assert result == {"intValue": "42"}
    
    def test_float_value(self):
        """Convert float."""
        result = _to_otel_value(3.14)
        assert result == {"doubleValue": 3.14}


class TestAttributeConversion:
    """Test attribute conversion."""
    
    def test_convert_error_entry(self):
        """Convert error entry."""
        entry = {
            "tag": "error",
            "error": {"type": "ValueError", "msg": "test error"},
            "fn": "process_data"
        }
        
        attrs = _convert_to_otel_attributes(entry)
        
        assert attrs["agentlog.tag"] == "error"
        assert attrs["error.type"] == "ValueError"
        assert attrs["error.message"] == "test error"
        assert attrs["code.function"] == "process_data"
    
    def test_convert_llm_entry(self):
        """Convert LLM entry."""
        entry = {
            "tag": "llm",
            "model": "gpt-4",
            "tokens_in": 100,
            "tokens_out": 50,
            "ms": 250.5
        }
        
        attrs = _convert_to_otel_attributes(entry)
        
        assert attrs["agentlog.tag"] == "llm"
        assert attrs["llm.model"] == "gpt-4"
        assert attrs["llm.tokens.input"] == 100
        assert attrs["llm.tokens.output"] == 50
        assert attrs["llm.duration_ms"] == 250.5


class TestOtlpLogs:
    """Test OTLP logs export."""
    
    def test_to_otlp_logs_structure(self):
        """OTLP logs has correct structure."""
        entries = [
            {"tag": "info", "msg": "test", "ts": 1234567890.0, "seq": 1}
        ]
        
        otlp = to_otlp_logs(entries, {"service.name": "test-service"})
        
        assert "resourceLogs" in otlp
        assert len(otlp["resourceLogs"]) == 1
        
        resource = otlp["resourceLogs"][0]["resource"]
        assert any(a["key"] == "service.name" for a in resource["attributes"])
        
        scope_logs = otlp["resourceLogs"][0]["scopeLogs"]
        assert len(scope_logs) == 1
        
        log_records = scope_logs[0]["logRecords"]
        assert len(log_records) == 1
        
        record = log_records[0]
        assert "timeUnixNano" in record
        assert "severityNumber" in record
        assert "body" in record
    
    def test_export_otlp_json(self):
        """Export OTLP as JSON string."""
        entries = [{"tag": "error", "msg": "test", "ts": 1234567890.0}]
        
        json_str = export_otlp_json(entries)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "resourceLogs" in parsed


class TestOtlpSpans:
    """Test OTLP spans export."""
    
    def test_to_otlp_spans_structure(self):
        """OTLP spans has correct structure."""
        # This test would need mocking, so we just check structure
        otlp = to_otlp_spans("trace-123")
        
        assert "resourceSpans" in otlp
        # May be empty if no trace data
    
    def test_export_spans_json(self):
        """Export spans as JSON."""
        json_str = export_spans_json("trace-123")
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "resourceSpans" in parsed
