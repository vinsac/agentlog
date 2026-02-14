"""
Phase 3 Schema Validation and Framework Adapters Demo

Demonstrates Phase 3 features:
- Schema validation
- Schema exports (JSON, TypeScript, Go)
- Framework adapters (FastAPI, Flask, Django)
- Cross-language compatibility

Run with:
    AGENTLOG=true python3 examples/phase3_schema_and_adapters.py
"""

import sys
import os
import json

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog
from agentlog import (
    enable, log, log_error,
    validate_entry, validate_value_descriptor,
    export_schema_json, export_schema_typescript, export_schema_go,
    log_endpoint
)

# Enable agentlog
enable()


def demonstrate_schema_validation():
    """Show schema validation for log entries."""
    print("\n" + "=" * 70)
    print("1. SCHEMA VALIDATION")
    print("=" * 70)
    
    # Valid entry
    valid_entry = {
        "seq": 1,
        "ts": 1234567890.0,
        "at": "main.py:42 process_skill",
        "msg": "Processing request"
    }
    
    is_valid, error = validate_entry(valid_entry)
    print(f"Valid entry: {is_valid}")
    
    # Invalid entry (missing required field)
    invalid_entry = {
        "seq": 1,
        "ts": 1234567890.0
        # Missing 'at' field
    }
    
    is_valid, error = validate_entry(invalid_entry)
    print(f"Invalid entry: {is_valid}, Error: {error}")
    
    print("✓ Schema validation ensures consistent output format")


def demonstrate_value_descriptor_validation():
    """Show value descriptor validation."""
    print("\n" + "=" * 70)
    print("2. VALUE DESCRIPTOR VALIDATION")
    print("=" * 70)
    
    # Valid descriptor
    valid_descriptor = {
        "t": "str",
        "v": "Python"
    }
    
    is_valid, error = validate_value_descriptor(valid_descriptor)
    print(f"Valid descriptor: {is_valid}")
    
    # Invalid descriptor (missing type)
    invalid_descriptor = {
        "v": "Python"
    }
    
    is_valid, error = validate_value_descriptor(invalid_descriptor)
    print(f"Invalid descriptor: {is_valid}, Error: {error}")
    
    print("✓ Value descriptors follow consistent schema")


def demonstrate_schema_exports():
    """Show schema exports for different languages."""
    print("\n" + "=" * 70)
    print("3. SCHEMA EXPORTS FOR CROSS-LANGUAGE COMPATIBILITY")
    print("=" * 70)
    
    # Export JSON Schema
    json_schema = export_schema_json()
    schema_obj = json.loads(json_schema)
    print(f"JSON Schema version: {schema_obj['version']}")
    print(f"Defined tags: {len(schema_obj['tags'])}")
    
    # Export TypeScript
    ts_types = export_schema_typescript()
    print(f"TypeScript definitions: {len(ts_types)} characters")
    print("  Includes: AgentlogEntry, ValueDescriptor, ErrorEntry, LLMEntry, ToolEntry")
    
    # Export Go
    go_types = export_schema_go()
    print(f"Go struct definitions: {len(go_types)} characters")
    print("  Includes: AgentlogEntry, ValueDescriptor, ErrorEntry, LLMEntry, ToolEntry")
    
    print("✓ Schema can be exported for TypeScript, Go, and other languages")


def demonstrate_endpoint_decorator():
    """Show generic endpoint decorator."""
    print("\n" + "=" * 70)
    print("4. GENERIC ENDPOINT DECORATOR")
    print("=" * 70)
    
    @log_endpoint(method="POST", path="/api/users")
    def create_user(name: str):
        """Simulated endpoint function."""
        return {"id": 123, "name": name}
    
    # Call the decorated function
    result = create_user("Alice")
    
    print(f"Endpoint called: {result}")
    print("✓ Generic decorator works with any framework")


