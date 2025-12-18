from backend.utils.scoring import score_answer

# Test cases with expected keywords
test_cases = [
    # Test case 1: Answer with expected keywords
    {
        "answer": "Object-oriented programming uses encapsulation to bundle data and methods together, inheritance to derive classes from parent classes, and polymorphism to allow objects to take multiple forms.",
        "question": "What is object-oriented programming?",
        "track": "General",
        "expected_keywords": ["encapsulation", "inheritance", "polymorphism", "classes", "objects"],
        "description": "Answer with relevant keywords"
    },
    # Test case 2: Answer without expected keywords
    {
        "answer": "Programming is a way to give instructions to computers using languages.",
        "question": "What is object-oriented programming?",
        "track": "General",
        "expected_keywords": ["encapsulation", "inheritance", "polymorphism", "classes", "objects"],
        "description": "Answer without relevant keywords"
    },
    # Test case 3: Refusal phrase
    {
        "answer": "I don't know anything about object-oriented programming.",
        "question": "What is object-oriented programming?",
        "track": "General",
        "expected_keywords": ["encapsulation", "inheritance", "polymorphism", "classes", "objects"],
        "description": "Refusal phrase"
    }
]

print("Testing updated scoring system with expected keywords:")
print("=" * 60)

for i, test_case in enumerate(test_cases, 1):
    score, feedback = score_answer(
        test_case["answer"], 
        question=test_case["question"], 
        track=test_case["track"], 
        expected_keywords=test_case["expected_keywords"]
    )
    print(f"Test {i}: {test_case['description']}")
    print(f"Answer: {test_case['answer']}")
    print(f"Score: {score}/5")
    print(f"Feedback: {feedback}")
    print("-" * 40)