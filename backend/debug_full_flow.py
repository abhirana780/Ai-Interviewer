#!/usr/bin/env python3
"""
Debug script to test the full flow from answer submission to scoring and display
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from interviewer import Interviewer
from utils.scoring import score_answer
from database.db_helper import init_db, save_transcript, get_transcript
import tempfile
import json

def test_scoring_flow():
    print("=== DEBUG FULL FLOW TEST ===\n")
    
    # Create a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Initialize database
        init_db(db_path)
        print(f"✓ Created temporary database: {db_path}")
        
        # Create interviewer instance
        model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "models"))
        interviewer = Interviewer(model_dir=model_dir, db_path=db_path)
        print("✓ Created interviewer instance")
        
        # Start a session
        session_id = "test_session_123"
        role = "Software Engineer"
        first_question = interviewer.start_session(session_id, role)
        print(f"✓ Started session with role: {role}")
        print(f"✓ First question: {first_question}")
        
        # Test answer 1 - Good answer that should score well
        good_answer = "A challenging system I designed was a scalable e-commerce platform with high traffic requirements. The key requirements included handling thousands of concurrent users, ensuring data consistency, providing fast response times, and supporting real-time inventory updates. Major constraints were budget limitations, tight deadlines, legacy system integration, and compliance with PCI-DSS security standards. I addressed these by implementing a microservices architecture with load balancing, database sharding, caching layers, and automated testing pipelines."
        
        print("\n--- TESTING GOOD ANSWER ---")
        print(f"Answer: {good_answer[:100]}...")
        
        # Get current question from session
        state = interviewer.sessions.get(session_id) or {}
        questions = state.get("questions", [])
        current_question_obj = questions[0] if questions else {}
        current_question = current_question_obj.get("question", "") if isinstance(current_question_obj, dict) else ""
        expected_answer = current_question_obj.get("expected_answer", "") if isinstance(current_question_obj, dict) else ""
        
        print(f"Current question: {current_question}")
        print(f"Expected answer: {expected_answer[:100]}...")
        
        # Score the answer directly
        score, feedback = score_answer(good_answer, question=current_question, track=role, expected_answer=expected_answer)
        print(f"Direct scoring result - Score: {score}/5, Feedback: {feedback}")
        
        # Process through interviewer handler
        result = interviewer.handle_answer(session_id, good_answer)
        print(f"Interviewer handler result:")
        print(f"  Next question: {result.get('next_question')}")
        print(f"  Score: {result.get('score')}/5")
        print(f"  Feedback: {result.get('feedback')}")
        
        # Test answer 2 - Poor answer that should score poorly
        poor_answer = "I don't know much about this. It's complicated and I'm not sure how to answer properly."
        
        print("\n--- TESTING POOR ANSWER ---")
        print(f"Answer: {poor_answer}")
        
        # Process through interviewer handler
        result2 = interviewer.handle_answer(session_id, poor_answer)
        print(f"Interviewer handler result:")
        print(f"  Next question: {result2.get('next_question')}")
        print(f"  Score: {result2.get('score')}/5")
        print(f"  Feedback: {result2.get('feedback')}")
        
        # Check transcript
        transcript = get_transcript(db_path, session_id)
        print(f"\n--- TRANSCRIPT ---")
        print(transcript)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            os.unlink(db_path)
            print(f"\n✓ Cleaned up temporary database")
        except:
            pass

if __name__ == "__main__":
    test_scoring_flow()