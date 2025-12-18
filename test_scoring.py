from backend.utils.scoring import score_answer

# Test cases
test_cases = [
    ("I don't know anything about this topic", "What is object-oriented programming?", "General"),
    ("", "What is a database index?", "General"),
    ("[video_answer]", "Explain RESTful APIs", "General"),
    ("Object-oriented programming is a programming paradigm based on objects containing data and code. It provides concepts like encapsulation, inheritance, and polymorphism.", "What is object-oriented programming?", "General"),
    ("A database index is a data structure that improves query speed by allowing faster data retrieval. Common types include B-tree, hash, and bitmap indexes.", "What is a database index?", "General"),
]

print("Testing updated scoring system:")
print("=" * 50)

for i, (answer, question, track) in enumerate(test_cases, 1):
    score, feedback = score_answer(answer, question, track)
    print(f"Test {i}:")
    print(f"Answer: {answer}")
    print(f"Score: {score}/5")
    print(f"Feedback: {feedback}")
    print("-" * 30)