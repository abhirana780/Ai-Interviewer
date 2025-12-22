#!/usr/bin/env python3
"""
Test script to verify the keyword matching system with expected answers.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.scoring import score_answer

def test_keyword_matching():
    """Test the keyword matching functionality."""
    print("Testing keyword matching with expected answers...")
    
    # Test case 1: Good match
    question = "What is the difference between lists and tuples in Python?"
    expected_answer = "Lists are mutable data structures that can be modified after creation, while tuples are immutable and cannot be changed once created. Lists use square brackets and tuples use parentheses."
    candidate_answer = "Lists are mutable while tuples are immutable. Lists use square brackets and tuples use parentheses."
    
    score, feedback = score_answer(
        text=candidate_answer,
        question=question,
        expected_answer=expected_answer
    )
    
    print(f"\nQuestion: {question}")
    print(f"Expected Answer: {expected_answer}")
    print(f"Candidate Answer: {candidate_answer}")
    print(f"Score: {score}/5")
    print(f"Feedback: {feedback}")
    
    # Test case 2: Poor match
    poor_candidate_answer = "I don't know the difference between lists and tuples."
    poor_score, poor_feedback = score_answer(
        text=poor_candidate_answer,
        question=question,
        expected_answer=expected_answer
    )
    
    print(f"\nPoor Candidate Answer: {poor_candidate_answer}")
    print(f"Poor Score: {poor_score}/5")
    print(f"Poor Feedback: {poor_feedback}")
    
    # Test case 3: Another good match
    question2 = "Explain the CAP theorem and its implications for distributed systems."
    expected_answer2 = "CAP theorem states that distributed systems can only guarantee two of three properties: Consistency, Availability, and Partition tolerance. In practice, network partitions are inevitable, so systems must choose between consistency and availability. CP systems like traditional RDBMS prioritize consistency, potentially becoming unavailable during partitions. AP systems like DNS prioritize availability, potentially serving stale data. CA systems don't exist in real distributed systems."
    candidate_answer2 = "The CAP theorem says you can only have two of three things in distributed systems: Consistency, Availability, and Partition tolerance. Network problems happen so you have to pick consistency or availability. Database systems focus on consistency while DNS focuses on availability."
    
    score2, feedback2 = score_answer(
        text=candidate_answer2,
        question=question2,
        expected_answer=expected_answer2
    )
    
    print(f"\nQuestion 2: {question2}")
    print(f"Expected Answer 2: {expected_answer2}")
    print(f"Candidate Answer 2: {candidate_answer2}")
    print(f"Score 2: {score2}/5")
    print(f"Feedback 2: {feedback2}")
    
    if score > poor_score and score2 >= 3:
        print("\n✅ Keyword matching system working correctly!")
        return True
    else:
        print("\n❌ Keyword matching system not working correctly!")
        return False

def main():
    """Main test function."""
    print("Running Keyword Matching Tests...\n")
    
    success = test_keyword_matching()
    
    print("\n" + "="*50)
    if success:
        print("🎉 All tests passed! Keyword matching system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())