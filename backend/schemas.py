from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class AuthUserOut(BaseModel):
    id: str
    email: str
    username: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUserOut


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_note: Optional[str] = Field(default=None, max_length=500)


class AnalyzeBulkRequest(BaseModel):
    messages: list[str] = Field(..., min_length=1)
    user_note: Optional[str] = Field(default=None, max_length=500)


class IngestionMessageIn(BaseModel):
    message: str = Field(..., min_length=1)
    source_message_id: Optional[str] = Field(default=None, max_length=128)
    source_received_at: Optional[datetime] = None
    user_note: Optional[str] = Field(default=None, max_length=500)
    source: Optional[str] = Field(default=None, max_length=32)


class IngestMessagesRequest(BaseModel):
    mode: Literal["single_upload", "inbox_sync", "statement_import"] = "single_upload"
    batch_id: Optional[str] = Field(default=None, max_length=64)
    user_note: Optional[str] = Field(default=None, max_length=500)
    source: Optional[str] = Field(default=None, max_length=32)
    messages: list[IngestionMessageIn] = Field(..., min_length=1, max_length=500)


class TransactionOut(BaseModel):
    id: int
    amount: float
    currency: str
    category: str
    direction: str
    transaction_type: Optional[str] = None
    transaction_sub_type: Optional[str] = None
    recipient: Optional[str] = None
    merchant_name: Optional[str] = None
    contact_name: Optional[str] = None
    paybill_number: Optional[str] = None
    till_number: Optional[str] = None
    account_reference: Optional[str] = None
    raw_message: Optional[str] = None
    normalized_message: Optional[str] = None
    confidence_score: Optional[float] = None
    classification_source: Optional[str] = None
    matched_rule: Optional[str] = None
    matched_priority_tier: Optional[int] = None
    matched_key_type: Optional[str] = None
    correction_scope: Optional[str] = None
    correction_match_basis: Optional[str] = None
    canonical_entity_name: Optional[str] = None
    normalized_text_signature: Optional[str] = None
    confidence_band: Optional[str] = None
    confidence_breakdown: Optional[dict[str, float]] = None
    confidence_reason_summary: Optional[str] = None
    conflict_flag: Optional[bool] = None
    conflict_reasons: list[str] = Field(default_factory=list)
    competing_rules: list[str] = Field(default_factory=list)
    needs_review: Optional[bool] = None
    category_suggestions: list[str] = Field(default_factory=list)
    user_corrected_category: Optional[str] = None
    user_correction_key: Optional[str] = None
    reference: Optional[str] = None
    occurred_at: Optional[datetime] = None
    date: Optional[str] = None
    time: Optional[str] = None
    user_note: Optional[str] = None
    ingestion_mode: str = "single_upload"
    ingestion_batch_id: Optional[str] = None
    source_message_id: Optional[str] = None
    source_received_at: Optional[datetime] = None
    source: str


class AnalyzeResponse(BaseModel):
    stored: bool
    transaction: TransactionOut


class AnalyzeBulkResponse(BaseModel):
    stored: int
    failed: int
    transactions: list[TransactionOut]


class IngestionItemResult(BaseModel):
    index: int
    status: Literal["stored", "duplicate", "failed"]
    source_message_id: Optional[str] = None
    error: Optional[str] = None
    transaction: Optional[TransactionOut] = None


class IngestMessagesResponse(BaseModel):
    mode: Literal["single_upload", "inbox_sync", "statement_import"]
    batch_id: str
    total: int
    stored: int
    duplicates: int
    failed: int
    results: list[IngestionItemResult]


class TransactionsResponse(BaseModel):
    count: int
    transactions: list[TransactionOut]


class SummaryCategory(BaseModel):
    category: str
    amount: float


class SummaryResponse(BaseModel):
    currency: str
    total_spent: float
    categories: list[SummaryCategory]


class InsightsResponse(BaseModel):
    warnings: list[str]
    highlights: list[str]


class UpdateCategoryRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=64)
    apply_to_similar: bool = True
    correction_scope: Optional[
        Literal[
            "merchant_plus_account",
            "paybill_plus_account",
            "till_only",
            "merchant_only",
            "contact_only",
            "paybill_only",
            "normalized_text_exact",
            "broad",
        ]
    ] = None
    broad_apply: bool = False


class BudgetLimitUpsertRequest(BaseModel):
    monthly_budget: float = Field(..., ge=0)
    currency: str = Field(default="KES", min_length=1, max_length=8)


class BudgetLimitResponse(BaseModel):
    monthly_budget: float
    currency: str


class NotificationOut(BaseModel):
    id: int
    kind: str
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationsResponse(BaseModel):
    count: int
    unread: int
    notifications: list[NotificationOut]


class NotificationReadRequest(BaseModel):
    is_read: bool = True


class NotificationRefreshResponse(BaseModel):
    created: int
    total: int


class MessageResponse(BaseModel):
    message: str
