from backend.utils.scoring import score_answer, analyze_answer_quality

# Test with expected keywords
expected_keywords = ["requirements", "constraints", "architecture", "scalability", "performance", "design decisions"]
answer = "When designing a system, I always consider the requirements and constraints first. The architecture needs to be scalable and performant. Good design decisions are crucial for long-term success."
question = "Describe a challenging system you designed. What were the requirements and constraints?"

print("Testing with expected keywords:")
print(f"Expected keywords: {expected_keywords}")
print(f"Answer: {answer}")
print()

analysis = analyze_answer_quality(answer, question, "Software Engineer", expected_keywords)
print(f"Analysis: {analysis}")
print()

score, feedback = score_answer(answer, question, "Software Engineer", expected_keywords)
print(f"Score: {score}/5")
print(f"Feedback: {feedback}")