import re
from typing import Tuple, List
import numpy as np

# Import our HuggingFaceAnswerMatcher
try:
    from utils.huggingface_matcher import HuggingFaceAnswerMatcher
    HF_MATCHER_AVAILABLE = True
except ImportError:
    HF_MATCHER_AVAILABLE = False

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

# Global HuggingFaceAnswerMatcher instance (lazy loading)
_HF_MATCHER = None


def get_semantic_model():
    """Lazy load the semantic similarity model."""
    global _SEMANTIC_MODEL
    if SEMANTIC_MODEL_AVAILABLE and _SEMANTIC_MODEL is None:
        try:
            _SEMANTIC_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            pass
    return _SEMANTIC_MODEL

def get_hf_matcher():
    """Lazy load the HuggingFaceAnswerMatcher."""
    global _HF_MATCHER
    if HF_MATCHER_AVAILABLE and _HF_MATCHER is None:
        try:
            _HF_MATCHER = HuggingFaceAnswerMatcher()
        except Exception:
            pass
    return _HF_MATCHER


def compute_semantic_similarity(question: str, answer: str) -> float:
    """Compute semantic similarity between question and answer using AI model."""
    if not question or not answer:
        return 0.0
    
    # Try to use HuggingFaceAnswerMatcher first
    hf_matcher = get_hf_matcher()
    if hf_matcher and hf_matcher.model:
        try:
            # Generate expected answer for the question
            expected_answer = hf_matcher.generate_expected_answer(question)
            # Compute similarity between candidate answer and expected answer
            similarity = hf_matcher.compute_similarity(answer, expected_answer)
            return max(0.0, min(1.0, similarity))
        except Exception:
            pass
    
    # Fallback to original sentence transformer approach
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


