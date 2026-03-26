from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.categorizer import ClassificationInput, classify_transaction, remember_manual_category
from backend.database import Base
from backend.models import CategoryLearningRule
from backend.normalizer import build_key, canonical_entity_name, clean_display_name, extract_account_reference, extract_phone_number, infer_entity_type, normalized_text_signature


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _classify(db: Session, message: str, **kwargs):
    return classify_transaction(
        db,
        user_id="u1",
        data=ClassificationInput(
            message=message,
            normalized_message=message.lower(),
            recipient=kwargs.get("recipient"),
            merchant_name=kwargs.get("merchant_name"),
            contact_name=kwargs.get("contact_name"),
            paybill_number=kwargs.get("paybill_number"),
            till_number=kwargs.get("till_number"),
            account_reference=kwargs.get("account_reference"),
            transaction_code=kwargs.get("transaction_code"),
            canonical_entity_name=kwargs.get("canonical_entity_name"),
            normalized_text_signature=kwargs.get("normalized_text_signature") or normalized_text_signature(message),
            parsed_direction=kwargs.get("parsed_direction", "expense"),
            parsed_sub_type=kwargs.get("parsed_sub_type", "unknown"),
            user_note=kwargs.get("user_note"),
        ),
    )


def test_precedence_manual_and_structured_beat_keyword_rules():
    db = _session()
    remember_manual_category(
        db,
        user_id="u1",
        category="rent",
        merchant_name="Cheruka Enterprises Ltd",
        contact_name=None,
        recipient="Cheruka Enterprises Ltd",
        paybill_number=None,
        till_number=None,
        account_reference="2.11a",
        normalized_message="sent to cheruka enterprises for account 2.11a",
        correction_scope="merchant_plus_account",
    )
    db.commit()

    result = _classify(
        db,
        "sent to CHERUKA ENTERPRISES LIMITED for account 2.11a",
        merchant_name="CHERUKA ENTERPRISES LIMITED",
        account_reference="2.11a",
        parsed_sub_type="send_money",
    )
    assert result.category == "rent"
    assert result.matched_priority_tier == 1
    assert result.matched_key_type == "merchant_plus_account"


def test_apply_to_similar_specificity_prevents_poisoning():
    db = _session()
    # specific scope
    remember_manual_category(
        db,
        user_id="u1",
        category="rent",
        merchant_name="Cheruka",
        contact_name=None,
        recipient="Cheruka",
        paybill_number=None,
        till_number=None,
        account_reference="2.11a",
        normalized_message="rent for account 2.11a",
        correction_scope="merchant_plus_account",
    )
    db.commit()

    match_specific = _classify(db, "paid to cheruka for account 2.11a", merchant_name="Cheruka", account_reference="2.11a")
    non_match_other = _classify(db, "paid to cheruka for account 3.02b", merchant_name="Cheruka", account_reference="3.02b")

    assert match_specific.category == "rent"
    assert non_match_other.category != "rent"


def test_paybill_plus_account_outweighs_paybill_only():
    db = _session()
    remember_manual_category(
        db,
        user_id="u1",
        category="fees",
        merchant_name=None,
        contact_name=None,
        recipient=None,
        paybill_number="888880",
        till_number=None,
        account_reference="admission-2026-04",
        normalized_message="school fees",
        correction_scope="paybill_plus_account",
    )
    remember_manual_category(
        db,
        user_id="u1",
        category="bills",
        merchant_name=None,
        contact_name=None,
        recipient=None,
        paybill_number="888880",
        till_number=None,
        account_reference=None,
        normalized_message="general token",
        correction_scope="paybill_only",
    )
    db.commit()

    r = _classify(db, "paybill 888880 for account admission-2026-04", paybill_number="888880", account_reference="admission-2026-04")
    assert r.category == "fees"
    assert r.matched_key_type == "paybill_plus_account"


def test_conflict_detection_and_needs_review_for_unresolved_ambiguity():
    db = _session()
    db.add(CategoryLearningRule(user_id="u1", match_key=build_key("merchant_only", merchant="Cheruka"), category="transport", usage_count=5, is_manual=False))
    db.commit()

    r = _classify(
        db,
        "sent to CHERUKA for account school fees paybill 888880",
        merchant_name="CHERUKA",
        paybill_number="888880",
        account_reference="school-fees",
        parsed_sub_type="send_money",
    )
    assert r.conflict_flag is True
    assert r.needs_review is True or r.confidence_band == "low"


def test_confidence_model_distinguishes_strong_vs_weak_matches():
    db = _session()
    remember_manual_category(
        db,
        user_id="u1",
        category="family",
        merchant_name=None,
        contact_name="Jane Doe",
        recipient="Jane Doe",
        paybill_number=None,
        till_number=None,
        account_reference=None,
        normalized_message="sent to jane doe",
        correction_scope="contact_only",
    )
    db.commit()

    strong = _classify(db, "sent to Jane Doe", contact_name="Jane Doe", recipient="Jane Doe")
    weak = _classify(db, "some random message maybe transport")

    assert strong.confidence_score > weak.confidence_score
    assert strong.confidence_band in {"high", "medium"}


def test_normalization_helpers_cover_noise_and_specificity():
    raw = " CHERUKA ENTERPRISES LIMITED... "
    assert clean_display_name(raw) == "Cheruka Enterprises Limited"
    assert canonical_entity_name(raw) == "cheruka"
    assert extract_account_reference("Paid to Cheruka for account room 2.11a on 20/03") == "room 2.11a"
    assert extract_phone_number("Sent to JOHN 0712345678") is not None
    assert infer_entity_type("Jane Doe") == "person"
