"""
Demo: agentlog in action — a real app with a real bug.

This app processes skill ratings from LLM analysis. It has a validation
bug: confidence values > 1.0 slip through and crash downstream.
Run this to see what agentlog captures when the crash happens.

Usage:
    AGENTLOG=true python examples/demo_app.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import agentlog


def validate_rating(confidence: float, threshold: float = 0.7) -> bool:
    """Check if confidence meets threshold. BUG: doesn't validate range."""
    if confidence > threshold:
        return True
    return False


def normalize_score(confidence: float) -> float:
    """Normalize confidence to percentage. Crashes on out-of-range input."""
    if confidence < 0 or confidence > 1.0:
        raise ValueError(
            f"Confidence {confidence} out of valid range [0, 1]"
        )
    return round(confidence * 100, 1)


def process_skill_ratings(ratings: list) -> dict:
    """Process a batch of skill ratings from LLM analysis."""
    agentlog.start_session("skill_analyzer", "process_ratings")
    results = {"accepted": [], "rejected": []}

    for rating in ratings:
        name = rating["skill"]
        confidence = rating["confidence"]

        with agentlog.tool_call("validate_rating", {"confidence": confidence, "threshold": 0.7}):
            passed = validate_rating(confidence)

        if passed:
            score = normalize_score(confidence)
            results["accepted"].append({"skill": name, "score": score})
        else:
            results["rejected"].append({"skill": name, "confidence": confidence})

    agentlog.end_session()
    return results


def main():
    agentlog.enable()

    with agentlog.llm_call("gpt-4", "Analyze skill confidence scores") as call:
        ratings = [
            {"skill": "Python", "confidence": 0.95},
            {"skill": "Rust", "confidence": 0.45},
            {"skill": "Go", "confidence": 1.5},
        ]
        call["tokens_in"] = 150
        call["tokens_out"] = 80

    try:
        result = process_skill_ratings(ratings)
        print("Results:", result)
    except Exception as e:
        agentlog.log_error("Rating processing crashed", error=e)
        print("\n" + "=" * 60)
        print("CRASH! Here's what agentlog captured for the AI agent:")
        print("=" * 60 + "\n")
        print(agentlog.get_debug_context())


if __name__ == "__main__":
    main()
