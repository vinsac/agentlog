"""
JSON Schema validation for agentlog output.

Provides schema definitions and validation utilities to ensure
consistent output format across implementations and languages.
"""

import json
from typing import Any, Dict, List, Optional, Tuple


# Core schema version
SCHEMA_VERSION = "1.0"


def get_base_schema() -> Dict[str, Any]:
    """
    Get the base JSON schema for all agentlog entries.
    
    Returns:
        JSON Schema dict for base entry structure
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Agentlog Entry",
        "description": "Base schema for all agentlog log entries",
        "type": "object",
        "required": ["seq", "ts", "at"],
        "properties": {
            "seq": {
                "type": "integer",
                "description": "Monotonically increasing sequence number",
                "minimum": 1
            },
            "ts": {
                "type": "number",
                "description": "Unix timestamp (seconds since epoch)"
            },
            "at": {
                "type": "string",
                "description": "Location: filename:line function_name",
                "pattern": "^.+:\\d+ .+$"
            },
            "trace": {
                "type": "string",
                "description": "Optional trace ID for distributed tracing"
            },
            "span": {
                "type": "string",
                "description": "Optional span ID for nested operations"
            }
        }
    }


def get_value_descriptor_schema() -> Dict[str, Any]:
    """
    Get the JSON schema for value descriptors.
    
    Returns:
        JSON Schema dict for value descriptor structure
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Value Descriptor",
        "description": "Compact value descriptor for AI consumption",
        "type": "object",
        "required": ["t"],
        "properties": {
            "t": {
                "type": "string",
                "description": "Type name (str, int, float, bool, list, dict, etc.)"
            },
            "v": {
                "description": "Value (for scalars and small collections)"
            },
            "n": {
                "type": "integer",
                "description": "Length/count (for collections)",
                "minimum": 0
            },
            "k": {
                "type": "array",
                "description": "Keys (for dicts)",
                "items": {"type": "string"}
            },
            "it": {
                "type": "string",
                "description": "Item type (for homogeneous collections)"
            },
            "sh": {
                "type": "string",
                "description": "Shape (for numpy/torch/pandas arrays)"
            },
            "dt": {
                "type": "string",
                "description": "Data type (for arrays)"
            },
            "range": {
                "type": "array",
                "description": "Min/max values (for numeric arrays)",
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2
            },
            "preview": {
                "type": "array",
                "description": "First items of large collections"
            },
            "truncated": {
                "type": "integer",
                "description": "Original length if value was truncated",
                "minimum": 0
            }
        }
    }


def validate_entry(entry: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a log entry against the base schema.
    
    Args:
        entry: Log entry dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        valid, error = validate_entry({"seq": 1, "ts": 1234567890.0, "at": "main.py:42 func"})
        if not valid:
            print(f"Validation error: {error}")
    """
    # Check required fields
    required = ["seq", "ts", "at"]
    for field in required:
        if field not in entry:
            return False, f"Missing required field: {field}"
    
    # Validate seq
    if not isinstance(entry["seq"], int) or entry["seq"] < 1:
        return False, "Field 'seq' must be a positive integer"
    
    # Validate ts
    if not isinstance(entry["ts"], (int, float)):
        return False, "Field 'ts' must be a number"
    
    # Validate at
    if not isinstance(entry["at"], str):
        return False, "Field 'at' must be a string"
    
    # Basic format check for 'at' field
    if ":" not in entry["at"] or " " not in entry["at"]:
        return False, "Field 'at' must be in format 'filename:line function_name'"
    
    return True, None


def validate_value_descriptor(descriptor: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a value descriptor.
    
    Args:
        descriptor: Value descriptor dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required field
    if "t" not in descriptor:
        return False, "Missing required field: 't' (type)"
    
    if not isinstance(descriptor["t"], str):
        return False, "Field 't' must be a string"
    
    # Validate optional fields
    if "n" in descriptor and not isinstance(descriptor["n"], int):
        return False, "Field 'n' must be an integer"
    
    if "k" in descriptor and not isinstance(descriptor["k"], list):
        return False, "Field 'k' must be an array"
    
    if "range" in descriptor:
        if not isinstance(descriptor["range"], list) or len(descriptor["range"]) != 2:
            return False, "Field 'range' must be an array of 2 numbers"
    
    return True, None


def export_schema_json() -> str:
    """
    Export the complete JSON schema as a JSON string.
    
    Returns:
        JSON string of the complete schema
        
    Example:
        schema_json = export_schema_json()
        with open("agentlog-schema.json", "w") as f:
            f.write(schema_json)
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Agentlog Schema",
        "description": "Complete schema for agentlog output format",
        "version": SCHEMA_VERSION,
        "definitions": {
            "base_entry": get_base_schema(),
            "value_descriptor": get_value_descriptor_schema()
        },
        "tags": {
            "error": {
                "description": "Error with structured context",
                "level": "error",
                "priority": 10
            },
            "check": {
                "description": "Runtime assertion (failed checks are warnings)",
                "level": "warn",
                "priority": 9
            },
            "llm": {
                "description": "LLM API call with prompt/response",
                "level": "info",
                "priority": 8
            },
            "tool": {
                "description": "AI agent tool/function call",
                "level": "info",
                "priority": 8
            },
            "decision": {
                "description": "Control flow decision",
                "level": "info",
                "priority": 7
            },
            "prompt": {
                "description": "Prompt sent to LLM",
                "level": "info",
                "priority": 7
            },
            "response": {
                "description": "Response from LLM",
                "level": "info",
                "priority": 7
            },
            "diff": {
                "description": "State difference",
                "level": "debug",
                "priority": 6
            },
            "flow": {
                "description": "Data flow transformation",
                "level": "debug",
                "priority": 5
            },
            "func": {
                "description": "Function entry/exit",
                "level": "info",
                "priority": 4
            },
            "query": {
                "description": "Database/external query",
                "level": "info",
                "priority": 4
            },
            "http": {
                "description": "HTTP request/response",
                "level": "info",
                "priority": 4
            },
            "span": {
                "description": "Named span",
                "level": "info",
                "priority": 3
            },
            "info": {
                "description": "General information",
                "level": "info",
                "priority": 2
            },
            "vars": {
                "description": "Variable inspection",
                "level": "debug",
                "priority": 1
            },
            "state": {
                "description": "State snapshot",
                "level": "debug",
                "priority": 1
            },
            "perf": {
                "description": "Performance metrics",
                "level": "debug",
                "priority": 1
            }
        }
    }
    
    return json.dumps(schema, indent=2)


