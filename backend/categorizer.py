from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import CategoryLearningRule
from backend.normalizer import build_key, canonical_entity_name, normalized_text_signature

KNOWN_MERCHANT_CATEGORY = {
    "naivas": "food",
    "quickmart": "food",
    "carrefour": "shopping",
    "kplc": "bills",
    "kenya power": "bills",
    "nairobi water": "bills",
    "shell": "transport",
    "total": "transport",
}
KNOWN_PAYBILL_CATEGORY = {"888880": "bills", "222222": "bills"}

KEYWORD_RULES: list[tuple[str, list[str], str, str, str, float]] = [
    ("reversal", ["reversal", "reversed"], "expense", "reversal", "uncategorized", 0.60),
    ("fuliza", ["fuliza", "overdraft"], "expense", "fuliza", "fees", 0.60),
    ("salary", ["salary", "payroll", "wages"], "income", "receive_money", "salary", 0.62),
    ("airtime", ["airtime", "bundle", "data bundle"], "expense", "airtime", "bills", 0.60),
    ("withdrawal", ["withdraw", "agent"], "expense", "withdrawal", "fees", 0.58),
    ("rent", ["rent", "landlord"], "expense", "send_money", "rent", 0.57),
    ("transport", ["matatu", "uber", "bolt", "fare", "fuel"], "expense", "send_money", "transport", 0.55),
    ("food", ["restaurant", "hotel", "grocer", "supermarket", "lunch", "dinner"], "expense", "buy_goods", "food", 0.54),
    ("utility", ["electricity", "water", "internet", "token"], "expense", "paybill", "bills", 0.58),
]

PARSED_SUBTYPE_FALLBACKS: dict[str, tuple[str, str, str, float]] = {
    "buy_goods": ("expense", "buy_goods", "shopping", 0.64),
    "paybill": ("expense", "paybill", "bills", 0.66),
    "airtime": ("expense", "airtime", "airtime", 0.67),
    "withdrawal": ("expense", "withdrawal", "transport", 0.58),
}

SCOPE_RANK = {
    "merchant_plus_account": 7,
    "paybill_plus_account": 7,
    "till_only": 6,
    "transaction_code": 6,
    "merchant_only": 5,
    "contact_only": 5,
    "paybill_only": 4,
    "normalized_text_exact": 3,
    "parsed_sub_type": 2,
    "broad": 1,
}


@dataclass(frozen=True)
class ClassificationInput:
    message: str
    normalized_message: str
    recipient: Optional[str]
    merchant_name: Optional[str]
    contact_name: Optional[str]
    paybill_number: Optional[str]
    till_number: Optional[str]
    account_reference: Optional[str]
    transaction_code: Optional[str]
    canonical_entity_name: Optional[str]
    normalized_text_signature: Optional[str]
    parsed_direction: Optional[str]
    parsed_sub_type: Optional[str]
    user_note: Optional[str]


@dataclass(frozen=True)
class ClassificationResult:
    transaction_type: str
    transaction_sub_type: str
    category: str
    confidence_score: float
    confidence_band: str
    confidence_breakdown: dict[str, float]
    confidence_reason_summary: str
    classification_source: str
    matched_rule: str
    matched_priority_tier: int
    matched_key_type: str
    suggestions: list[str]
    conflict_flag: bool
    conflict_reasons: list[str]
    competing_rules: list[str]
    needs_review: bool


@dataclass(frozen=True)
class CandidateRule:
    category: str
    tx_type: str
    sub_type: str
    source: str
    matched_rule: str
    priority_tier: int
    key_type: str
    scope: str
    base: float


def _confidence(candidate: CandidateRule, data: ClassificationInput, *, conflicts: int, history: int) -> tuple[float, str, dict[str, float], bool]:
    breakdown = {
        "base_rule_score": candidate.base,
        "specificity_bonus": min(0.18, SCOPE_RANK.get(candidate.scope, 1) * 0.02),
        "identifier_bonus": 0.08 if candidate.key_type in {"paybill_only", "paybill_plus_account", "till_only", "transaction_code"} else 0.03,
        "history_bonus": min(0.12, history * 0.02),
        "parser_bonus": 0.06 if data.parsed_sub_type and data.parsed_sub_type != "unknown" else 0.0,
        "ambiguity_penalty": 0.08 if data.merchant_name and data.contact_name else 0.0,
        "conflict_penalty": min(0.25, conflicts * 0.12),
        "missing_data_penalty": 0.06 if not (data.merchant_name or data.contact_name or data.paybill_number or data.till_number) else 0.0,
        "unknown_entity_penalty": 0.04 if not data.canonical_entity_name else 0.0,
    }
    score = (
        breakdown["base_rule_score"]
        + breakdown["specificity_bonus"]
        + breakdown["identifier_bonus"]
        + breakdown["history_bonus"]
        + breakdown["parser_bonus"]
        - breakdown["ambiguity_penalty"]
        - breakdown["conflict_penalty"]
        - breakdown["missing_data_penalty"]
        - breakdown["unknown_entity_penalty"]
    )
    score = max(0.0, min(1.0, round(score, 3)))
    band = "high" if score >= 0.8 else "medium" if score >= 0.55 else "low"
    needs_review = band == "low" and candidate.priority_tier >= 5
    return score, band, breakdown, needs_review


