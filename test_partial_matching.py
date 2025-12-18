import re

# Test the improved keyword matching logic
expected_keywords = ["requirements", "constraints", "architecture", "scalability", "performance", "design decisions"]
text = "When designing a system, I always consider the requirements and constraints first. The architecture needs to be scalable and performant. Good design decisions are crucial for long-term success."
text_lower = text.lower()

print("Testing improved keyword matching:")
print(f"Text: {text}")
print()

for kw in expected_keywords:
    # Try exact match first
    if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
        print(f"✓ Exact match: '{kw}'")
    # Try partial match for flexibility
    elif any(word.startswith(kw.lower().split()[0]) for word in text_lower.split()):
        print(f"~ Partial match: '{kw}'")
    else:
        print(f"✗ No match: '{kw}'")

print()
print("Debugging partial matching:")
for kw in ["scalability", "performance"]:
    first_word = kw.lower().split()[0]
    print(f"Keyword: '{kw}' -> first word: '{first_word}'")
    matching_words = [word for word in text_lower.split() if word.startswith(first_word)]
    print(f"Words in text starting with '{first_word}': {matching_words}")