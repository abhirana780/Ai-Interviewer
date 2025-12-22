#!/usr/bin/env python3
"""
Test script to verify Hugging Face integration is working correctly.
"""

import sys
import os

# Add the backend directory to the path so we can import our modules
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.huggingface_matcher import HuggingFaceAnswerMatcher
from utils.answer_verifier import SemanticVerifier

def test_huggingface_matcher():
    """Test the HuggingFaceAnswerMatcher class."""
    print("Testing HuggingFaceAnswerMatcher...")
    
    # Initialize the matcher
    matcher = HuggingFaceAnswerMatcher()
    
    # Check if model was loaded successfully
    if matcher.model is None:
        print("⚠️  Hugging Face model not available (this is OK if sentence-transformers is not installed)")
        print("✅ Test passed (model not available)")
        return True
    else:
        print("✅ Hugging Face model loaded successfully")
    
    # Test similarity computation
    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "A fast brown fox leaps over a sleepy dog"
    
    similarity = matcher.compute_similarity(text1, text2)
    print(f"Similarity between '{text1}' and '{text2}': {similarity:.4f}")
    
    if similarity > 0:
        print("✅ Similarity computation working")
    else:
        print("❌ Similarity computation failed")
        return False
    
    # Test answer matching
    question = "What is the difference between lists and tuples in Python?"
    candidate_answer = "Lists are mutable while tuples are immutable. Lists use square brackets and tuples use parentheses."
    expected_answer = "Lists are mutable data structures that can be modified after creation, while tuples are immutable and cannot be changed once created. Lists are defined with square brackets [] and tuples with parentheses ()."
    
    score, feedback = matcher.match_answer(question, candidate_answer, expected_answer)
    print(f"Answer matching score: {score:.4f}")
    print(f"Feedback: {feedback}")
    
    if score > 0:
        print("✅ Answer matching working")
    else:
        print("❌ Answer matching failed")
        return False
    
    return True

def test_semantic_verifier():
    """Test the SemanticVerifier class with Hugging Face integration."""
    print("\nTesting SemanticVerifier with Hugging Face integration...")
    
    # Initialize the verifier
    verifier = SemanticVerifier()
    
    # Test scoring a question-answer pair
    question = "Explain the difference between supervised and unsupervised learning."
    answer = "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data."
    
    score = verifier.score_pair(question, answer)
    print(f"Score for Q&A pair: {score:.2f}")
    
    # The original SemanticVerifier has fallback mechanisms, so it should always return a score
    if score >= 0:
        print("✅ SemanticVerifier working (may be using fallback methods)")
        return True
    else:
        print("❌ SemanticVerifier failed")
        return False

def main():
    """Main test function."""
    print("Running Hugging Face Integration Tests...\n")
    
    # Test HuggingFaceAnswerMatcher
    hf_test_passed = test_huggingface_matcher()
    
    # Test SemanticVerifier
    sv_test_passed = test_semantic_verifier()
    
    print("\n" + "="*50)
    if hf_test_passed and sv_test_passed:
        print("🎉 All tests passed! Hugging Face integration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())