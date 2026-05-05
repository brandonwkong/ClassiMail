"""
Email ranking module.

Provides both static (rule-based) and ML-based ranking.
Start with static formula, swap to ML model once enough interaction data is collected.
"""

from typing import Dict, Any, List, Optional
import json
import os

# Weights for static ranking formula (tunable)
CATEGORY_WEIGHTS = {
    'job interview': 1.0,
    'interview': 1.0,
    'next steps': 0.95,
    'job offer': 1.0,
    'offer': 1.0,
    'job rejection': 0.5,
    'rejection': 0.5,
    'job application': 0.4,
    'thank you': 0.3,
    'notification': 0.3,
    'spam': 0.05,
    'promo': 0.05,
    'other': 0.2,
}


def get_category_weight(category: str) -> float:
    """Get weight for a category (fuzzy matching)."""
    category_lower = category.lower()
    for key, weight in CATEGORY_WEIGHTS.items():
        if key in category_lower:
            return weight
    return 0.2  # default


def compute_static_rank_score(features: Dict[str, Any]) -> float:
    """
    Compute ranking score using a static formula.

    Score components:
    1. Category importance (0-1)
    2. Recency decay (0-1)
    3. Keyword signals (0-0.3)
    4. Sender familiarity (0-0.2)
    5. Urgency signals (0-0.2)

    Returns: float between 0 and 1
    """
    score = 0.0

    # 1. Category importance (weight: 35%)
    category = features.get('category', 'Other')
    category_score = get_category_weight(category)
    score += category_score * 0.35

    # 2. Recency decay (weight: 25%)
    # Full score if < 1 hour, decays to 0 over 1 week
    recency_hours = features.get('recency_hours', 168)
    recency_score = max(0, 1 - (recency_hours / 168))
    score += recency_score * 0.25

    # 3. Keyword signals (weight: 20%)
    keyword_score = 0.0
    if features.get('is_interview') or features.get('has_interview_keyword'):
        keyword_score = 1.0
    elif features.get('is_offer') or features.get('has_offer_keyword'):
        keyword_score = 1.0
    elif features.get('has_action_keyword'):
        keyword_score = 0.7
    elif features.get('is_rejection') or features.get('has_rejection_keyword'):
        keyword_score = 0.4
    elif features.get('is_spam'):
        keyword_score = 0.0
    else:
        keyword_score = 0.3
    score += keyword_score * 0.20

    # 4. Sender familiarity (weight: 10%)
    # More emails from sender = more important (up to a point)
    sender_freq = features.get('sender_frequency', 0)
    familiarity_score = min(sender_freq / 5, 1.0)  # caps at 5 emails
    score += familiarity_score * 0.10

    # 5. Urgency signals (weight: 10%)
    urgency_score = 0.0
    if features.get('has_urgent_keyword'):
        urgency_score += 0.5
    if features.get('exclamation_count', 0) > 0:
        urgency_score += 0.2
    if features.get('has_question'):
        urgency_score += 0.1
    if features.get('has_attachment'):
        urgency_score += 0.2
    urgency_score = min(urgency_score, 1.0)
    score += urgency_score * 0.10

    return round(score, 4)


def rank_emails(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank a list of emails by importance score.

    Each email dict should have a 'features' key with extracted features.
    Adds 'rank_score' and 'rank_position' to each email.

    Returns: Sorted list (highest score first)
    """
    # Compute scores
    for email in emails:
        features = email.get('features', {})
        email['rank_score'] = compute_static_rank_score(features)

    # Sort by score descending
    ranked = sorted(emails, key=lambda x: x['rank_score'], reverse=True)

    # Add position
    for i, email in enumerate(ranked):
        email['rank_position'] = i + 1

    return ranked


# ----- ML-based ranking (for later) -----

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'ranker_model.pkl')


def load_ml_model():
    """Load trained ranking model if available."""
    if os.path.exists(MODEL_PATH):
        import pickle
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    return None


def compute_ml_rank_score(features: Dict[str, Any], model) -> float:
    """
    Compute ranking score using trained ML model.

    Requires: trained model from training/train_ranker.py
    """
    from features import features_to_vector

    feature_vector = features_to_vector(features)
    score = model.predict_proba([feature_vector])[0][1]  # probability of "important"
    return round(float(score), 4)


def compute_rank_score(features: Dict[str, Any]) -> float:
    """
    Main ranking function - uses ML model if available, falls back to static.
    """
    model = load_ml_model()
    if model is not None:
        return compute_ml_rank_score(features, model)
    return compute_static_rank_score(features)