def _candidate_keys(data: ClassificationInput) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    for scope, key_type in [
        ("merchant_plus_account", "merchant_plus_account"),
        ("paybill_plus_account", "paybill_plus_account"),
        ("till_only", "till_only"),
        ("transaction_code", "transaction_code"),
        ("merchant_only", "merchant_only"),
        ("contact_only", "contact_only"),
        ("paybill_only", "paybill_only"),
        ("normalized_text_exact", "normalized_text_exact"),
    ]:
        key = build_key(
            scope,
            merchant=data.merchant_name,
            contact=data.contact_name,
            paybill=data.paybill_number,
            till=data.till_number,
            account=data.account_reference,
            text_signature=data.normalized_text_signature or normalized_text_signature(data.normalized_message),
            transaction_code=data.transaction_code,
        )
        if key:
            items.append((scope, key_type, key))
    return items


def _fetch_rules(db: Session, user_id: str, keys: list[str]) -> dict[str, list[CategoryLearningRule]]:
    if not keys:
        return {}
    rules = db.execute(
        select(CategoryLearningRule).where(
            CategoryLearningRule.user_id == user_id,
            CategoryLearningRule.match_key.in_(keys),
        )
    ).scalars().all()
    out: dict[str, list[CategoryLearningRule]] = {}
    for r in rules:
        out.setdefault(r.match_key, []).append(r)
    return out


def _select_learned_rule(rules: list[CategoryLearningRule], *, scope: str, key_type: str, tier: int) -> Optional[CandidateRule]:
    if not rules:
        return None
    exact = sorted(rules, key=lambda r: (r.usage_count or 0), reverse=True)[0]
    source = "manual" if getattr(exact, "is_manual", False) else "learned_rule"
    return CandidateRule(
        category=exact.category,
        tx_type="expense",
        sub_type="unknown",
        source=source,
        matched_rule=f"learned:{exact.match_key}",
        priority_tier=tier,
        key_type=key_type,
        scope=scope,
        base=0.72 if source == "manual" else 0.66,
    )


def _keyword_candidate(data: ClassificationInput) -> Optional[CandidateRule]:
    text = f"{data.normalized_message} {data.user_note or ''}".lower()
    for rule_name, keywords, tx_type, subtype, category, base in KEYWORD_RULES:
        if any(k in text for k in keywords):
            return CandidateRule(category, tx_type, subtype, "rule", f"keyword:{rule_name}", 5, "keyword", "broad", base)
    return None


def _curated_candidate(data: ClassificationInput) -> Optional[CandidateRule]:
    merchant = canonical_entity_name(data.merchant_name or data.recipient) or ""
    if data.paybill_number and data.paybill_number in KNOWN_PAYBILL_CATEGORY:
        return CandidateRule(KNOWN_PAYBILL_CATEGORY[data.paybill_number], "expense", "paybill", "rule", f"known_paybill:{data.paybill_number}", 4, "paybill_only", "paybill_only", 0.68)
    for key, category in KNOWN_MERCHANT_CATEGORY.items():
        if key in merchant:
            return CandidateRule(category, data.parsed_direction or "expense", data.parsed_sub_type or "buy_goods", "rule", f"known_merchant:{key}", 4, "merchant_only", "merchant_only", 0.66)
    return None


def _parsed_sub_type_candidate(data: ClassificationInput) -> Optional[CandidateRule]:
    if not data.parsed_sub_type:
        return None
    fallback = PARSED_SUBTYPE_FALLBACKS.get(data.parsed_sub_type)
    if not fallback:
        return None
    tx_type, sub_type, category, base = fallback
    return CandidateRule(
        category=category,
        tx_type=tx_type,
        sub_type=sub_type,
        source="rule",
        matched_rule=f"parsed_sub_type:{data.parsed_sub_type}",
        priority_tier=4,
        key_type="parsed_sub_type",
        scope="parsed_sub_type",
        base=base,
    )


