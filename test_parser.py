from backend.parser import parse_mpesa_message


def test_parse_sent_money_transaction():
    msg = "QAB12CD345 Confirmed. Ksh1,250.00 sent to JOHN DOE 0712345678 on 24/03/2026 at 8:14 PM."
    parsed = parse_mpesa_message(msg)
    assert str(parsed.amount) == "1250.00"
    assert parsed.direction == "expense"
    assert parsed.transaction_type == "send_money"
    assert parsed.contact_name == "John Doe"


def test_parse_paybill_with_account_reference():
    msg = "QXY98ZA765 Confirmed. KES 2,100.00 paid to KPLC paybill number 888880 for account 12345678 on 24/03/2026 at 7:00 AM."
    parsed = parse_mpesa_message(msg)
    assert parsed.paybill_number == "888880"
    assert parsed.account_reference == "12345678"
    assert parsed.transaction_type in {"buy_goods", "paybill"}
