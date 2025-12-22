#!/usr/bin/env python3
"""
Test script to verify the new answer generation and matching system.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.huggingface_matcher import HuggingFaceAnswerMatcher
from utils.scoring import compute_semantic_similarity

def test_answer_generation():
    """Test the answer generation functionality."""
    print("Testing answer generation...")
    
    # Initialize the matcher
    matcher = HuggingFaceAnswerMatcher()
    
    # Test with a sample question
    question = "What is the difference between lists and tuples in Python?"
    
    # Generate an expected answer
    expected_answer = matcher.generate_expected_answer(question)
    print(f"Question: {question}")
    print(f"Generated Expected Answer: {expected_answer}")
    
    if expected_answer and len(expected_answer) > 0:
        print("✅ Answer generation working")
        return True
    else:
        print("❌ Answer generation failed")
        return False

def test_sentence_similarity():
    """Test the sentence similarity matching."""
    print("\nTesting sentence similarity matching...")
    
    # Test with a sample question and answers
    question = "What is the difference between lists and tuples in Python?"
    
    # Generate an expected answer
    matcher = HuggingFaceAnswerMatcher()
    expected_answer = matcher.generate_expected_answer(question)
    
    # Test with a good candidate answer
    candidate_answer_good = "Lists are mutable data structures that can be modified after creation, while tuples are immutable and cannot be changed once created."
    
    # Test with a poor candidate answer
    candidate_answer_poor = "I don't know the difference."
    
    # Compute similarities
    similarity_good = compute_semantic_similarity(question, candidate_answer_good)
    similarity_poor = compute_semantic_similarity(question, candidate_answer_poor)
    similarity_expected = compute_semantic_similarity(question, expected_answer)
    
    print(f"Question: {question}")
    print(f"Expected Answer: {expected_answer}")
    print(f"Good Candidate Answer: {candidate_answer_good}")
    print(f"Poor Candidate Answer: {candidate_answer_poor}")
    print(f"Similarity (Good Answer): {similarity_good:.4f}")
    print(f"Similarity (Poor Answer): {similarity_poor:.4f}")
    print(f"Similarity (Expected Answer): {similarity_expected:.4f}")
    
    # Check that the good answer has higher similarity than the poor one
    if similarity_good > similarity_poor:
        print("✅ Sentence similarity matching working correctly")
        return True
    else:
        print("❌ Sentence similarity matching not working correctly")
        return False

def test_integration():
    """Test the full integration."""
    print("\nTesting full integration...")
    
    # Test with a more complex example
    question = "Explain the concept of object-oriented programming and its key principles."
    
    matcher = HuggingFaceAnswerMatcher()
    expected_answer = matcher.generate_expected_answer(question)
    
    # Good detailed answer
    candidate_answer = """Object-oriented programming (OOP) is a programming paradigm based on the concept of objects, which can contain data and code. The key principles of OOP include encapsulation, inheritance, polymorphism, and abstraction. Encapsulation refers to bundling data and methods that operate on that data within a single unit or class. Inheritance allows classes to inherit properties and methods from parent classes. Polymorphism enables objects to take multiple forms and behave differently based on their type. Abstraction hides complex implementation details and exposes only essential features."""
    
    # Compute similarity
    similarity = compute_semantic_similarity(question, candidate_answer)
    
    print(f"Question: {question}")
    print(f"Expected Answer: {expected_answer}")
    print(f"Candidate Answer: {candidate_answer}")
    print(f"Similarity Score: {similarity:.4f}")
    
    if similarity > 0.3:  # Should be reasonably high for a good answer
        print("✅ Full integration working")
        return True
    else:
        print("❌ Full integration not working correctly")
        return False

def main():
    """Main test function."""
    print("Running Answer Generation and Matching Tests...\n")
    
    # Test answer generation
    gen_test_passed = test_answer_generation()
    
    # Test sentence similarity
    sim_test_passed = test_sentence_similarity()
    
    # Test full integration
    int_test_passed = test_integration()
    
    print("\n" + "="*50)
    if gen_test_passed and sim_test_passed and int_test_passed:
        print("🎉 All tests passed! Answer generation and matching system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())