def _detect_conflicts(candidates: list[CandidateRule], data: ClassificationInput) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    competing: list[str] = []
    categories = {c.category for c in candidates}
    if len(categories) > 1:
        reasons.append("multiple_rules_disagree")
        competing.extend([f"{c.matched_rule}:{c.category}" for c in candidates[:4]])
    text = data.normalized_message.lower()
    if "sent to" in text and (data.paybill_number or "for account" in text):
        reasons.append("transfer_vs_bill_signal")
    if data.merchant_name and data.contact_name:
        reasons.append("merchant_person_ambiguity")
    return reasons, competing


def classify_transaction(db: Session, *, user_id: str, data: ClassificationInput) -> ClassificationResult:
    key_triplets = _candidate_keys(data)
    by_key = _fetch_rules(db, user_id, [k for _, _, k in key_triplets])
    candidates: list[CandidateRule] = []

    # Tier 1: exact manual correction
    for scope, key_type, key in key_triplets:
        rules = [r for r in by_key.get(key, []) if getattr(r, "is_manual", False)]
        c = _select_learned_rule(rules, scope=scope, key_type=key_type, tier=1)
        if c:
            candidates.append(c)

    # Tier 2: exact structured identifier
    for scope, key_type, key in key_triplets:
        if key_type in {"paybill_only", "paybill_plus_account", "till_only", "transaction_code", "merchant_only", "contact_only", "merchant_plus_account"}:
            rules = [r for r in by_key.get(key, []) if not getattr(r, "is_manual", False)]
            c = _select_learned_rule(rules, scope=scope, key_type=key_type, tier=2)
            if c:
                candidates.append(c)

    # Tier 3: high-confidence learned
    for scope, key_type, key in key_triplets:
        rules = [r for r in by_key.get(key, []) if (r.usage_count or 0) >= 2]
        c = _select_learned_rule(rules, scope=scope, key_type=key_type, tier=3)
        if c:
            candidates.append(c)

    curated = _curated_candidate(data)
    if curated:
        candidates.append(curated)
    parsed_sub_type_candidate = _parsed_sub_type_candidate(data)
    if parsed_sub_type_candidate:
        candidates.append(parsed_sub_type_candidate)
    keyword = _keyword_candidate(data)
    if keyword:
        candidates.append(keyword)

    suggestions = []
    if not candidates:
        sig = data.normalized_text_signature or normalized_text_signature(data.normalized_message)
        for key in [f"text:{sig}"]:
            for r in by_key.get(key, []):
                if r.category and r.category not in suggestions:
                    suggestions.append(r.category)
        for c in ["bills", "transport", "food"]:
            if c not in suggestions:
                suggestions.append(c)

    if not candidates:
        return ClassificationResult(
            transaction_type=data.parsed_direction or "expense",
            transaction_sub_type=data.parsed_sub_type or "unknown",
            category="uncategorized",
            confidence_score=0.2,
            confidence_band="low",
            confidence_breakdown={"base_rule_score": 0.2},
            confidence_reason_summary="No reliable rule match; using fallback suggestions.",
            classification_source="fallback",
            matched_rule="fallback:uncategorized",
            matched_priority_tier=7,
            matched_key_type="none",
            suggestions=suggestions[:3],
            conflict_flag=False,
            conflict_reasons=[],
            competing_rules=[],
            needs_review=False,
        )

    candidates = sorted(candidates, key=lambda c: (c.priority_tier * -1, SCOPE_RANK.get(c.scope, 1), c.base), reverse=False)
    # explicit best selection by tier asc then specificity desc then base desc
    candidates = sorted(candidates, key=lambda c: (c.priority_tier, -SCOPE_RANK.get(c.scope, 1), -c.base))
    winner = candidates[0]
    conflict_reasons, competing = _detect_conflicts(candidates, data)
    history = 0
    for _, _, key in key_triplets:
        history += sum((r.usage_count or 0) for r in by_key.get(key, []))

    score, band, breakdown, needs_review = _confidence(
        winner,
        data,
        conflicts=len(conflict_reasons),
        history=history,
    )
    if conflict_reasons and len(candidates) > 1:
        second = candidates[1]
        if second.category != winner.category and abs(second.base - winner.base) <= 0.08 and second.priority_tier == winner.priority_tier:
            needs_review = True
            score = max(0.3, score - 0.15)
            band = "low" if score < 0.55 else band
        elif second.category != winner.category and "multiple_rules_disagree" in conflict_reasons and score < 0.78:
            needs_review = True
            score = max(0.3, score - 0.1)
            band = "low" if score < 0.55 else band
    if "multiple_rules_disagree" in conflict_reasons and winner.priority_tier > 1 and band != "high":
        needs_review = True

    final_category = winner.category
    if band == "low" and winner.priority_tier >= 5:
        final_category = "uncategorized"

    return ClassificationResult(
        transaction_type=winner.tx_type,
        transaction_sub_type=winner.sub_type,
        category=final_category,
        confidence_score=score,
        confidence_band=band,
        confidence_breakdown=breakdown,
        confidence_reason_summary=f"Tier {winner.priority_tier} {winner.key_type} match via {winner.matched_rule}.",
        classification_source=winner.source,
        matched_rule=winner.matched_rule,
        matched_priority_tier=winner.priority_tier,
        matched_key_type=winner.key_type,
        suggestions=suggestions[:3],
        conflict_flag=bool(conflict_reasons),
        conflict_reasons=conflict_reasons,
        competing_rules=competing,
        needs_review=needs_review,
    )


