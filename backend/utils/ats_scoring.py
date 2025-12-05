import re
from typing import Tuple, Dict, Any, List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except Exception:
    ST_AVAILABLE = False

_ST_MODEL = None

try:
    from utils.prompts import ROLE_DESCRIPTIONS, ATS_KEYWORDS
except Exception:
    ROLE_DESCRIPTIONS = {
        "General": "General software role"
    }
    ATS_KEYWORDS = {
        "General": ["python", "java", "sql", "git", "docker", "api", "testing", "cloud"]
    }


def _normalize(text: str) -> str:
    t = (text or "")
    t = t.replace("\r", "\n")
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def _keyword_coverage(text: str, keywords: List[str]) -> Tuple[int, int, List[str]]:
    hits = 0
    matched = []
    t = text.lower()
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", t):
            hits += 1
            matched.append(kw)
    total = max(len(keywords), 1)
    return hits, total, matched


def _formatting_signals(text: str) -> Dict[str, Any]:
    t = text.lower()
    sections = [s for s in ["experience", "education", "skills", "projects", "summary"] if s in t]
    has_email = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
    has_phone = bool(re.search(r"\+?\d[\d\s().-]{7,}\d", text))
    bullet_like = text.count("\n-") + text.count("\n*") + text.count("•")
    length = max(len(text), 1)
    bullet_ratio = min(bullet_like / (length / 80.0), 1.0)
    return {
        "sections": sections,
        "contact_email": has_email,
        "contact_phone": has_phone,
        "bullet_ratio": round(bullet_ratio, 3)
    }


def compute_ats_score(text: str, track: str = "General") -> Tuple[int, str, Dict[str, Any]]:
    """Compute ATS score combining sentence-transformer (if available) or TF-IDF similarity, keyword coverage, and formatting signals."""
    resume_text = _normalize(text or "")
    role_desc = _normalize(ROLE_DESCRIPTIONS.get(track, ROLE_DESCRIPTIONS.get("General", "")))
    keywords = ATS_KEYWORDS.get(track, ATS_KEYWORDS.get("General", []))

    tfidf_sim = 0.0
    if SKLEARN_AVAILABLE and (resume_text and role_desc):
        try:
            vec = TfidfVectorizer(stop_words="english")
            X = vec.fit_transform([role_desc, resume_text])
            tfidf_sim = float(cosine_similarity(X[0].toarray(), X[1].toarray())[0][0])
        except Exception:
            tfidf_sim = 0.0

    st_sim = 0.0
    if ST_AVAILABLE and (resume_text and role_desc):
        global _ST_MODEL
        try:
            if _ST_MODEL is None:
                _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            import numpy as np
            e1 = _ST_MODEL.encode([role_desc])[0]
            e2 = _ST_MODEL.encode([resume_text])[0]
            denom = float(np.linalg.norm(e1) * np.linalg.norm(e2)) or 1e-8
            st_sim = float(np.dot(e1, e2) / denom)
            if st_sim < -1.0:
                st_sim = -1.0
            if st_sim > 1.0:
                st_sim = 1.0
        except Exception:
            st_sim = 0.0

    main_sim = st_sim if (ST_AVAILABLE and _ST_MODEL is not None) else tfidf_sim

    hits, total, matched = _keyword_coverage(resume_text, keywords)
    coverage = hits / total if total > 0 else 0.0
    missing = [kw for kw in keywords if kw not in matched]

    fmt = _formatting_signals(resume_text)
    fmt_bonus = 0
    if fmt.get("contact_email"):
        fmt_bonus += 2
    if fmt.get("contact_phone"):
        fmt_bonus += 2
    if len(fmt.get("sections", [])) >= 3:
        fmt_bonus += 3
    fmt_bonus = min(fmt_bonus, 10)

    base_score = (main_sim * 60.0) + (coverage * 40.0)
    score = int(min(100, round(base_score + fmt_bonus)))

    details = (
        f"Similarity={main_sim:.2f} ({'ST' if (ST_AVAILABLE and _ST_MODEL is not None) else 'TFIDF'}), "
        f"Keywords={hits}/{total} ({coverage*100:.0f}%), Formatting bonus={fmt_bonus}"
    )
    breakdown = {
        "tfidf_similarity": tfidf_sim,
        "st_similarity": st_sim,
        "keyword_hits": hits,
        "keyword_total": total,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "coverage": coverage,
        "formatting": fmt
    }
    return score, details, breakdown