import 'package:flutter_test/flutter_test.dart';
import 'package:mpesa_mobile/enums/financial_category.dart';
import 'package:mpesa_mobile/enums/transaction_type.dart';
import 'package:mpesa_mobile/services/transaction_categorization_service.dart';

void main() {
  const service = TransactionCategorizationService();

  group('TransactionCategorizationService.categorizeParsedTransaction', () {
    test('maps income transaction types correctly', () {
      expect(
        service.categorizeParsedTransaction(TransactionType.receivedMoney),
        FinancialCategory.income,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.deposit),
        FinancialCategory.income,
      );
    });

    test('maps expense transaction types correctly', () {
      expect(
        service.categorizeParsedTransaction(TransactionType.sentMoney),
        FinancialCategory.expense,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.paybill),
        FinancialCategory.expense,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.buyGoods),
        FinancialCategory.expense,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.airtimePurchase),
        FinancialCategory.expense,
      );
    });

    test('maps withdrawal to transfer by default', () {
      expect(
        service.categorizeParsedTransaction(TransactionType.withdrawal),
        FinancialCategory.transfer,
      );
    });

    test('maps reversal and ignored message types safely for analytics', () {
      expect(
        service.categorizeParsedTransaction(TransactionType.reversal),
        FinancialCategory.reversal,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.balanceMessage),
        FinancialCategory.ignored,
      );
      expect(
        service.categorizeParsedTransaction(TransactionType.unknown),
        FinancialCategory.uncategorized,
      );
    });

    test('supports optional user override for sent-money transfer classification', () {
      final category = service.categorizeParsedTransaction(
        TransactionType.sentMoney,
        context: const CategorizationContext(userClassifiedAsTransfer: true),
      );

      expect(category, FinancialCategory.transfer);
    });
  });

  group('TransactionCategorizationService.analyticsLabel', () {
    test('returns friendly labels for dashboard/reporting', () {
      expect(service.analyticsLabel(FinancialCategory.income), 'Income');
      expect(service.analyticsLabel(FinancialCategory.expense), 'Expense');
      expect(service.analyticsLabel(FinancialCategory.transfer), 'Transfer');
      expect(service.analyticsLabel(FinancialCategory.reversal), 'Reversal');
      expect(service.analyticsLabel(FinancialCategory.ignored), 'Ignored');
      expect(
        service.analyticsLabel(FinancialCategory.uncategorized),
        'Needs Review',
      );
    });
  });

  group('TransactionCategorizationService.isIncludedInDashboard', () {
    test('excludes ignored category and keeps other categories', () {
      expect(service.isIncludedInDashboard(FinancialCategory.ignored), isFalse);
      expect(service.isIncludedInDashboard(FinancialCategory.income), isTrue);
      expect(service.isIncludedInDashboard(FinancialCategory.expense), isTrue);
      expect(service.isIncludedInDashboard(FinancialCategory.transfer), isTrue);
      expect(service.isIncludedInDashboard(FinancialCategory.reversal), isTrue);
      expect(
        service.isIncludedInDashboard(FinancialCategory.uncategorized),
        isTrue,
      );
    });
  });
}
