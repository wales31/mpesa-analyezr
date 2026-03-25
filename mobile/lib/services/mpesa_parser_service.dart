import '../models/parsed_mpesa_message.dart';
import '../enums/transaction_type.dart';
import '../utils/mpesa_patterns.dart';

class TransactionTypeDetection {
  const TransactionTypeDetection({
    required this.type,
    required this.reason,
    required this.confidence,
  });

  final TransactionType type;
  final String reason;
  final ParseConfidence confidence;
}

class MpesaParserService {
  ParsedMpesaMessage parse(String rawMessage) {
    final normalized = _normalize(rawMessage);
    final detection = detectTransactionType(normalized);

    final amount = _extractAmount(rawMessage);
    final transactionCode = _extractTransactionCode(rawMessage);
    final balance = _extractBalance(rawMessage);
    final transactionDate = _extractDate(rawMessage);
    final phoneNumber = _extractPhoneNumber(rawMessage);
    final accountReference = _extractAccountReference(rawMessage);
    final counterparty = _extractCounterparty(detection.type, rawMessage);

    return ParsedMpesaMessage(
      transactionType: detection.type,
      transactionTypeReason: detection.reason,
      parseConfidence: detection.confidence,
      amount: amount,
      transactionCode: transactionCode,
      balance: balance,
      transactionDate: transactionDate,
      phoneNumber: phoneNumber,
      accountReference: accountReference,
      counterparty: counterparty,
      rawMessage: rawMessage,
    );
  }

  TransactionTypeDetection detectTransactionType(String message) {
    // Priority rule: reversals must win over transfer types.
    if (MpesaPatterns.reversal.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.reversal,
        reason: 'Matched reversal keywords (reversal/reversed).',
        confidence: ParseConfidence.high,
      );
    }

    // Priority rule: pure balance notifications should not be treated as transactions.
    if (MpesaPatterns.balanceOnly.hasMatch(message) &&
        !_looksLikeTransactionalMessage(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.balanceMessage,
        reason: 'Matched balance-only keywords without transactional signals.',
        confidence: ParseConfidence.high,
      );
    }

    final hasPaidTo = message.contains('paid to');
    final hasPaybillSignals = message.contains('paybill') ||
        message.contains('business number') ||
        message.contains('account no') ||
        message.contains('account:');

