import '../enums/financial_category.dart';
import '../enums/transaction_type.dart';

/// Optional context for richer categorization rules.
///
/// This keeps the API open for future rules such as salary detection,
/// customer/business income splitting, or utility bill tagging.
class CategorizationContext {
  const CategorizationContext({
    this.counterparty,
    this.accountReference,
    this.userClassifiedAsTransfer = false,
  });

  final String? counterparty;
  final String? accountReference;
  final bool userClassifiedAsTransfer;
}

class TransactionCategorizationService {
  const TransactionCategorizationService();

  static const Map<TransactionType, FinancialCategory> _baseRules = {
    TransactionType.receivedMoney: FinancialCategory.income,
    TransactionType.deposit: FinancialCategory.income,
    TransactionType.sentMoney: FinancialCategory.expense,
    TransactionType.paybill: FinancialCategory.expense,
    TransactionType.buyGoods: FinancialCategory.expense,
    TransactionType.airtimePurchase: FinancialCategory.expense,
    TransactionType.withdrawal: FinancialCategory.transfer,
    TransactionType.reversal: FinancialCategory.reversal,
    TransactionType.balanceMessage: FinancialCategory.ignored,
    TransactionType.unknown: FinancialCategory.uncategorized,
  };

  FinancialCategory categorizeParsedTransaction(
    TransactionType type, {
    CategorizationContext context = const CategorizationContext(),
  }) {
    // Extensibility hook for future user-driven transfer classification.
    if (type == TransactionType.sentMoney && context.userClassifiedAsTransfer) {
      return FinancialCategory.transfer;
    }

    return _baseRules[type] ?? FinancialCategory.uncategorized;
  }

  String analyticsLabel(FinancialCategory category) {
    switch (category) {
      case FinancialCategory.income:
        return 'Income';
      case FinancialCategory.expense:
        return 'Expense';
      case FinancialCategory.transfer:
        return 'Transfer';
      case FinancialCategory.reversal:
        return 'Reversal';
      case FinancialCategory.ignored:
        return 'Ignored';
      case FinancialCategory.uncategorized:
        return 'Needs Review';
    }
  }

  bool isIncludedInDashboard(FinancialCategory category) {
    return category != FinancialCategory.ignored;
  }
}