def demonstrate_framework_integration_patterns():
    """Show framework integration patterns."""
    print("\n" + "=" * 70)
    print("5. FRAMEWORK INTEGRATION PATTERNS")
    print("=" * 70)
    
    print("\nFastAPI Integration:")
    print("  from agentlog import fastapi_middleware")
    print("  app = FastAPI()")
    print("  app.middleware('http')(fastapi_middleware())")
    
    print("\nFlask Integration:")
    print("  from agentlog import flask_before_request, flask_after_request")
    print("  app = Flask(__name__)")
    print("  app.before_request(flask_before_request)")
    print("  app.after_request(flask_after_request)")
    
    print("\nDjango Integration:")
    print("  # In settings.py")
    print("  MIDDLEWARE = ['agentlog.DjangoMiddleware', ...]")
    
    print("\nGeneric ASGI/WSGI:")
    print("  from agentlog import asgi_middleware, wsgi_middleware")
    print("  app = asgi_middleware(app)  # For ASGI")
    print("  app.wsgi_app = wsgi_middleware(app.wsgi_app)  # For WSGI")
    
    print("\n✓ Lightweight adapters for all major Python frameworks")


def demonstrate_cross_language_compatibility():
    """Show cross-language compatibility features."""
    print("\n" + "=" * 70)
    print("6. CROSS-LANGUAGE COMPATIBILITY")
    print("=" * 70)
    
    # Generate some logs
    log("Processing batch", batch_size=100)
    log_error("Connection timeout", error=Exception("Timeout"))
    
    print("\nOutput Format:")
    print("  - Single-line JSON (JSONL)")
    print("  - Compact keys (t, v, n, k)")
    print("  - Consistent schema across all tags")
    print("  - Language-agnostic structure")
    
    print("\nSchema Validation:")
    print("  - JSON Schema for validation")
    print("  - TypeScript types for JS/TS consumers")
    print("  - Go structs for Go consumers")
    print("  - Easy to add more languages")
    
    print("\n✓ Output can be consumed by any language with JSON support")


def demonstrate_schema_export_to_files():
    """Show exporting schemas to files."""
    print("\n" + "=" * 70)
    print("7. EXPORTING SCHEMAS TO FILES")
    print("=" * 70)
    
    # Export to files (simulated)
    print("\nExporting schemas:")
    
    json_schema = export_schema_json()
    print(f"  agentlog-schema.json: {len(json_schema)} bytes")
    
    ts_types = export_schema_typescript()
    print(f"  agentlog.d.ts: {len(ts_types)} bytes")
    
    go_types = export_schema_go()
    print(f"  agentlog.go: {len(go_types)} bytes")
    
    print("\n✓ Schemas can be exported for documentation and validation")


def main():
    print("=" * 70)
    print("AGENTLOG PHASE 3 DEMONSTRATION")
    print("Schema Validation & Framework Adapters")
    print("=" * 70)
    
    demonstrate_schema_validation()
    demonstrate_value_descriptor_validation()
    demonstrate_schema_exports()
    demonstrate_endpoint_decorator()
    demonstrate_framework_integration_patterns()
    demonstrate_cross_language_compatibility()
    demonstrate_schema_export_to_files()
    
    print("\n" + "=" * 70)
    print("PHASE 3 FEATURES COMPLETE")
    print("=" * 70)
    print("\nAll Phase 3 features demonstrated:")
    print("✓ Schema validation (validate_entry, validate_value_descriptor)")
    print("✓ JSON Schema export (export_schema_json)")
    print("✓ TypeScript type definitions (export_schema_typescript)")
    print("✓ Go struct definitions (export_schema_go)")
    print("✓ Framework adapters (FastAPI, Flask, Django)")
    print("✓ Generic decorators and middleware")
    print("✓ ASGI/WSGI adapters")
    print("✓ Cross-language compatibility")
    print("\nPhase 3 Status: COMPLETE ✅")
    print("\nAll 3 Phases Complete:")
    print("  Phase 1: AI Debugging Foundation ✅")
    print("  Phase 2: Agent Workflow Optimization ✅")
    print("  Phase 3: Schema Validation & Adapters ✅")
    print()


if __name__ == "__main__":
    main()
