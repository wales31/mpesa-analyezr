enum TransactionType {
  sentMoney,
  receivedMoney,
  paybill,
  buyGoods,
  withdrawal,
  airtimePurchase,
  deposit,
  reversal,
  balanceMessage,
  unknown,
}

enum ParseConfidence { high, medium, low }

class ParsedMpesaMessage {
  const ParsedMpesaMessage({
    required this.transactionType,
    required this.rawMessage,
    required this.parseConfidence,
    this.transactionTypeReason,
    this.amount,
    this.counterparty,
    this.transactionCode,
    this.balance,
    this.transactionDate,
    this.phoneNumber,
    this.accountReference,
  });

  final TransactionType transactionType;
  final String rawMessage;
  final ParseConfidence parseConfidence;
  final String? transactionTypeReason;

  final double? amount;
  final String? counterparty;
  final String? transactionCode;
  final double? balance;
  final DateTime? transactionDate;
  final String? phoneNumber;
  final String? accountReference;

  Map<String, dynamic> toJson() => {
        'transactionType': transactionType.name,
        'amount': amount,
        'counterparty': counterparty,
        'transactionCode': transactionCode,
        'balance': balance,
        'transactionDate': transactionDate?.toIso8601String(),
        'phoneNumber': phoneNumber,
        'accountReference': accountReference,
        'rawMessage': rawMessage,
        'parseConfidence': parseConfidence.name,
        'transactionTypeReason': transactionTypeReason,
      };
}
