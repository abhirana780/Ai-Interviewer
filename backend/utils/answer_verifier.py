import re
from typing import List, Dict, Tuple

def qa_pairs_from_transcript(text: str) -> List[Tuple[str, str]]:
    if not text:
        return []
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    pairs = []
    q = None
    for ln in lines:
        if ln.startswith("INTERVIEWER:"):
            q = ln.split(":", 1)[1].strip()
        elif ln.startswith("CANDIDATE:") and q is not None:
            a = ln.split(":", 1)[1].strip()
            pairs.append((q, a))
            q = None
    return pairs

class SemanticVerifier:
    def __init__(self):
        self.model = None
        self._init()

    def _init(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception:
            self.model = None

    def score_pair(self, q: str, a: str) -> float:
        q = (q or "").strip()
        a = (a or "").strip()
        if not q or not a or a == "[video_answer]":
            return 0.0
        low = a.lower()
        if "i don't know" in low:
            return 10.0
        if self.model is None:
            # Fallback heuristic: keyword overlap
            q_words = set(re.findall(r"[a-zA-Z]{3,}", q.lower()))
            a_words = set(re.findall(r"[a-zA-Z]{3,}", a.lower()))
            overlap = len(q_words & a_words)
            return min(100.0, 10.0 * overlap)
        try:
            import numpy as np
            emb = self.model.encode([q, a], normalize_embeddings=True)
            sim = float(np.dot(emb[0], emb[1]))
            # map cosine [-1,1] to [0,100]
            return max(0.0, min(100.0, (sim + 1.0) * 50.0))
        except Exception:
            return 0.0

def verify_transcript(text: str) -> Dict:
    pairs = qa_pairs_from_transcript(text)
    ver = SemanticVerifier()
    results = []
    for q, a in pairs:
        score = ver.score_pair(q, a)
        results.append({"question": q, "answer": a, "correctness": round(score, 1)})
    overall = round(sum(r["correctness"] for r in results) / len(results), 1) if results else 0.0
    return {"pairs": results, "overall": overall}

def verify_session(transcript: str, answers: List[Dict]) -> Dict:
    qs = [q for q, _a in qa_pairs_from_transcript(transcript)]
    ans_texts = [ (a.get("answer_text") or "").strip() for a in (answers or []) ]
    # align by index; pad if needed
    n = max(len(qs), len(ans_texts))
    while len(qs) < n: qs.append("")
    while len(ans_texts) < n: ans_texts.append("")
    ver = SemanticVerifier()
    results = []
    for i in range(n):
        q = (qs[i] or "").strip()
        a = (ans_texts[i] or "").strip()
        score = ver.score_pair(q, a)
        results.append({"question": q, "answer": a, "correctness": round(score, 1)})
    overall = round(sum(r["correctness"] for r in results) / len(results), 1) if results else 0.0
    return {"pairs": results, "overall": overall}
