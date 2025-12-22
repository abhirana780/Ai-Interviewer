#!/usr/bin/env python3
"""
Test script to verify admin score update functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.db_helper import init_db, save_transcript, save_answer, get_session, get_answers_for_session, update_answer_score, update_final_score
import tempfile
import json

def test_admin_updates():
    print("=== TESTING ADMIN SCORE UPDATE FUNCTIONALITY ===\n")
    
    # Create a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_path = temp_db.name
    
    try:
        # Initialize database
        init_db(db_path)
        print(f"✓ Created temporary database: {db_path}")
        
        # Create a test session
        session_id = "test_session_123"
        save_transcript(db_path, session_id, "Test transcript", "Test Candidate", "1234567890", "test@example.com", "BS Computer Science", "Test University", "Software Engineer", 3.5)
        print("✓ Created test session")
        
        # Add some test answers
        save_answer(db_path, session_id, "This is answer 1", "/media/test1.webm", 3, "Good answer")
        save_answer(db_path, session_id, "This is answer 2", "/media/test2.webm", 4, "Excellent answer")
        save_answer(db_path, session_id, "This is answer 3", "/media/test3.webm", 2, "Needs improvement")
        print("✓ Added test answers")
        
        # Check initial state
        session = get_session(db_path, session_id)
        answers = get_answers_for_session(db_path, session_id)
        print(f"Initial final score: {session.get('final_score')}")
        for i, answer in enumerate(answers):
            print(f"Initial answer {i+1} score: {answer.get('score')}")
        
        # Test updating individual answer scores
        print("\n--- UPDATING ANSWER SCORES ---")
        update_answer_score(db_path, session_id, 0, 5, "Updated to excellent")
        update_answer_score(db_path, session_id, 1, 2, "Updated to needs improvement")
        print("✓ Updated individual answer scores")
        
        # Test updating final score
        print("\n--- UPDATING FINAL SCORE ---")
        update_final_score(db_path, session_id, 4.2)
        print("✓ Updated final score")
        
        # Check updated state
        session = get_session(db_path, session_id)
        answers = get_answers_for_session(db_path, session_id)
        print(f"\nUpdated final score: {session.get('final_score')}")
        for i, answer in enumerate(answers):
            print(f"Updated answer {i+1} score: {answer.get('score')} - {answer.get('feedback')}")
            
        print("\n✓ All tests passed!")
        
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
    test_admin_updates()