import re

def sanitize_text(text):
    return (text or "").replace("\r", "").strip()


def _clean_name(name):
    name = sanitize_text(name)
    if not name:
        return None
    # Remove trailing punctuation and extra spaces
    name = re.sub(r"[\.,;:!\?]+$", "", name).strip()
    # Limit to 3 tokens, title-case each
    parts = [p for p in re.split(r"\s+", name) if p]
    parts = parts[:3]
    if not parts:
        return None
    # Title-case tokens (handle apostrophes and hyphens)
    def tc(token):
        return "-".join([sub.capitalize() for sub in token.split("-")])
    parts = [tc(p) for p in parts]
    # Basic sanity: avoid non-name phrases
    bad = set(["the", "a", "an", "and", "or", "but", "of", "for", "to", "with", "in", "on", "at", "from"])
    if parts[0].lower() in bad:
        return None
    return " ".join(parts)


def parse_name(transcript):
    """
    Extract a likely name from a free-form introduction.
    Heuristics:
    - Prefer patterns like:
      "my name is X", "I am X", "I'm X", "this is X", "name: X", "hello, I'm X", "hi, I'm X".
    - Capture up to 3 tokens for the name.
    - Fallback: use the first short, capitalizable token(s) from the start of the transcript.
    Returns a cleaned title-cased name or None if not confident.
    """
    text = sanitize_text(transcript)
    if not text:
        return None

    # Try common explicit patterns first
    patterns = [
        r"\bmy\s+name\s+is\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bi\s*am\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bi'?m\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bthis\s+is\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bname\s*:\s*([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bhello[\s,]+i'?m\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
        r"\bhi[\s,]+i'?m\s+([A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){0,2})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            candidate = _clean_name(m.group(1))
            if candidate:
                return candidate

    # Fallback: inspect the beginning of the transcript for likely name tokens
    # Take the first sentence up to 120 chars
    first = re.split(r"[\.!?\n]", text, maxsplit=1)[0].strip()
    first = first[:120]
    tokens = [t for t in re.split(r"\s+", first) if t]
    # Remove typical greetings/fillers
    stop = {"hello", "hi", "hey", "greetings", "this", "is", "i", "am", "i'm", "my", "name", "the", "a"}
    filtered = [t for t in tokens if t.lower() not in stop]
    # Build a 1-3 token name and clean
    if filtered:
        guess = " ".join(filtered[:3])
        candidate = _clean_name(guess)
        return candidate

    return None