def export_schema_typescript() -> str:
    """
    Export TypeScript type definitions for agentlog schema.
    
    Returns:
        TypeScript type definitions as a string
    """
    return '''/**
 * Agentlog TypeScript Type Definitions
 * Schema Version: 1.0
 * 
 * These types define the structure of agentlog output for TypeScript/JavaScript
 * implementations and consumers.
 */

/**
 * Base structure for all log entries
 */
export interface AgentlogEntry {
  seq: number;           // Monotonically increasing sequence number
  ts: number;            // Unix timestamp (seconds since epoch)
  at: string;            // Location: "filename:line function_name"
  trace?: string;        // Optional trace ID
  span?: string;         // Optional span ID
  tag?: string;          // Entry tag (error, info, llm, tool, etc.)
  [key: string]: any;    // Tag-specific fields
}

/**
 * Value descriptor for compact representation
 */
export interface ValueDescriptor {
  t: string;             // Type name
  v?: any;               // Value (for scalars and small collections)
  n?: number;            // Length/count (for collections)
  k?: string[];          // Keys (for dicts)
  it?: string;           // Item type (for homogeneous collections)
  sh?: string;           // Shape (for arrays)
  dt?: string;           // Data type (for arrays)
  range?: [number, number]; // Min/max (for numeric arrays)
  preview?: any[];       // First items of large collections
  truncated?: number;    // Original length if truncated
}

/**
 * Error entry
 */
export interface ErrorEntry extends AgentlogEntry {
  tag: "error";
  fn: string;
  error: {
    type: string;
    msg: string;
  };
  locals: Record<string, ValueDescriptor>;
}

/**
 * LLM call entry
 */
export interface LLMEntry extends AgentlogEntry {
  tag: "llm";
  call_id: string;
  model: string;
  prompt: ValueDescriptor;
  response?: ValueDescriptor;
  ms?: number;
  tokens_in?: number;
  tokens_out?: number;
  ctx?: Record<string, ValueDescriptor>;
}

/**
 * Tool call entry
 */
export interface ToolEntry extends AgentlogEntry {
  tag: "tool";
  call_id: string;
  tool: string;
  args: Record<string, ValueDescriptor>;
  result?: ValueDescriptor;
  ms?: number;
  success: boolean;
  ctx?: Record<string, ValueDescriptor>;
}

/**
 * Decision entry
 */
export interface DecisionEntry extends AgentlogEntry {
  tag: "decision";
  question: string;
  answer: ValueDescriptor;
  reason?: string;
  ctx?: Record<string, ValueDescriptor>;
}

/**
 * Log level type
 */
export type LogLevel = "debug" | "info" | "warn" | "error";

/**
 * Tag type
 */
export type LogTag = 
  | "error" | "check" | "llm" | "tool" | "decision" 
  | "prompt" | "response" | "diff" | "flow" | "func" 
  | "query" | "http" | "span" | "info" | "vars" 
  | "state" | "perf";

/**
 * Importance level for filtering
 */
export type ImportanceLevel = "low" | "medium" | "high" | "critical";
'''


