import re

# Test the keyword matching logic
expected_keywords = ["requirements", "constraints", "architecture", "scalability", "performance", "design decisions"]
text = "When designing a system, I always consider the requirements and constraints first. The architecture needs to be scalable and performant. Good design decisions are crucial for long-term success."
text_lower = text.lower()

print("Testing keyword matching:")
print(f"Text: {text}")
print()

for kw in expected_keywords:
    # Current matching logic
    match = re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)
    if match:
        print(f"✓ '{kw}' matched")
    else:
        print(f"✗ '{kw}' did not match")

print()
print("Checking specific words:")
print(f"'scalability' in text: {'scalability' in text_lower}")
print(f"'scalable' in text: {'scalable' in text_lower}")
print(f"'performance' in text: {'performance' in text_lower}")
print(f"'performant' in text: {'performant' in text_lower}")