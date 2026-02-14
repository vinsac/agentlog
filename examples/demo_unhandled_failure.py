"""
Demonstration of automatic failure capture for UNHANDLED exceptions.

sys.excepthook only fires for unhandled exceptions that would normally
crash the program. This is the primary use case: capturing runtime state
when your program fails unexpectedly.

Run with:
    AGENTLOG=true python3 examples/demo_unhandled_failure.py
"""

import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog

# Enable agentlog (or set AGENTLOG=true environment variable)
agentlog.enable()


def process_user_data(user_id: str, profile_data: dict):
    """
    Process user profile data.
    
    This function will crash with an unhandled exception, and agentlog
    will automatically capture all local variables at the failure point.
    """
    # Some processing
    confidence_scores = [0.8, 0.9, 0.95, 0.7]
    threshold = 0.85
    
    # This will cause an unhandled KeyError
    email = profile_data["email"]  # Key doesn't exist!
    
    return {"user_id": user_id, "email": email}


def main():
    print("=" * 70)
    print("Automatic Failure Capture Demo (Unhandled Exception)")
    print("=" * 70)
    print()
    print("This script will crash with an unhandled KeyError.")
    print("Watch for the [AGENTLOG:error] line that shows:")
    print("  - All local variables at the failure point")
    print("  - Structured error context")
    print("  - Compact JSON format for AI agents")
    print()
    print("-" * 70)
    
    # This will crash - no try/except
    user_id = "u_abc123"
    profile = {"name": "Alice", "age": 30}  # Missing "email" key
    
    result = process_user_data(user_id, profile)
    
    # This line never executes
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
