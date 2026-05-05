"""
Feature engineering module for email ranking and CTR prediction.

Extracts features from emails that can be used for:
1. Ranking emails by importance
2. Predicting open/click probability (CTR)
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from database import get_conn


# Keywords that signal importance
INTERVIEW_KEYWORDS = ['interview', 'schedule', 'meeting', 'call', 'phone screen', 'onsite', 'virtual']
OFFER_KEYWORDS = ['offer', 'congratulations', 'pleased to offer', 'welcome aboard', 'accepted']
REJECTION_KEYWORDS = ['unfortunately', 'regret', 'not moving forward', 'other candidates', 'not selected']
URGENT_KEYWORDS = ['urgent', 'asap', 'immediately', 'deadline', 'expires', 'last chance', 'final']
ACTION_KEYWORDS = ['action required', 'please respond', 'reply needed', 'confirm', 'complete', 'submit']

# Common personal email domains (non-company)
PERSONAL_DOMAINS = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com', 'protonmail.com'}


def extract_sender_domain(sender: str) -> str:
    """Extract domain from sender email address."""
    match = re.search(r'@([\w.-]+)', sender)
    return match.group(1).lower() if match else ''


def extract_sender_email(sender: str) -> str:
    """Extract email address from sender field (handles 'Name <email>' format)."""
    match = re.search(r'<([^>]+)>', sender)
    if match:
        return match.group(1).lower()
    # If no angle brackets, assume the whole thing is an email
    if '@' in sender:
        return sender.lower().strip()
    return ''


def count_keyword_matches(text: str, keywords: list) -> int:
    """Count how many keywords appear in text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def has_any_keyword(text: str, keywords: list) -> bool:
    """Check if any keyword appears in text."""
    return count_keyword_matches(text, keywords) > 0


def get_sender_frequency(sender_email: str) -> int:
    """Get how many emails we've seen from this sender."""
    if not sender_email:
        return 0

    conn = get_conn()
    c = conn.cursor()
    # Match by domain or full email in sender_name field
    domain = extract_sender_domain(sender_email)
    c.execute(
        "SELECT COUNT(*) FROM seen_emails WHERE sender_name LIKE ?",
        (f'%{domain}%',)
    )
    count = c.fetchone()[0]
    conn.close()
    return count


def parse_email_timestamp(internal_date_ms: Optional[str]) -> Optional[datetime]:
    """Parse Gmail internalDate (milliseconds since epoch) to datetime."""
    if not internal_date_ms:
        return None
    try:
        timestamp_s = int(internal_date_ms) / 1000
        return datetime.fromtimestamp(timestamp_s, tz=timezone.utc)
    except (ValueError, TypeError):
        return None


def compute_recency_hours(email_time: Optional[datetime]) -> float:
    """Compute hours since email was received."""
    if not email_time:
        return 168.0  # Default to 1 week if unknown

    now = datetime.now(timezone.utc)
    delta = now - email_time
    return delta.total_seconds() / 3600


def extract_features(
    subject: str,
    body: str,
    sender: str,
    category: str,
    internal_date_ms: Optional[str] = None,
    has_attachment: bool = False
) -> Dict[str, Any]:
    """
    Extract all features from an email.

    Args:
        subject: Email subject line
        body: Email body text
        sender: Sender field (e.g., "John Doe <john@company.com>")
        category: Classification category from GPT
        internal_date_ms: Gmail internalDate in milliseconds
        has_attachment: Whether email has attachments

    Returns:
        Dictionary of features
    """
    sender_email = extract_sender_email(sender)
    sender_domain = extract_sender_domain(sender)
    email_time = parse_email_timestamp(internal_date_ms)
    combined_text = f"{subject} {body}"

    features = {
        # Text length features
        'subject_length': len(subject),
        'body_length': len(body),
        'word_count': len(body.split()),

        # Subject pattern features
        'is_reply': subject.lower().startswith('re:'),
        'is_forward': subject.lower().startswith('fwd:'),
        'has_question': '?' in subject,
        'exclamation_count': subject.count('!'),

        # Sender features
        'sender_domain': sender_domain,
        'is_company_email': sender_domain not in PERSONAL_DOMAINS and sender_domain != '',
        'sender_frequency': get_sender_frequency(sender_email),

        # Time features
        'recency_hours': compute_recency_hours(email_time),
        'hour_of_day': email_time.hour if email_time else 12,
        'day_of_week': email_time.weekday() if email_time else 0,  # 0=Monday
        'is_weekend': email_time.weekday() >= 5 if email_time else False,

        # Keyword features
        'has_interview_keyword': has_any_keyword(combined_text, INTERVIEW_KEYWORDS),
        'has_offer_keyword': has_any_keyword(combined_text, OFFER_KEYWORDS),
        'has_rejection_keyword': has_any_keyword(combined_text, REJECTION_KEYWORDS),
        'has_urgent_keyword': has_any_keyword(combined_text, URGENT_KEYWORDS),
        'has_action_keyword': has_any_keyword(combined_text, ACTION_KEYWORDS),
        'interview_keyword_count': count_keyword_matches(combined_text, INTERVIEW_KEYWORDS),
        'offer_keyword_count': count_keyword_matches(combined_text, OFFER_KEYWORDS),

        # Category features (from GPT classification)
        'category': category,
        'is_interview': 'interview' in category.lower(),
        'is_offer': 'offer' in category.lower(),
        'is_rejection': 'rejection' in category.lower(),
        'is_spam': 'spam' in category.lower() or 'promo' in category.lower(),

        # Other
        'has_attachment': has_attachment,
    }

    return features


def features_to_vector(features: Dict[str, Any]) -> list:
    """
    Convert features dict to numerical vector for ML models.

    Returns list of floats that can be used as model input.
    """
    # Define feature order (must be consistent for training and inference)
    numeric_features = [
        features['subject_length'],
        features['body_length'],
        features['word_count'],
        float(features['is_reply']),
        float(features['is_forward']),
        float(features['has_question']),
        features['exclamation_count'],
        float(features['is_company_email']),
        features['sender_frequency'],
        features['recency_hours'],
        features['hour_of_day'],
        features['day_of_week'],
        float(features['is_weekend']),
        float(features['has_interview_keyword']),
        float(features['has_offer_keyword']),
        float(features['has_rejection_keyword']),
        float(features['has_urgent_keyword']),
        float(features['has_action_keyword']),
        features['interview_keyword_count'],
        features['offer_keyword_count'],
        float(features['is_interview']),
        float(features['is_offer']),
        float(features['is_rejection']),
        float(features['is_spam']),
        float(features['has_attachment']),
    ]

    return numeric_features


# Feature names for model interpretation
FEATURE_NAMES = [
    'subject_length',
    'body_length',
    'word_count',
    'is_reply',
    'is_forward',
    'has_question',
    'exclamation_count',
    'is_company_email',
    'sender_frequency',
    'recency_hours',
    'hour_of_day',
    'day_of_week',
    'is_weekend',
    'has_interview_keyword',
    'has_offer_keyword',
    'has_rejection_keyword',
    'has_urgent_keyword',
    'has_action_keyword',
    'interview_keyword_count',
    'offer_keyword_count',
    'is_interview',
    'is_offer',
    'is_rejection',
    'is_spam',
    'has_attachment',
]
