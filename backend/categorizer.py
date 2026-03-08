from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import CategoryLearningRule


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": ["food", "lunch", "dinner", "breakfast", "restaurant", "cafe", "groceries", "supermarket"],
    "transport": ["transport", "uber", "bolt", "taxi", "matatu", "bus", "fare", "fuel", "petrol", "diesel"],
    "rent": ["rent", "landlord", "house rent", "apartment"],
    "bills": ["bill", "electricity", "kplc", "water", "internet", "wifi", "tokens"],
    "airtime": ["airtime", "bundles", "data"],
    "betting": ["bet", "betting", "sportpesa", "betika", "odibet"],
    "shopping": ["shopping", "mall", "store", "shop"],
}


def _haystack(*parts: Optional[str]) -> str:
    return " ".join(p for p in parts if p).lower()


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    out = re.sub(r"[^a-z0-9]+", " ", value.lower())
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _candidate_match_keys(
    *,
    recipient: Optional[str],
    transaction_type: Optional[str],
    user_note: Optional[str],
) -> list[str]:
    keys: list[str] = []

    recipient_norm = _normalize_text(recipient)
    tx_type_norm = _normalize_text(transaction_type)
    note_norm = _normalize_text(user_note)

    if recipient_norm and tx_type_norm:
        keys.append(f"recipient_type:{recipient_norm}|{tx_type_norm}")
    if recipient_norm:
        keys.append(f"recipient:{recipient_norm}")

    if note_norm:
        # Learn on stable, meaningful tokens from user notes.
        for token in note_norm.split(" "):
            if len(token) >= 4:
                keys.append(f"note:{token}")

    if tx_type_norm:
        keys.append(f"type:{tx_type_norm}")

    # Preserve order and remove duplicates.
    seen: set[str] = set()
    out: list[str] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _keyword_fallback(
    message: str,
    user_note: Optional[str],
    recipient: Optional[str],
    transaction_type: Optional[str],
) -> str:
    text = _haystack(user_note, recipient, transaction_type, message)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "uncategorized"

    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category

    return "uncategorized"


def categorize_hybrid(
    db: Session,
    *,
    user_id: str,
    message: str,
    user_note: Optional[str],
    recipient: Optional[str],
    transaction_type: Optional[str],
) -> str:
    """
    Hybrid categorization strategy:
    1) User-learned mappings from past manual categorizations.
    2) Keyword/pattern fallback.
    """
    keys = _candidate_match_keys(
        recipient=recipient,
        transaction_type=transaction_type,
        user_note=user_note,
    )
    if keys:
        rules = db.execute(
            select(CategoryLearningRule).where(
                CategoryLearningRule.user_id == user_id,
                CategoryLearningRule.match_key.in_(keys),
            )
        ).scalars().all()
        by_key = {rule.match_key: rule for rule in rules}
        for key in keys:
            rule = by_key.get(key)
            if rule and rule.category:
                return rule.category

    return _keyword_fallback(
        message=message,
        user_note=user_note,
        recipient=recipient,
        transaction_type=transaction_type,
    )


def remember_manual_category(
    db: Session,
    *,
    user_id: str,
    category: str,
    message: Optional[str],
    user_note: Optional[str],
    recipient: Optional[str],
    transaction_type: Optional[str],
    learned_from_tx_id: Optional[int] = None,
) -> int:
    """
    Persist learned categorization keys from a user manual category choice.
    Returns number of keys learned/updated.
    """
    category = normalize_category(category)
    keys = _candidate_match_keys(
        recipient=recipient,
        transaction_type=transaction_type,
        user_note=user_note,
    )
    if not keys:
        return 0

    touched = 0
    now = datetime.utcnow()
    # Keep rules focused and avoid overfitting from too many note tokens.
    for key in keys[:5]:
        existing = db.execute(
            select(CategoryLearningRule).where(
                CategoryLearningRule.user_id == user_id,
                CategoryLearningRule.match_key == key,
            )
        ).scalar_one_or_none()

        if existing:
            existing.category = category
            existing.updated_at = now
            existing.learned_from_tx_id = learned_from_tx_id
            existing.usage_count = int(existing.usage_count or 0) + 1
        else:
            db.add(
                CategoryLearningRule(
                    user_id=user_id,
                    match_key=key,
                    category=category,
                    learned_from_tx_id=learned_from_tx_id,
                    usage_count=1,
                    updated_at=now,
                )
            )
        touched += 1

    return touched


def normalize_category(value: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return "uncategorized"
    return normalized.replace(" ", "_")


def categorize(message: str, user_note: Optional[str], recipient: Optional[str], transaction_type: Optional[str]) -> str:
    """
    Compatibility wrapper for callers that only want keyword-based categorization.

    New code should call `categorize_hybrid(...)`.
    """
    return _keyword_fallback(
        message=message,
        user_note=user_note,
        recipient=recipient,
        transaction_type=transaction_type,
    )
