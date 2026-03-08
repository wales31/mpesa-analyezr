from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Optional

from dateutil import parser as date_parser

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


_RE_AMOUNT = re.compile(r"(?i)\b(?:ksh|kes)\s*([\d,]+(?:\.\d{1,2})?)\b")
_RE_REF = re.compile(r"(?i)\b([A-Z0-9]{8,12})\b\s+confirmed\b")
_RE_DATE_TIME = re.compile(
    r"(?i)\bon\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(\d{1,2}:\d{2}\s*(?:am|pm)?)"
)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


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
    if not m:
        return None
    ref = m.group(1).upper()
    if ref.isdigit():
        return None
    return ref


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


def parse_mpesa_message(message: str) -> ParsedTransaction:
    """
    Parse an M-PESA-like SMS into a normalized transaction.

    Assumptions (v1):
    - Contains an amount formatted like: "Ksh500.00" or "KES 500.00"
    - Contains a timestamp formatted like: "on 2/2/26 at 9:14 AM"
    """

    if not message or not message.strip():
        raise ParseError("Message is empty.")

    text = _clean_text(message)

    amount = _parse_amount(text)
    occurred_at = _parse_occurred_at(text)
    reference = _parse_reference(text)

    lower = text.lower()

    # Determine type/direction and best-effort recipient.
    if "received from" in lower:
        direction = "income"
        tx_type = "received"
        recipient = _extract_recipient(
            text,
            re.compile(r"(?i)\breceived from\s+(.+?)\s+on\b"),
        )
    elif "sent to" in lower:
        direction = "expense"
        tx_type = "sent"
        recipient = _extract_recipient(
            text,
            re.compile(r"(?i)\bsent to\s+(.+?)(?:\s+\d{7,15})?\s+on\b"),
        )
    elif "paid to" in lower:
        direction = "expense"
        tx_type = "pay"
        recipient = _extract_recipient(
            text,
            re.compile(r"(?i)\bpaid to\s+(.+?)\s+on\b"),
        )
    elif "withdrawn" in lower:
        direction = "transfer"
        tx_type = "withdraw"
        recipient = _extract_recipient(
            text,
            re.compile(r"(?i)\bwithdrawn(?: from| at)?\s+(.+?)\s+on\b"),
        )
    elif "deposited" in lower or "deposit" in lower:
        direction = "transfer"
        tx_type = "deposit"
        recipient = _extract_recipient(
            text,
            re.compile(r"(?i)\bdeposited(?: to| at)?\s+(.+?)\s+on\b"),
        )
    else:
        direction = "expense"
        tx_type = None
        recipient = None

    return ParsedTransaction(
        amount=amount,
        currency="KES",
        direction=direction,
        transaction_type=tx_type,
        recipient=recipient,
        reference=reference,
        occurred_at=occurred_at,
    )