def normalize_category(value: str) -> str:
    normalized = normalized_text_signature(value).replace(" ", "_")
    return normalized or "uncategorized"


def remember_manual_category(
    db: Session,
    *,
    user_id: str,
    category: str,
    merchant_name: Optional[str],
    contact_name: Optional[str],
    recipient: Optional[str],
    paybill_number: Optional[str],
    till_number: Optional[str],
    account_reference: Optional[str],
    normalized_message: Optional[str],
    transaction_code: Optional[str] = None,
    correction_scope: str = "merchant_plus_account",
    correction_match_basis: str = "manual_correction",
    canonical_entity_name_value: Optional[str] = None,
    normalized_text_signature_value: Optional[str] = None,
    broad_apply: bool = False,
    learned_from_tx_id: Optional[int] = None,
) -> list[str]:
    category = normalize_category(category)
    sig = normalized_text_signature_value or normalized_text_signature(normalized_message or "")
    canonical = canonical_entity_name_value or canonical_entity_name(merchant_name or contact_name or recipient)

    scopes = [correction_scope]
    if correction_scope == "broad":
        scopes = ["merchant_only"]
        broad_apply = True
    if broad_apply and correction_scope != "merchant_only":
        scopes.append("merchant_only")

    keys: list[str] = []
    now = datetime.now(timezone.utc)
    for scope in scopes:
        key = build_key(
            scope,
            merchant=merchant_name or recipient,
            contact=contact_name or recipient,
            paybill=paybill_number,
            till=till_number,
            account=account_reference,
            text_signature=sig,
            transaction_code=transaction_code,
        )
        if not key:
            continue
        keys.append(key)
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
            existing.correction_scope = scope
            existing.correction_match_basis = correction_match_basis
            existing.canonical_entity_name = canonical
            existing.normalized_text_signature = sig
            existing.is_manual = True
        else:
            db.add(
                CategoryLearningRule(
                    user_id=user_id,
                    match_key=key,
                    category=category,
                    learned_from_tx_id=learned_from_tx_id,
                    usage_count=1,
                    updated_at=now,
                    correction_scope=scope,
                    correction_match_basis=correction_match_basis,
                    canonical_entity_name=canonical,
                    normalized_text_signature=sig,
                    is_manual=True,
                )
            )
    return keys


def categorize_hybrid(db: Session, *, user_id: str, message: str, user_note: Optional[str], recipient: Optional[str], transaction_type: Optional[str]) -> str:
    result = classify_transaction(
        db,
        user_id=user_id,
        data=ClassificationInput(
            message=message,
            normalized_message=message.lower(),
            recipient=recipient,
            merchant_name=recipient,
            contact_name=recipient,
            paybill_number=None,
            till_number=None,
            account_reference=None,
            transaction_code=None,
            canonical_entity_name=canonical_entity_name(recipient),
            normalized_text_signature=normalized_text_signature(message),
            parsed_direction="income" if transaction_type == "receive_money" else "expense",
            parsed_sub_type=transaction_type,
            user_note=user_note,
        ),
    )
    return result.category


def serialize_breakdown(value: dict[str, float]) -> str:
    return json.dumps(value, sort_keys=True)
