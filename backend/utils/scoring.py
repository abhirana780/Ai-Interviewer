def score_answer(text):
    text = text.lower()

    if not text or text.strip() == "[video_answer]":
        return 3, "Video answer received."

    score = 3
    feedback = []

    if "algorithm" in text:
        score = 4
        feedback.append("Mentions algorithmic understanding.")

    if "time complexity" in text or "space complexity" in text:
        score = 5
        feedback.append("Understands complexity analysis.")

    if "i don't know" in text:
        score = 1
        feedback.append("Shows uncertainty.")

    return score, " | ".join(feedback) or "Decent answer."
