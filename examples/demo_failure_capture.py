"""
Demonstration of automatic failure capture in agentlog.

This script shows how agentlog automatically captures structured runtime
context when exceptions occur, without requiring any instrumentation.

Run with:
    AGENTLOG=true python3 examples/demo_failure_capture.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog

# Enable agentlog (or set AGENTLOG=true environment variable)
agentlog.enable()


def process_skill(name: str, confidence: float, threshold: float = 0.9):
    """
    Process a skill with validation.
    
    This function will fail if confidence is invalid, and agentlog will
    automatically capture all local variables at the failure point.
    """
    user_id = "u_abc123"
    skill_data = {
        "name": name,
        "confidence": confidence,
        "created_at": "2026-02-14",
    }
    
    # Validation that will fail
    if confidence > 1.0:
        raise ValueError(f"Invalid confidence: {confidence}")
    
    if confidence < threshold:
        raise ValueError(f"Confidence {confidence} below threshold {threshold}")
    
    return skill_data


def main():
    print("=" * 70)
    print("Automatic Failure Capture Demo")
    print("=" * 70)
    print()
    
    print("Example 1: Confidence validation failure")
    print("-" * 70)
    try:
        # This will fail with confidence > 1.0
        result = process_skill("Python", 1.5, 0.9)
    except ValueError as e:
        print(f"\nCaught exception: {e}")
        print("\nCheck the [AGENTLOG:error] line above for structured context!")
        print("It includes:")
        print("  - All local variables (user_id, skill_data, confidence, threshold)")
        print("  - Compact type descriptors (t, v, n, k)")
        print("  - Function name and error details")
    
    print("\n" + "=" * 70)
    print("\nExample 2: Threshold validation failure")
    print("-" * 70)
    try:
        # This will fail with confidence < threshold
        result = process_skill("JavaScript", 0.3, 0.9)
    except ValueError as e:
        print(f"\nCaught exception: {e}")
        print("\nAgain, check the [AGENTLOG:error] line for structured context!")
    
    print("\n" + "=" * 70)
    print("\nKey Benefits for AI Agents:")
    print("-" * 70)
    print("✓ Zero instrumentation required")
    print("✓ Automatic capture at failure boundaries")
    print("✓ Structured JSON with compact keys (t, v, n, k)")
    print("✓ Token-efficient for LLM context windows")
    print("✓ AI agents see actual runtime values, not assumptions")
    print()


if __name__ == "__main__":
    main()
