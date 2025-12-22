#!/usr/bin/env python3
"""
Simple test to verify scoring functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.scoring import score_answer

def test_scoring():
    print("=== SIMPLE SCORING TEST ===\n")
    
    # Test case 1: Matching answer
    question = "Describe your approach to optimizing application performance."
    expected_answer = "My approach to performance optimization starts with profiling to identify bottlenecks using tools like profilers, APMs, and custom metrics. I optimize database queries with proper indexing, query analysis, and caching strategies. I implement lazy loading, pagination, and asynchronous processing where appropriate. I optimize front-end performance with code splitting, asset compression, and CDN usage. I use connection pooling, caching layers, and efficient algorithms. I monitor key metrics like response time, throughput, and resource utilization. I conduct load testing and implement auto-scaling. I follow performance best practices from the beginning rather than optimizing reactively."
    
    good_answer = "My approach to performance optimization starts with profiling to identify bottlenecks using tools like profilers, APMs, and custom metrics. I optimize database queries with proper indexing, query analysis, and caching strategies. I implement lazy loading, pagination, and asynchronous processing where appropriate. I optimize front-end performance with code splitting, asset compression, and CDN usage. I use connection pooling, caching layers, and efficient algorithms. I monitor key metrics like response time, throughput, and resource utilization. I conduct load testing and implement auto-scaling. I follow performance best practices from the beginning rather than optimizing reactively."
    
    score, feedback = score_answer(good_answer, question=question, track="Software Engineer", expected_answer=expected_answer)
    print(f"Test 1 - Perfect match:")
    print(f"  Score: {score}/5")
    print(f"  Feedback: {feedback}\n")
    
    # Test case 2: Partial match
    partial_answer = "I optimize performance by using caching and database indexing. I also monitor response times and use CDNs for static assets."
    
    score2, feedback2 = score_answer(partial_answer, question=question, track="Software Engineer", expected_answer=expected_answer)
    print(f"Test 2 - Partial match:")
    print(f"  Score: {score2}/5")
    print(f"  Feedback: {feedback2}\n")
    
    # Test case 3: Poor match
    poor_answer = "I don't really know much about performance optimization. It seems complicated and I haven't worked on it much."
    
    score3, feedback3 = score_answer(poor_answer, question=question, track="Software Engineer", expected_answer=expected_answer)
    print(f"Test 3 - Poor match:")
    print(f"  Score: {score3}/5")
    print(f"  Feedback: {feedback3}\n")

if __name__ == "__main__":
    test_scoring()