from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Optional

from dateutil import parser as date_parser
from backend.normalizer import (
    canonical_entity_name,
    clean_display_name,
    extract_account_reference as normalize_extract_account_reference,
    extract_phone_number,
    infer_entity_type,
    normalized_text_signature,
)

try:
    from zoneinfo import ZoneInfo

    _NAIROBI_TZ = ZoneInfo("Africa/Nairobi")
except Exception:  # pragma: no cover
    _NAIROBI_TZ = None


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedTransaction:
    amount: Decimal
    currency: str
    direction: str
    transaction_type: Optional[str]
    recipient: Optional[str]
    reference: Optional[str]
    occurred_at: datetime
    raw_message: str
    normalized_message: str
    transaction_code: Optional[str]
    merchant_name: Optional[str]
    contact_name: Optional[str]
    paybill_number: Optional[str]
    till_number: Optional[str]
    account_reference: Optional[str]
    canonical_entity_name: Optional[str]
    display_entity_name: Optional[str]
    normalized_text_signature: str
    entity_type: str
    phone_number: Optional[str]


_RE_AMOUNT = re.compile(r"(?i)\b(?:ksh|kes)\s*([\d,]+(?:\.\d{1,2})?)\b")
_RE_REF = re.compile(r"(?i)\b([A-Z0-9]{8,12})\b\s+confirmed\b")
_RE_TX_CODE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{8,11})\b")
_RE_DATE_TIME = re.compile(
    r"(?i)\bon\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(\d{1,2}:\d{2}\s*(?:am|pm)?)"
)
_RE_PAYBILL = re.compile(r"(?i)(?:paybill\s*(?:number)?|business\s*number)\s*:?\s*(\d{4,8})")
_RE_TILL = re.compile(r"(?i)(?:till\s*(?:number)?|buy\s*goods\s*(?:at)?|merchant\s*code)\s*:?\s*(\d{4,8})")
_RE_ACCOUNT = re.compile(r"(?i)\bfor\s+account\s+(.+?)(?:\s+on\s+\d{1,2}/\d{1,2}/\d{2,4}\s+at\b|[\.]|$)")


def normalize_message_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    return text


def normalize_party_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    out = re.sub(r"\s+", " ", value).strip(" .")
    out = re.sub(r"\b(limited|ltd|limited\.)\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" .")
    return out.title() if out else None


def _parse_amount(message: str) -> Decimal:
    m = _RE_AMOUNT.search(message)
    if not m:
        raise ParseError("Could not find amount (expected 'Ksh...' or 'KES...').")
    raw = m.group(1).replace(",", "")
    try:
        return Decimal(raw)
    except InvalidOperation as e:  # pragma: no cover
        raise ParseError("Invalid amount format.") from e


def _parse_reference(message: str) -> Optional[str]:
    m = _RE_REF.search(message)
    if m:
        ref = m.group(1).upper()
        if not ref.isdigit():
            return ref

    code = _RE_TX_CODE.search(message)
    return code.group(1).upper() if code else None


def _parse_occurred_at(message: str) -> datetime:
    m = _RE_DATE_TIME.search(message)
    if not m:
        raise ParseError("Could not find date/time (expected 'on d/m/yy at h:mm AM/PM').")
    date_str, time_str = m.group(1), m.group(2)
    try:
        dt = date_parser.parse(f"{date_str} {time_str}", dayfirst=True, fuzzy=True)
    except (ValueError, OverflowError) as e:
        raise ParseError("Could not parse date/time.") from e
    if dt.tzinfo is None and _NAIROBI_TZ is not None:
        dt = dt.replace(tzinfo=_NAIROBI_TZ)
    return dt


def _extract_recipient(message: str, pattern: re.Pattern[str]) -> Optional[str]:
    m = pattern.search(message)
    if not m:
        return None
    rec = m.group(1).strip()
    rec = re.sub(r"\s+", " ", rec)
    return rec or None


def extract_paybill_number(message: str) -> Optional[str]:
    m = _RE_PAYBILL.search(message)
    return m.group(1) if m else None


def extract_till_number(message: str) -> Optional[str]:
    m = _RE_TILL.search(message)
    return m.group(1) if m else None


def extract_account_reference(message: str) -> Optional[str]:
    m = _RE_ACCOUNT.search(message)
    if not m:
        return normalize_extract_account_reference(message)
    return normalize_message_text(m.group(1)).strip(" .") or normalize_extract_account_reference(message)


def parse_mpesa_message(message: str) -> ParsedTransaction:
    if not message or not message.strip():
        raise ParseError("Message is empty.")

    raw = message.strip()
    text = normalize_message_text(raw)
    lower = text.lower()

    amount = _parse_amount(text)
    occurred_at = _parse_occurred_at(text)
    reference = _parse_reference(text)

    if "received from" in lower:
        direction = "income"
        tx_type = "receive_money"
        contact = _extract_recipient(text, re.compile(r"(?i)\breceived from\s+(.+?)\s+on\b"))
        merchant = None
    elif "sent to" in lower:
        direction = "expense"
        tx_type = "send_money"
        contact = _extract_recipient(text, re.compile(r"(?i)\bsent to\s+(.+?)(?:\s+\d{7,15})?\s+on\b"))
        merchant = None
    elif "paid to" in lower or "buy goods" in lower:
        direction = "expense"
        tx_type = "buy_goods"
        merchant = _extract_recipient(text, re.compile(r"(?i)\b(?:paid to|paid to business|buy goods(?: at)?)\s+(.+?)\s+on\b"))
        contact = None
    elif "paybill" in lower:
        direction = "expense"
        tx_type = "paybill"
        merchant = _extract_recipient(text, re.compile(r"(?i)\bpaybill\s+(.+?)\s+on\b"))
        contact = None
    elif "withdraw" in lower:
        direction = "expense"
        tx_type = "withdrawal"
        merchant = _extract_recipient(text, re.compile(r"(?i)\bwithdrawn?(?: from| at)?\s+(.+?)\s+on\b"))
        contact = None
    elif "deposited" in lower or "deposit" in lower:
        direction = "income"
        tx_type = "deposit"
        merchant = _extract_recipient(text, re.compile(r"(?i)\bdeposited(?: to| at)?\s+(.+?)\s+on\b"))
        contact = None
    elif "airtime" in lower:
        direction = "expense"
        tx_type = "airtime"
        merchant = "Safaricom Airtime"
        contact = None
    else:
        direction = "expense"
        tx_type = "unknown"
        merchant = None
        contact = None

    paybill_number = extract_paybill_number(text)
    till_number = extract_till_number(text)
    account_reference = extract_account_reference(text)

    recipient = contact or merchant
    display_entity = clean_display_name(recipient)
    canonical_entity = canonical_entity_name(recipient)
    text_signature = normalized_text_signature(text)
    phone = extract_phone_number(text)
    entity_type = infer_entity_type(recipient, text)
    return ParsedTransaction(
        amount=amount,
        currency="KES",
        direction=direction,
        transaction_type=tx_type,
        recipient=normalize_party_name(recipient),
        reference=reference,
        occurred_at=occurred_at,
        raw_message=raw,
        normalized_message=text.lower(),
        transaction_code=reference,
        merchant_name=normalize_party_name(merchant),
        contact_name=normalize_party_name(contact),
        paybill_number=paybill_number,
        till_number=till_number,
        account_reference=account_reference,
        canonical_entity_name=canonical_entity,
        display_entity_name=display_entity,
        normalized_text_signature=text_signature,
        entity_type=entity_type,
        phone_number=phone,
    )
