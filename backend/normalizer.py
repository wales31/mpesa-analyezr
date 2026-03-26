from __future__ import annotations

import re
from typing import Optional

BUSINESS_SUFFIXES = {
    "ltd",
    "limited",
    "enterprises",
    "enterprise",
    "investments",
    "shop",
    "stores",
    "agency",
    "services",
    "traders",
    "wholesalers",
    "supermarket",
}

ACCOUNT_PATTERNS = [
    r"\bfor\s+account\s+([a-z0-9\-\./ ]+?)(?:\s+on\b|,|$)",
    r"\b(?:acct|account)\s*[:#-]?\s*([a-z0-9\-\./ ]+?)(?:\s+on\b|,|$)",
    r"\b(?:meter|invoice|admission|room)\s*[:#-]?\s*([a-z0-9\-\./]+)",
]


def clean_display_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    out = re.sub(r"\s+", " ", value).strip().strip(".,;:-")
    return out.title() if out else None


def canonical_entity_name(value: Optional[str]) -> Optional[str]:
    display = clean_display_name(value)
    if not display:
        return None
    s = re.sub(r"[^a-z0-9\s]", " ", display.lower())
    tokens = [t for t in re.sub(r"\s+", " ", s).strip().split(" ") if t and t not in BUSINESS_SUFFIXES]
    if not tokens:
        return None
    return " ".join(tokens)


def normalized_text_signature(text: str, *, max_tokens: int = 10) -> str:
    s = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    tokens = [t for t in re.sub(r"\s+", " ", s).strip().split(" ") if len(t) >= 4]
    return " ".join(tokens[:max_tokens])


def extract_account_reference(text: str) -> Optional[str]:
    lower = (text or "").lower()
    for pattern in ACCOUNT_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            value = re.sub(r"\s+", " ", m.group(1)).strip(" .,:;")
            return value
    return None


def extract_phone_number(text: str) -> Optional[str]:
    m = re.search(r"\b(?:\+?254|0)?7\d{8}\b", text or "")
    return m.group(0) if m else None


def infer_entity_type(entity: Optional[str], text: str = "") -> str:
    canonical = canonical_entity_name(entity) or ""
    full = f"{canonical} {(text or '').lower()}"
    if any(k in full for k in ["kplc", "water", "token", "electricity", "utility"]):
        return "utility"
    if any(k in full for k in ["school", "tuition", "admission"]):
        return "school"
    if any(k in full for k in ["landlord", "rent"]):
        return "landlord"
    if any(k in full for k in ["agent", "mpesa agent"]):
        return "agent"
    # person-ish: 2-3 alpha tokens without merchant words
    if canonical and re.fullmatch(r"[a-z]+(?:\s[a-z]+){1,2}", canonical):
        return "person"
    if canonical:
        return "merchant"
    return "unknown"


def build_key(scope: str, *, merchant: Optional[str] = None, contact: Optional[str] = None, paybill: Optional[str] = None, till: Optional[str] = None, account: Optional[str] = None, text_signature: Optional[str] = None, transaction_code: Optional[str] = None) -> Optional[str]:
    merchant = canonical_entity_name(merchant)
    contact = canonical_entity_name(contact)
    account = (account or "").strip().lower() or None
    if scope == "merchant_plus_account" and merchant and account:
        return f"merchant_account:{merchant}|{account}"
    if scope == "paybill_plus_account" and paybill and account:
        return f"paybill_account:{paybill}|{account}"
    if scope == "till_only" and till:
        return f"till:{till}"
    if scope == "merchant_only" and merchant:
        return f"merchant:{merchant}"
    if scope == "contact_only" and contact:
        return f"contact:{contact}"
    if scope == "paybill_only" and paybill:
        return f"paybill:{paybill}"
    if scope == "transaction_code" and transaction_code:
        return f"txcode:{transaction_code.lower()}"
    if scope == "normalized_text_exact" and text_signature:
        return f"text:{text_signature}"
    return None
