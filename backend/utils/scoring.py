import re
from typing import Tuple, List
import numpy as np

# Import track-specific keywords from prompts
try:
    from utils.prompts import ATS_KEYWORDS
except:
    ATS_KEYWORDS = {}

# AI Model for semantic similarity
try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_MODEL_AVAILABLE = True
except:
    SEMANTIC_MODEL_AVAILABLE = False

# Global model instance (lazy loading)
_SEMANTIC_MODEL = None


def get_semantic_model():
    """Lazy load the semantic similarity model."""
    global _SEMANTIC_MODEL
    if SEMANTIC_MODEL_AVAILABLE and _SEMANTIC_MODEL is None:
        try:
            _SEMANTIC_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            pass
    return _SEMANTIC_MODEL


def compute_semantic_similarity(question: str, answer: str) -> float:
    """Compute semantic similarity between question and answer using AI model."""
    if not question or not answer:
        return 0.0
    
    model = get_semantic_model()
    if model is None:
        # Fallback to keyword overlap if model not available
        q_words = set(re.findall(r'[a-zA-Z]{3,}', question.lower()))
        a_words = set(re.findall(r'[a-zA-Z]{3,}', answer.lower()))
        overlap = len(q_words & a_words)
        return min(1.0, overlap / max(len(q_words), 1) * 2)  # Normalize to 0-1
    
    try:
        # Encode question and answer
        embeddings = model.encode([question, answer], normalize_embeddings=True)
        # Compute cosine similarity (already normalized, so just dot product)
        similarity = float(np.dot(embeddings[0], embeddings[1]))
        # Map from [-1, 1] to [0, 1]
        similarity = (similarity + 1.0) / 2.0
        return max(0.0, min(1.0, similarity))
    except Exception:
        return 0.0


def preprocess_text(text: str) -> str:
    """Preprocess transcribed text for better analysis."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove filler words
    filler_words = r'\b(um|uh|like|you know|basically|actually|literally|sort of|kind of)\b'
    text = re.sub(filler_words, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces after removal
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def analyze_answer_quality(text: str, question: str = "", track: str = "General") -> dict:
    """Analyze answer quality with multiple metrics including AI-based semantic similarity."""
    if not text:
        return {
            "word_count": 0,
            "technical_terms": 0,
            "completeness": 0,
            "uncertainty_level": 0,
            "keyword_matches": [],
            "semantic_similarity": 0.0
        }
    
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)
    
    # Check for uncertainty phrases
    uncertainty_phrases = [
        "i don't know", "not sure", "maybe", "i think", "probably",
        "i guess", "unclear", "don't understand", "no idea"
    ]
    uncertainty_level = sum(1 for phrase in uncertainty_phrases if phrase in text_lower)
    
    # Track-specific keyword matching
    keywords = ATS_KEYWORDS.get(track, ATS_KEYWORDS.get("General", []))
    keyword_matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)]
    
    # Technical depth indicators
    technical_indicators = [
        "algorithm", "complexity", "performance", "optimization", "architecture",
        "design pattern", "scalability", "security", "implementation", "framework",
        "database", "api", "backend", "frontend", "deployment", "testing",
        "integration", "refactoring", "debugging", "monitoring"
    ]
    technical_terms = sum(1 for term in technical_indicators if term in text_lower)
    
    # Completeness score based on word count
    if word_count < 10:
        completeness = 1
    elif word_count < 30:
        completeness = 2
    elif word_count < 60:
        completeness = 3
    elif word_count < 100:
        completeness = 4
    else:
        completeness = 5
    
    # AI-based semantic similarity (if question provided)
    semantic_similarity = 0.0
    if question:
        semantic_similarity = compute_semantic_similarity(question, text)
    
    return {
        "word_count": word_count,
        "technical_terms": technical_terms,
        "completeness": completeness,
        "uncertainty_level": uncertainty_level,
        "keyword_matches": keyword_matches,
        "semantic_similarity": semantic_similarity
    }


def score_answer(text: str, question: str = "", track: str = "General") -> Tuple[int, str]:
    """Enhanced answer scoring with AI-based semantic analysis and intelligent evaluation."""
    
    # Handle empty or placeholder answers
    if not text or text.strip() == "[video_answer]":
        return 3, "Video answer received."
    
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Analyze answer quality (includes AI semantic similarity)
    analysis = analyze_answer_quality(processed_text, question, track)
    
    # Calculate base score
    score = 3  # Default neutral score
    feedback_items = []
    
    # AI Semantic Similarity - Most important factor
    semantic_sim = analysis.get("semantic_similarity", 0.0)
    if semantic_sim > 0.0:
        if semantic_sim >= 0.75:
            score = min(5, score + 2)
            feedback_items.append("Highly relevant answer (AI: {:.0f}%)".format(semantic_sim * 100))
        elif semantic_sim >= 0.55:
            score = min(5, score + 1)
            feedback_items.append("Relevant answer (AI: {:.0f}%)".format(semantic_sim * 100))
        elif semantic_sim >= 0.35:
            feedback_items.append("Moderately relevant (AI: {:.0f}%)".format(semantic_sim * 100))
        else:
            score = max(1, score - 1)
            feedback_items.append("Low relevance to question (AI: {:.0f}%)".format(semantic_sim * 100))
    
    # Penalize for high uncertainty
    if analysis["uncertainty_level"] >= 2:
        score = max(1, score - 2)
        feedback_items.append("Shows significant uncertainty")
    elif analysis["uncertainty_level"] == 1:
        score = max(2, score - 1)
        feedback_items.append("Some uncertainty detected")
    
    # Reward for completeness
    completeness = analysis["completeness"]
    if completeness >= 4:
        score = min(5, score + 1)
        feedback_items.append("Comprehensive answer")
    elif completeness >= 3:
        feedback_items.append("Good detail level")
    elif completeness <= 1:
        score = max(1, score - 1)
        feedback_items.append("Answer too brief")
    
    # Reward for technical depth
    if analysis["technical_terms"] >= 3:
        score = min(5, score + 1)
        feedback_items.append("Strong technical understanding")
    elif analysis["technical_terms"] >= 1:
        feedback_items.append("Some technical terms used")
    
    # Reward for keyword matches
    keyword_count = len(analysis["keyword_matches"])
    if keyword_count >= 3:
        score = min(5, score + 1)
        feedback_items.append(f"Excellent keyword coverage ({keyword_count} matches)")
    elif keyword_count >= 1:
        feedback_items.append(f"Good keyword usage ({keyword_count} matches)")
    
    # Ensure score is within bounds
    score = max(1, min(5, score))
    
    # Build feedback string
    if not feedback_items:
        feedback_items.append("Decent answer")
    
    feedback = " | ".join(feedback_items)
    
    return score, feedback
