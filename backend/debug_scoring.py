#!/usr/bin/env python3
"""
Debug script to understand why scoring is not working correctly.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.scoring import analyze_answer_quality, calculate_detailed_score

def debug_scoring():
    """Debug the scoring functionality."""
    print("Debugging scoring system...")
    
    # Test case
    question = "What is the difference between lists and tuples in Python?"
    expected_answer = "Lists are mutable data structures that can be modified after creation, while tuples are immutable and cannot be changed once created. Lists use square brackets and tuples use parentheses."
    candidate_answer = "Lists are mutable while tuples are immutable. Lists use square brackets and tuples use parentheses."
    
    print(f"\nQuestion: {question}")
    print(f"Expected Answer: {expected_answer}")
    print(f"Candidate Answer: {candidate_answer}")
    
    # Analyze answer quality
    analysis = analyze_answer_quality(
        text=candidate_answer,
        question=question,
        expected_answer=expected_answer
    )
    
    print(f"\nAnalysis Results:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    # Calculate detailed score
    detailed_score, feedback_items = calculate_detailed_score(analysis, question)
    
    print(f"\nDetailed Score: {detailed_score}")
    print(f"Feedback Items:")
    for item in feedback_items:
        print(f"  {item}")
    
    # Convert to 1-5 scale
    scaled_score = max(1, min(5, round(detailed_score / 20)))
    print(f"\nScaled Score (1-5): {scaled_score}")
    
    # Build feedback string
    feedback = " | ".join(feedback_items)
    print(f"\nFeedback String: {feedback}")

if __name__ == "__main__":
    debug_scoring()