def export_schema_go() -> str:
    """
    Export Go struct definitions for agentlog schema.
    
    Returns:
        Go struct definitions as a string
    """
    return '''// Agentlog Go Type Definitions
// Schema Version: 1.0
//
// These types define the structure of agentlog output for Go
// implementations and consumers.

package agentlog

import "time"

// AgentlogEntry is the base structure for all log entries
type AgentlogEntry struct {
	Seq   int                    `json:"seq"`            // Monotonically increasing sequence number
	Ts    float64                `json:"ts"`             // Unix timestamp (seconds since epoch)
	At    string                 `json:"at"`             // Location: "filename:line function_name"
	Trace *string                `json:"trace,omitempty"` // Optional trace ID
	Span  *string                `json:"span,omitempty"`  // Optional span ID
	Tag   string                 `json:"tag,omitempty"`   // Entry tag
	Extra map[string]interface{} `json:"-"`              // Tag-specific fields
}

// ValueDescriptor represents a compact value representation
type ValueDescriptor struct {
	T         string        `json:"t"`                   // Type name
	V         interface{}   `json:"v,omitempty"`         // Value
	N         *int          `json:"n,omitempty"`         // Length/count
	K         []string      `json:"k,omitempty"`         // Keys
	It        *string       `json:"it,omitempty"`        // Item type
	Sh        *string       `json:"sh,omitempty"`        // Shape
	Dt        *string       `json:"dt,omitempty"`        // Data type
	Range     *[2]float64   `json:"range,omitempty"`     // Min/max
	Preview   []interface{} `json:"preview,omitempty"`   // Preview items
	Truncated *int          `json:"truncated,omitempty"` // Original length
}

// ErrorEntry represents an error log entry
type ErrorEntry struct {
	AgentlogEntry
	Fn     string                      `json:"fn"`
	Error  ErrorInfo                   `json:"error"`
	Locals map[string]ValueDescriptor  `json:"locals"`
}

// ErrorInfo contains error details
type ErrorInfo struct {
	Type string `json:"type"`
	Msg  string `json:"msg"`
}

// LLMEntry represents an LLM call log entry
type LLMEntry struct {
	AgentlogEntry
	CallID    string                     `json:"call_id"`
	Model     string                     `json:"model"`
	Prompt    ValueDescriptor            `json:"prompt"`
	Response  *ValueDescriptor           `json:"response,omitempty"`
	Ms        *float64                   `json:"ms,omitempty"`
	TokensIn  *int                       `json:"tokens_in,omitempty"`
	TokensOut *int                       `json:"tokens_out,omitempty"`
	Ctx       map[string]ValueDescriptor `json:"ctx,omitempty"`
}

// ToolEntry represents a tool call log entry
type ToolEntry struct {
	AgentlogEntry
	CallID  string                     `json:"call_id"`
	Tool    string                     `json:"tool"`
	Args    map[string]ValueDescriptor `json:"args"`
	Result  *ValueDescriptor           `json:"result,omitempty"`
	Ms      *float64                   `json:"ms,omitempty"`
	Success bool                       `json:"success"`
	Ctx     map[string]ValueDescriptor `json:"ctx,omitempty"`
}

// DecisionEntry represents a decision log entry
type DecisionEntry struct {
	AgentlogEntry
	Question string                     `json:"question"`
	Answer   ValueDescriptor            `json:"answer"`
	Reason   *string                    `json:"reason,omitempty"`
	Ctx      map[string]ValueDescriptor `json:"ctx,omitempty"`
}

// LogLevel represents log severity
type LogLevel string

const (
	LogLevelDebug LogLevel = "debug"
	LogLevelInfo  LogLevel = "info"
	LogLevelWarn  LogLevel = "warn"
	LogLevelError LogLevel = "error"
)

// ImportanceLevel for filtering
type ImportanceLevel string

const (
	ImportanceLow      ImportanceLevel = "low"
	ImportanceMedium   ImportanceLevel = "medium"
	ImportanceHigh     ImportanceLevel = "high"
	ImportanceCritical ImportanceLevel = "critical"
)
'''


def validate_jsonl_file(filepath: str) -> Tuple[int, int, List[str]]:
    """
    Validate a JSONL file of agentlog entries.
    
    Args:
        filepath: Path to JSONL file
        
    Returns:
        Tuple of (valid_count, invalid_count, error_messages)
        
    Example:
        valid, invalid, errors = validate_jsonl_file(".agentlog/session.jsonl")
        print(f"Valid: {valid}, Invalid: {invalid}")
        for error in errors:
            print(f"  {error}")
    """
    valid_count = 0
    invalid_count = 0
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    is_valid, error = validate_entry(entry)
                    
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        errors.append(f"Line {line_num}: {error}")
                        
                except json.JSONDecodeError as e:
                    invalid_count += 1
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                    
    except FileNotFoundError:
        errors.append(f"File not found: {filepath}")
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
    
    return valid_count, invalid_count, errors
