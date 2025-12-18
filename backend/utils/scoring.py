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


def analyze_answer_quality(text: str, question: str = "", track: str = "General", expected_keywords: list = None) -> dict:
    """Analyze answer quality with multiple metrics including AI-based semantic similarity."""
    if not text:
        return {
            "word_count": 0,
            "technical_terms": 0,
            "completeness": 0,
            "uncertainty_level": 0,
            "refusal_phrases": 0,
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
    
    # Check for explicit refusal phrases that should result in zero score
    refusal_phrases = [
        "i don't know", "no idea", "don't know", "can't answer", 
        "no clue", "no answer", "sorry", "cannot answer", "unable to answer",
        "i'm not sure", "not sure", "i have no idea"
    ]
    refusal_count = sum(1 for phrase in refusal_phrases if phrase in text_lower)
    
    # Track-specific keyword matching
    track_keywords = ATS_KEYWORDS.get(track, ATS_KEYWORDS.get("General", []))
    
    # Expected answer keywords matching (higher priority)
    expected_keywords = expected_keywords or []
    expected_matches = []
    for kw in expected_keywords:
        # Try exact match first
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
            expected_matches.append(kw)
        # Try fuzzy matching for flexibility (handles word variations like "scalability" vs "scalable")
        else:
            kw_clean = re.sub(r'[^\w\s]', '', kw.lower())  # Remove punctuation
            text_clean = re.sub(r'[^\w\s]', '', text_lower)  # Remove punctuation
            
            # For single words, check if they're related
            if ' ' not in kw_clean:
                # Check if keyword is contained in any word in text or vice versa
                text_words = text_clean.split()
                for word in text_words:
                    if kw_clean in word or word in kw_clean:
                        expected_matches.append(kw)
                        break
            # For multi-word keywords, check if all parts are present
            else:
                kw_parts = kw_clean.split()
                if all(any(part in word for word in text_clean.split()) for part in kw_parts):
                    expected_matches.append(kw)
    # Track-specific keyword matching
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
    
    # AI-based semantic similarity (if question provided)
    semantic_similarity = 0.0
    if question:
        semantic_similarity = compute_semantic_similarity(question, text)
    
    return {
        "word_count": word_count,
        "technical_terms": technical_terms,
        "completeness": completeness,
        "uncertainty_level": uncertainty_level,
        "refusal_phrases": refusal_count,
        "keyword_matches": keyword_matches,
        "expected_matches": expected_matches,
        "semantic_similarity": semantic_similarity
    }


def calculate_detailed_score(analysis: dict, question: str = "") -> Tuple[float, List[str]]:
    """Calculate a detailed score out of 100 with component breakdown."""
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
    
    # Check for expected keywords - heavily weighted
    expected_matches = len(analysis.get("expected_matches", []))
    expected_keywords_count = analysis.get("expected_keywords_count", 0)
    
    # 1. Expected Keywords Match (40% weight) - How well does the answer match expected keywords?
    expected_match_ratio = expected_matches / max(expected_keywords_count, 1) if expected_keywords_count > 0 else 0
    expected_score = expected_match_ratio * 40  # Scale to 40 points
    scores["expected_keywords"] = expected_score
    
    if expected_match_ratio >= 0.8:
        feedback_items.append(f"Excellent keyword match (+{expected_score:.1f}/40)")
    elif expected_match_ratio >= 0.6:
        feedback_items.append(f"Good keyword match (+{expected_score:.1f}/40)")
    elif expected_match_ratio >= 0.4:
        feedback_items.append(f"Moderate keyword match (+{expected_score:.1f}/40)")
    elif expected_match_ratio >= 0.2:
        feedback_items.append(f"Low keyword match (+{expected_score:.1f}/40)")
    else:
        feedback_items.append(f"Poor keyword match (+{expected_score:.1f}/40)")
    
    # 2. Semantic Relevance (20% weight) - How well does the answer relate to the question?
    semantic_sim = analysis.get("semantic_similarity", 0.0)
    semantic_score = semantic_sim * 20  # Scale to 20 points
    scores["semantic"] = semantic_score
    
    if semantic_sim >= 0.8:
        feedback_items.append(f"Excellent semantic relevance (+{semantic_score:.1f}/20)")
    elif semantic_sim >= 0.6:
        feedback_items.append(f"Good semantic relevance (+{semantic_score:.1f}/20)")
    elif semantic_sim >= 0.4:
        feedback_items.append(f"Moderate semantic relevance (+{semantic_score:.1f}/20)")
    elif semantic_sim >= 0.2:
        feedback_items.append(f"Low semantic relevance (+{semantic_score:.1f}/20)")
    else:
        feedback_items.append(f"Poor semantic relevance (+{semantic_score:.1f}/20)")
    
    # 2. Completeness (15% weight) - Is the answer sufficiently detailed?
    completeness = analysis.get("completeness", 0)
    completeness_score = (completeness / 5.0) * 15  # Scale to 15 points
    scores["completeness"] = completeness_score
    
    if completeness >= 4:
        feedback_items.append(f"Comprehensive response (+{completeness_score:.1f}/15)")
    elif completeness >= 3:
        feedback_items.append(f"Adequate detail (+{completeness_score:.1f}/15)")
    elif completeness >= 2:
        feedback_items.append(f"Basic detail (+{completeness_score:.1f}/15)")
    else:
        feedback_items.append(f"Insufficient detail (+{completeness_score:.1f}/15)")
    
    # 3. Technical Depth (20% weight) - Does the answer show technical expertise?
    tech_terms = analysis.get("technical_terms", 0)
    # Cap at 10 technical terms for maximum score
    tech_score = min(20.0, (tech_terms / 10.0) * 20)  # Scale to 20 points
    scores["technical"] = tech_score
    
    if tech_terms >= 7:
        feedback_items.append(f"Strong technical vocabulary (+{tech_score:.1f}/20)")
    elif tech_terms >= 4:
        feedback_items.append(f"Good technical vocabulary (+{tech_score:.1f}/20)")
    elif tech_terms >= 1:
        feedback_items.append(f"Some technical terms (+{tech_score:.1f}/20)")
    else:
        feedback_items.append(f"Limited technical vocabulary (+{tech_score:.1f}/20)")
    
    # 4. Keyword Usage (15% weight) - Track-specific terminology
    keyword_count = len(analysis.get("keyword_matches", []))
    # Cap at 10 keywords for maximum score
    keyword_score = min(15.0, (keyword_count / 10.0) * 15)  # Scale to 15 points
    scores["keywords"] = keyword_score
    
    if keyword_count >= 5:
        feedback_items.append(f"Excellent keyword usage (+{keyword_score:.1f}/15)")
    elif keyword_count >= 3:
        feedback_items.append(f"Good keyword usage (+{keyword_score:.1f}/15)")
    elif keyword_count >= 1:
        feedback_items.append(f"Some relevant keywords (+{keyword_score:.1f}/15)")
    else:
        feedback_items.append(f"Few relevant keywords (+{keyword_score:.1f}/15)")
    
    # 5. Confidence Bonus (10% weight) - Reward confidence
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

def score_answer(text: str, question: str = "", track: str = "General", expected_keywords: list = None) -> Tuple[int, str]:
    """Enhanced answer scoring with detailed analysis and 100-point scale."""
    
    # Handle empty or placeholder answers
    if not text or not text.strip() or text.strip() == "[video_answer]":
        return 1, "No answer provided - Zero score."
    
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Check for completely blank or whitespace-only answers
    if not processed_text:
        return 1, "Blank answer - Zero score."
    
    # Analyze answer quality (includes AI semantic similarity)
    analysis = analyze_answer_quality(processed_text, question, track, expected_keywords)
    # Add expected keywords count for scoring
    analysis["expected_keywords_count"] = len(expected_keywords) if expected_keywords else 0
    
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
