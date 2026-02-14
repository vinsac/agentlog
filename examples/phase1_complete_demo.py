"""
Complete Phase 1 Feature Demonstration

This script demonstrates all Phase 1 features of agentlog:
- Automatic failure capture
- Decision logging
- Flow tracing
- Context export for AI agents
- Runtime error structuring

Run with:
    AGENTLOG=true python3 examples/phase1_complete_demo.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog
from agentlog import (
    log, log_vars, log_error, log_decision, log_flow, 
    log_diff, get_context, summary, enable
)

# Enable agentlog
enable()


def demonstrate_decision_logging():
    """Show how decision logging helps AI agents understand control flow."""
    print("\n" + "=" * 70)
    print("1. DECISION LOGGING")
    print("=" * 70)
    
    user_id = "u_abc123"
    confidence = 0.85
    threshold = 0.9
    
    # Log the decision with actual values
    log_decision(
        "Should merge with existing skill?",
        confidence >= threshold,
        reason=f"confidence {confidence} >= threshold {threshold}",
        confidence=confidence,
        threshold=threshold,
        user_id=user_id
    )
    
    print(f"Decision: confidence {confidence} >= {threshold} = {confidence >= threshold}")
    print("✓ AI agents see the actual runtime values, not assumptions")


def demonstrate_flow_tracing():
    """Show how flow tracing tracks data through pipelines."""
    print("\n" + "=" * 70)
    print("2. FLOW TRACING")
    print("=" * 70)
    
    # Simulate a data processing pipeline
    raw_input = "  Python Programming  "
    
    log_flow("skill_pipeline", "raw_input", raw_input)
    
    # Step 1: Normalize
    normalized = raw_input.strip().lower()
    log_flow("skill_pipeline", "normalized", normalized)
    
    # Step 2: Validate
    is_valid = len(normalized) > 0
    log_flow("skill_pipeline", "validated", is_valid, length=len(normalized))
    
    # Step 3: Enrich
    enriched = {"name": normalized, "category": "programming", "confidence": 0.95}
    log_flow("skill_pipeline", "enriched", enriched)
    
    print(f"Pipeline: '{raw_input}' -> '{normalized}' -> {enriched}")
    print("✓ AI agents see how data transforms through each step")


def demonstrate_state_diffing():
    """Show how state diffing captures changes."""
    print("\n" + "=" * 70)
    print("3. STATE DIFFING")
    print("=" * 70)
    
    # Before state
    old_profile = {
        "name": "Alice",
        "age": 30,
        "skills": ["Python", "JavaScript"],
        "active": True
    }
    
    # After state
    new_profile = {
        "name": "Alice",
        "age": 31,  # Changed
        "skills": ["Python", "JavaScript", "Go"],  # Added
        "active": True,
        "verified": True  # Added
    }
    
    log_diff("user_profile", old_profile, new_profile)
    
    print("Profile updated:")
    print(f"  Age: {old_profile['age']} -> {new_profile['age']}")
    print(f"  Skills: {old_profile['skills']} -> {new_profile['skills']}")
    print(f"  Added: verified={new_profile['verified']}")
    print("✓ AI agents see only what changed, not full state dumps")


def demonstrate_context_export():
    """Show how context export fits logs into AI token budgets."""
    print("\n" + "=" * 70)
    print("4. CONTEXT EXPORT FOR AI AGENTS")
    print("=" * 70)
    
    # Generate some logs
    for i in range(10):
        log(f"Processing item {i}", item_id=f"item_{i}", status="processing")
    
    # Export with token budget
    context = get_context(max_tokens=500, tags=["info", "decision", "flow"])
    
    print(f"Exported {len(context.split(chr(10)))} log entries within 500 token budget")
    print("✓ AI agents get relevant logs that fit in their context window")
    
    # Get summary
    s = summary()
    print(f"\nSession summary:")
    print(f"  Total entries: {s['total']}")
    print(f"  By tag: {s['by_tag']}")
    print("✓ AI agents can get quick overview without reading all logs")


def demonstrate_error_structuring():
    """Show how errors are automatically structured."""
    print("\n" + "=" * 70)
    print("5. RUNTIME ERROR STRUCTURING")
    print("=" * 70)
    
    try:
        user_data = {"name": "Bob", "age": 25}
        confidence_score = 1.5  # Invalid!
        threshold = 1.0
        
        if confidence_score > threshold:
            raise ValueError(f"Invalid confidence: {confidence_score}")
            
    except ValueError as e:
        # Manually log error with context
        log_error(
            "Validation failed",
            error=e,
            user_data=user_data,
            confidence_score=confidence_score,
            threshold=threshold
        )
        print(f"Caught error: {e}")
        print("✓ AI agents see structured error with all local context")


def demonstrate_automatic_failure_capture():
    """
    Show automatic failure capture (this will crash the script).
    
    Uncomment to see automatic capture in action.
    """
    print("\n" + "=" * 70)
    print("6. AUTOMATIC FAILURE CAPTURE")
    print("=" * 70)
    print("Note: Automatic capture only works for UNHANDLED exceptions")
    print("See examples/demo_unhandled_failure.py for a working demo")
    print("✓ Zero instrumentation - captures failures automatically")


def main():
    print("=" * 70)
    print("AGENTLOG PHASE 1 COMPLETE DEMONSTRATION")
    print("Agent Runtime Visibility Toolkit")
    print("=" * 70)
    
    demonstrate_decision_logging()
    demonstrate_flow_tracing()
    demonstrate_state_diffing()
    demonstrate_context_export()
    demonstrate_error_structuring()
    demonstrate_automatic_failure_capture()
    
    print("\n" + "=" * 70)
    print("PHASE 1 FEATURES COMPLETE")
    print("=" * 70)
    print("\nAll Phase 1 features demonstrated:")
    print("✓ Automatic failure capture (sys.excepthook)")
    print("✓ Decision logging (log_decision)")
    print("✓ Flow tracing (log_flow)")
    print("✓ State diffing (log_diff)")
    print("✓ Context export (get_context with token budget)")
    print("✓ Runtime error structuring (log_error)")
    print("\nNext: Phase 2 - Agent Workflow Optimization")
    print()


if __name__ == "__main__":
    main()
