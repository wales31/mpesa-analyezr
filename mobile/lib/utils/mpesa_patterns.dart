class MpesaPatterns {
  const MpesaPatterns._();

  static final transactionCode = RegExp(r'\b([A-Z0-9]{10,12})\b');

  static final amount = RegExp(
    r'(?:Ksh|KSh|KES)\s*([\d,]+(?:\.\d{1,2})?)',
    caseSensitive: false,
  );

  static final balance = RegExp(
    r'(?:(?:New\s+M-PESA\s+balance\s+is)|(?:M-PESA\s+balance\s+is)|(?:balance\s+is))\s*(?:Ksh|KSh|KES)?\s*([\d,]+(?:\.\d{1,2})?)',
    caseSensitive: false,
  );

  static final phoneNumber = RegExp(r'\b(?:\+?254|0)\d{9}\b');

  static final accountReference = RegExp(
    r'(?:Acc(?:ount)?\.?\s*(?:No\.?|Ref(?:erence)?\.?|for)?\s*[:\-]?\s*)([A-Z0-9\- ]{3,})',
    caseSensitive: false,
  );

  static final dateTime = RegExp(
    r'\b(on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\s+at\s+(\d{1,2}:\d{2})\s*([AP]M)?',
    caseSensitive: false,
  );

  // Type-specific patterns.
  static final sentMoney = RegExp(r'\bsent\s+to\b', caseSensitive: false);
  static final receivedMoney = RegExp(
    r'\b(?:you\s+have\s+)?received\b|\bfunds\s+received\b',
    caseSensitive: false,
  );
  static final paybill = RegExp(
    r'\b(?:paid\s+to|payment\s+to)\b.*\b(?:paybill|business\s+number|account)\b|\bpaybill\b',
    caseSensitive: false,
  );
  static final buyGoods = RegExp(
    r'\b(?:paid\s+to|buy\s+goods|customer\s+buy\s+goods)\b|\btill\b',
    caseSensitive: false,
  );
  static final withdrawal = RegExp(
    r'\bwithdrawn\b|\bwithdraw\b|\bgive\s+ksh\b',
    caseSensitive: false,
  );
  static final airtime = RegExp(
    r'\bbought\s+airtime\b|\bairtime\s+purchase\b',
    caseSensitive: false,
  );
  static final deposit = RegExp(
    r'\bgive\s+ksh\b|\bdeposited\s+to\b|\bcash\s+deposit\b',
    caseSensitive: false,
  );
  static final reversal = RegExp(
    r'\breversal\b|\breversed\b|\bhas\s+been\s+reversed\b',
    caseSensitive: false,
  );
  static final balanceOnly = RegExp(
    r'\b(?:your\s+m-pesa\s+balance|m-pesa\s+balance\s+is|statement\s+balance)\b',
    caseSensitive: false,
  );

  static final sentCounterparty = RegExp(
    r'sent\s+to\s+([^\.\n]+)',
    caseSensitive: false,
  );
  static final receivedCounterparty = RegExp(
    r'(?:from|received\s+from)\s+([^\.\n]+)',
    caseSensitive: false,
  );
  static final paidToCounterparty = RegExp(
    r'paid\s+to\s+([^\.\n]+)',
    caseSensitive: false,
  );

  static double? parseMoney(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    final sanitized = value.replaceAll(',', '').trim();
    return double.tryParse(sanitized);
  }
}