def analyze_answer_quality(text: str, question: str = "", track: str = "General", expected_keywords: list = None, expected_answer: str = None) -> dict:
    """Analyze answer quality with focus on exact keyword matching with expected answers."""
    if not text:
        return {
            "word_count": 0,
            "technical_terms": 0,
            "completeness": 0,
            "uncertainty_level": 0,
            "refusal_phrases": 0,
            "keyword_matches": [],
            "expected_matches": [],
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
    
    # Check for explicit refusal phrases that should result in zero score
    refusal_phrases = [
        "i don't know", "no idea", "don't know", "can't answer", 
        "no clue", "no answer", "sorry", "cannot answer", "unable to answer",
        "i'm not sure", "not sure", "i have no idea"
    ]
    refusal_count = sum(1 for phrase in refusal_phrases if phrase in text_lower)
    
    # Extract keywords from expected answer for matching
    expected_answer_keywords = []
    if expected_answer:
        # Extract significant words (exclude common stop words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"}
        expected_words = re.findall(r'\b[a-zA-Z]{3,}\b', expected_answer.lower())
        expected_answer_keywords = [word for word in expected_words if word not in stop_words]
    
    # Expected answer keywords matching (higher priority)
    expected_matches = []
    for kw in expected_answer_keywords:
        # Try exact match first
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
            expected_matches.append(kw)
    
    # Track-specific keyword matching
    track_keywords = ATS_KEYWORDS.get(track, ATS_KEYWORDS.get("General", []))
    keyword_matches = [kw for kw in track_keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower)]
    
    # Technical depth indicators
    technical_indicators = [
        "algorithm", "complexity", "performance", "optimization", "architecture",
        "design pattern", "scalability", "security", "implementation", "framework",
        "database", "api", "backend", "frontend", "deployment", "testing",
        "integration", "refactoring", "debugging", "monitoring", "microservices",
        "devops", "ci/cd", "containerization", "kubernetes", "docker", "git",
        "agile", "scrum", "methodology", "requirements", "specification",
        "documentation", "maintenance", "troubleshooting", "benchmarking"
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
    
    # True Semantic matching using AI model
    semantic_similarity = 0.0
    if expected_answer:
        # Use the actual AI semantic similarity function
        try:
            semantic_similarity = compute_semantic_similarity(question, text)
        except Exception:
            # Fallback to keyword matching overlap if AI fails
            if expected_answer_keywords:
                matched_keywords = len(expected_matches)
                total_keywords = len(expected_answer_keywords)
                semantic_similarity = matched_keywords / total_keywords if total_keywords > 0 else 0.0
    
    return {
        "word_count": word_count,
        "technical_terms": technical_terms,
        "completeness": completeness,
        "uncertainty_level": uncertainty_level,
        "refusal_phrases": refusal_count,
        "keyword_matches": keyword_matches,
        "expected_matches": expected_matches,
        "semantic_similarity": semantic_similarity,
        "expected_answer_keywords": expected_answer_keywords
    }


def calculate_detailed_score(analysis: dict, question: str = "") -> Tuple[float, List[str]]:
    """Calculate a detailed score out of 100 with focus on keyword matching."""
    if not analysis:
        return 0.0, ["No analysis data available"]
    
    scores = {}
    feedback_items = []
    
    # Check for refusal phrases first - if present, give zero score
    refusal_count = analysis.get("refusal_phrases", 0)
    if refusal_count > 0:
        total_score = 0.0
        feedback_items.append("Zero score: Refusal phrases detected")
        return total_score, feedback_items
    
    # Check for uncertainty phrases - heavy penalty
    uncertainty_level = analysis.get("uncertainty_level", 0)
    if uncertainty_level > 0:
        # Heavy penalty for uncertainty
        total_score = max(0.0, 20.0 - (uncertainty_level * 15))
        feedback_items.append(f"Low score: Uncertainty detected ({uncertainty_level} phrases)")
        return total_score, feedback_items
    
    # Focus on expected answer keyword matching (70% weight)
    # 1. Semantic Similarity (40% weight) - Using AI model or fallback
    semantic_sim = analysis.get("semantic_similarity", 0.0)
    semantic_score = semantic_sim * 40
    scores["semantic"] = semantic_score
    
    if semantic_sim >= 0.8:
        feedback_items.append(f"Excellent understanding (+{semantic_score:.1f}/40)")
    elif semantic_sim >= 0.6:
        feedback_items.append(f"Good understanding (+{semantic_score:.1f}/40)")
    elif semantic_sim >= 0.4:
        feedback_items.append(f"Moderate understanding (+{semantic_score:.1f}/40)")
    else:
        feedback_items.append(f"Low understanding (+{semantic_score:.1f}/40)")

    # 2. Expected Answer Keywords Match (30% weight or 70% if semantic failed/missing)
    # If semantic score is 0 but keywords are present, we might want to boost keyword weight, 
    # but for now let's keep robust split.
    expected_matches = len(analysis.get("expected_matches", []))
    expected_keywords = analysis.get("expected_answer_keywords", [])
    expected_keywords_count = len(expected_keywords)
    
    expected_match_ratio = expected_matches / max(expected_keywords_count, 1) if expected_keywords_count > 0 else 0
    keyword_weight = 30
    keyword_score = expected_match_ratio * keyword_weight
    scores["expected_keywords"] = keyword_score
    
    if expected_match_ratio >= 0.5:
        feedback_items.append(f"Good keyword usage (+{keyword_score:.1f}/{keyword_weight})")
    elif expected_match_ratio > 0:
        feedback_items.append(f"Some keywords present (+{keyword_score:.1f}/{keyword_weight})")
    else:
        feedback_items.append("Missing key terms")
    
    # 2. Completeness (20% weight) - Is the answer sufficiently detailed?
    completeness = analysis.get("completeness", 0)
    completeness_score = (completeness / 5.0) * 20  # Scale to 20 points
    scores["completeness"] = completeness_score
    
    if completeness >= 4:
        feedback_items.append(f"Comprehensive response (+{completeness_score:.1f}/20)")
    elif completeness >= 3:
        feedback_items.append(f"Adequate detail (+{completeness_score:.1f}/20)")
    elif completeness >= 2:
        feedback_items.append(f"Basic detail (+{completeness_score:.1f}/20)")
    else:
        feedback_items.append(f"Insufficient detail (+{completeness_score:.1f}/20)")
    
    # 3. Confidence Bonus (10% weight) - Reward confidence
    word_count = analysis.get("word_count", 0)
    # Bonus for substantial answers
    if word_count >= 50:
        confidence_score = 10.0  # Maximum bonus
        feedback_items.append("Strong response length (+10/10)")
    elif word_count >= 30:
        confidence_score = 5.0
        feedback_items.append("Good response length (+5/10)")
    elif word_count >= 15:
        confidence_score = 2.0
        feedback_items.append("Adequate response length (+2/10)")
    else:
        confidence_score = 0.0  # No bonus for short answers
    scores["confidence"] = confidence_score
    
    # Calculate total score
    total_score = sum(scores.values())
    
    # Ensure score is within bounds
    total_score = max(0.0, min(100.0, total_score))
    
    return total_score, feedback_items

def score_answer(text: str, question: str = "", track: str = "General", expected_keywords: list = None, expected_answer: str = None) -> Tuple[int, str]:
    """Enhanced answer scoring with detailed analysis and 100-point scale."""
    
    # Handle empty or placeholder answers
    if not text or not text.strip() or text.strip() == "[video_answer]":
        return 1, "No answer provided - Zero score."
    
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Check for completely blank or whitespace-only answers
    if not processed_text:
        return 1, "Blank answer - Zero score."
    
    # Analyze answer quality (focus on keyword matching with expected answer)
    analysis = analyze_answer_quality(processed_text, question, track, expected_keywords, expected_answer)
    
    # Calculate detailed score
    detailed_score, feedback_items = calculate_detailed_score(analysis, question)
    
    # Convert to 1-5 scale for compatibility
    scaled_score = max(1, min(5, round(detailed_score / 20)))
    
    # Special case: If we detected refusal phrases, ensure we return a 1 (lowest score)
    if analysis.get("refusal_phrases", 0) > 0 or analysis.get("uncertainty_level", 0) > 0:
        scaled_score = 1
    
    # Add overall score to feedback
    feedback_items.insert(0, f"Overall Score: {detailed_score:.1f}/100")
    
    # Build feedback string
    feedback = " | ".join(feedback_items)
    
    return scaled_score, feedback
