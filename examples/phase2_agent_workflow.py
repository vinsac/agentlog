"""
Phase 2 Agent Workflow Optimization Demo

Demonstrates Phase 2 features:
- LLM call tracing
- Tool call tracing
- Prompt/response correlation
- Context filtering by importance
- Token compression

Run with:
    AGENTLOG=true python3 examples/phase2_agent_workflow.py
"""

import sys
import os
import time

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog
from agentlog import (
    enable, log_llm_call, log_tool_call, log_prompt, log_response,
    llm_call, tool_call, get_context_smart, summary
)

# Enable agentlog
enable()


def demonstrate_llm_call_tracing():
    """Show LLM call tracing with correlation."""
    print("\n" + "=" * 70)
    print("1. LLM CALL TRACING")
    print("=" * 70)
    
    # Simulate an LLM API call
    call_id = log_llm_call(
        model="gpt-4",
        prompt="Explain Python decorators in simple terms",
        response="A decorator is a function that wraps another function...",
        duration_ms=1250.5,
        tokens_in=12,
        tokens_out=150,
        temperature=0.7,
        max_tokens=500
    )
    
    print(f"LLM call logged with ID: {call_id}")
    print("✓ AI agents see: model, prompt, response, timing, token usage")


def demonstrate_tool_call_tracing():
    """Show tool call tracing."""
    print("\n" + "=" * 70)
    print("2. TOOL CALL TRACING")
    print("=" * 70)
    
    # Simulate a tool call
    call_id = log_tool_call(
        tool_name="search_database",
        arguments={"query": "Python skills", "limit": 10},
        result={"count": 5, "items": ["Python", "Django", "FastAPI", "Flask", "Pandas"]},
        duration_ms=45.2,
        success=True
    )
    
    print(f"Tool call logged with ID: {call_id}")
    print("✓ AI agents see: tool name, arguments, result, timing, success status")


def demonstrate_prompt_response_correlation():
    """Show prompt/response correlation."""
    print("\n" + "=" * 70)
    print("3. PROMPT/RESPONSE CORRELATION")
    print("=" * 70)
    
    # Log prompt
    prompt_id = log_prompt(
        "Write a Python function to calculate fibonacci",
        model="gpt-4",
        temperature=0.5,
        max_tokens=300
    )
    
    print(f"Prompt logged with ID: {prompt_id}")
    
    # Simulate API call delay
    time.sleep(0.1)
    
    # Log response
    log_response(
        prompt_id,
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        duration_ms=850.3,
        tokens_out=45
    )
    
    print(f"Response logged, correlated with prompt ID: {prompt_id}")
    print("✓ AI agents can trace prompt → response flow")


def demonstrate_context_managers():
    """Show context manager usage for automatic timing."""
    print("\n" + "=" * 70)
    print("4. CONTEXT MANAGERS (Automatic Timing)")
    print("=" * 70)
    
    # LLM call with context manager
    with llm_call("claude-3-opus", "Explain async/await") as call:
        # Simulate API call
        time.sleep(0.05)
        call["response"] = "Async/await is a syntax for handling asynchronous operations..."
        call["tokens_out"] = 80
    
    print("LLM call with automatic timing ✓")
    
    # Tool call with context manager
    with tool_call("fetch_user_data", {"user_id": "u_123"}) as call:
        # Simulate tool execution
        time.sleep(0.02)
        call["result"] = {"name": "Alice", "age": 30}
    
    print("Tool call with automatic timing ✓")
    print("✓ Context managers handle timing and error logging automatically")


def demonstrate_context_filtering():
    """Show smart context filtering by importance."""
    print("\n" + "=" * 70)
    print("5. CONTEXT FILTERING BY IMPORTANCE")
    print("=" * 70)
    
    # Generate various log entries
    agentlog.log("Processing batch", batch_size=100)
    agentlog.log_decision("Should retry?", True, "error_count < 3")
    agentlog.log_error("Connection timeout", error=Exception("Timeout"))
    
    # Get context with different importance levels
    critical = get_context_smart(max_tokens=500, importance="critical")
    high = get_context_smart(max_tokens=1000, importance="high")
    medium = get_context_smart(max_tokens=2000, importance="medium")
    
    print(f"Critical importance: {len(critical.split(chr(10)))} entries")
    print(f"High importance: {len(high.split(chr(10)))} entries")
    print(f"Medium importance: {len(medium.split(chr(10)))} entries")
    print("✓ AI agents can filter by importance to focus on critical issues")


def demonstrate_session_summary():
    """Show session summary for quick overview."""
    print("\n" + "=" * 70)
    print("6. SESSION SUMMARY")
    print("=" * 70)
    
    s = summary()
    
    print(f"Total entries: {s['total']}")
    print(f"By tag: {s['by_tag']}")
    if s['errors']:
        print(f"Errors: {len(s['errors'])}")
    print("✓ AI agents get quick overview without reading all logs")


def simulate_agent_workflow():
    """Simulate a complete AI agent workflow."""
    print("\n" + "=" * 70)
    print("7. COMPLETE AGENT WORKFLOW SIMULATION")
    print("=" * 70)
    
    # Agent receives user request
    user_request = "Find Python developers with 5+ years experience"
    
    # Agent decides on approach
    agentlog.log_decision(
        "Should use database search?",
        True,
        "Query is specific and structured",
        query_type="structured"
    )
    
    # Agent calls search tool
    with tool_call("search_candidates", {"skill": "Python", "years": 5}) as call:
        time.sleep(0.03)
        call["result"] = {"count": 12, "candidates": ["Alice", "Bob", "Charlie"]}
    
    # Agent calls LLM to format results
    with llm_call("gpt-4", f"Format these candidates: {call['result']}") as llm:
        time.sleep(0.05)
        llm["response"] = "Found 12 Python developers:\n1. Alice (7 years)\n2. Bob (6 years)..."
        llm["tokens_out"] = 85
    
    # Get high-priority context for debugging
    context = get_context_smart(max_tokens=1000, importance="high")
    
    print("Agent workflow complete!")
    print(f"Context for AI debugging: {len(context)} characters")
    print("✓ Complete workflow traced with correlation IDs")


def main():
    print("=" * 70)
    print("AGENTLOG PHASE 2 DEMONSTRATION")
    print("Agent Workflow Optimization")
    print("=" * 70)
    
    demonstrate_llm_call_tracing()
    demonstrate_tool_call_tracing()
    demonstrate_prompt_response_correlation()
    demonstrate_context_managers()
    demonstrate_context_filtering()
    demonstrate_session_summary()
    simulate_agent_workflow()
    
    print("\n" + "=" * 70)
    print("PHASE 2 FEATURES COMPLETE")
    print("=" * 70)
    print("\nAll Phase 2 features demonstrated:")
    print("✓ LLM call tracing (log_llm_call)")
    print("✓ Tool call tracing (log_tool_call)")
    print("✓ Prompt/response correlation (log_prompt, log_response)")
    print("✓ Context managers (llm_call, tool_call)")
    print("✓ Context filtering by importance (get_context_smart)")
    print("✓ Token compression for large values")
    print("✓ Priority-based filtering")
    print("\nPhase 2 Status: COMPLETE ✅")
    print()


if __name__ == "__main__":
    main()