    if (hasPaidTo && hasPaybillSignals || MpesaPatterns.paybill.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.paybill,
        reason: 'Matched paid-to plus paybill/business/account signals.',
        confidence: ParseConfidence.high,
      );
    }

    final hasBuyGoodsSignals = message.contains('till') ||
        message.contains('buy goods') ||
        message.contains('customer buy goods');

    if ((hasPaidTo && hasBuyGoodsSignals) ||
        (MpesaPatterns.buyGoods.hasMatch(message) && !hasPaybillSignals)) {
      return const TransactionTypeDetection(
        type: TransactionType.buyGoods,
        reason: 'Matched buy-goods/till merchant payment wording.',
        confidence: ParseConfidence.high,
      );
    }

    if (MpesaPatterns.sentMoney.hasMatch(message) &&
        !MpesaPatterns.receivedMoney.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.sentMoney,
        reason: 'Matched "sent to" and no receive indicators.',
        confidence: ParseConfidence.high,
      );
    }

    if (MpesaPatterns.receivedMoney.hasMatch(message) &&
        !message.contains('sent to')) {
      return const TransactionTypeDetection(
        type: TransactionType.receivedMoney,
        reason: 'Matched receive/funds received indicators.',
        confidence: ParseConfidence.high,
      );
    }

    if (MpesaPatterns.airtime.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.airtimePurchase,
        reason: 'Matched bought airtime wording.',
        confidence: ParseConfidence.high,
      );
    }

    if (MpesaPatterns.withdrawal.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.withdrawal,
        reason: 'Matched withdrawal/Give Ksh keyword patterns.',
        confidence: ParseConfidence.medium,
      );
    }

    if (MpesaPatterns.deposit.hasMatch(message) &&
        !MpesaPatterns.withdrawal.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.deposit,
        reason: 'Matched cash deposit wording.',
        confidence: ParseConfidence.medium,
      );
    }

    if (MpesaPatterns.balanceOnly.hasMatch(message)) {
      return const TransactionTypeDetection(
        type: TransactionType.balanceMessage,
        reason: 'Matched balance keywords as fallback.',
        confidence: ParseConfidence.medium,
      );
    }

    return const TransactionTypeDetection(
      type: TransactionType.unknown,
      reason: 'No high-confidence transaction type rule matched.',
      confidence: ParseConfidence.low,
    );
  }

  String _normalize(String message) {
    return message.toLowerCase().replaceAll(RegExp(r'\s+'), ' ').trim();
  }

  bool _looksLikeTransactionalMessage(String message) {
    const transactionalHints = [
      'sent to',
      'received',
      'paid to',
      'withdraw',
      'bought airtime',
      'reversed',
      'deposited',
    ];
    return transactionalHints.any(message.contains);
  }

  double? _extractAmount(String message) {
    final match = MpesaPatterns.amount.firstMatch(message);
    return MpesaPatterns.parseMoney(match?.group(1));
  }

  String? _extractTransactionCode(String message) {
    return MpesaPatterns.transactionCode.firstMatch(message)?.group(1);
  }

  double? _extractBalance(String message) {
    final match = MpesaPatterns.balance.firstMatch(message);
    return MpesaPatterns.parseMoney(match?.group(1));
  }

  DateTime? _extractDate(String message) {
    final match = MpesaPatterns.dateTime.firstMatch(message);
    if (match == null) return null;

    final datePart = match.group(2);
    final timePart = match.group(3);
    final period = match.group(4);

    if (datePart == null || timePart == null) return null;

    final dateSegments = datePart.split(RegExp(r'[/-]'));
    if (dateSegments.length != 3) return null;

    final day = int.tryParse(dateSegments[0]);
    final month = int.tryParse(dateSegments[1]);
    var year = int.tryParse(dateSegments[2]);

    if (day == null || month == null || year == null) return null;
    if (year < 100) year += 2000;

    final timeSegments = timePart.split(':');
    if (timeSegments.length != 2) return null;

    var hour = int.tryParse(timeSegments[0]);
    final minute = int.tryParse(timeSegments[1]);
    if (hour == null || minute == null) return null;

    if (period != null) {
      final normalizedPeriod = period.toUpperCase();
      if (normalizedPeriod == 'PM' && hour < 12) hour += 12;
      if (normalizedPeriod == 'AM' && hour == 12) hour = 0;
    }

    return DateTime(year, month, day, hour, minute);
  }

  String? _extractPhoneNumber(String message) {
    return MpesaPatterns.phoneNumber.firstMatch(message)?.group(0);
  }

  String? _extractAccountReference(String message) {
    final match = MpesaPatterns.accountReference.firstMatch(message);
    return match?.group(1)?.trim();
  }

  String? _extractCounterparty(TransactionType type, String message) {
    RegExp? pattern;
    switch (type) {
      case TransactionType.sentMoney:
        pattern = MpesaPatterns.sentCounterparty;
        break;
      case TransactionType.receivedMoney:
        pattern = MpesaPatterns.receivedCounterparty;
        break;
      case TransactionType.paybill:
      case TransactionType.buyGoods:
        pattern = MpesaPatterns.paidToCounterparty;
        break;
      default:
        pattern = null;
    }

    if (pattern == null) return null;

    final candidate = pattern.firstMatch(message)?.group(1)?.trim();
    if (candidate == null || candidate.isEmpty) return null;

    return candidate
        .replaceAll(RegExp(r'\s+new\s+m-pesa\s+balance.*$', caseSensitive: false), '')
        .replaceAll(RegExp(r'\s+on\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}.*$', caseSensitive: false), '')
        .trim();
  }
}
