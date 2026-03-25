import 'package:flutter_test/flutter_test.dart';
import 'package:mpesa_mobile/models/parsed_mpesa_message.dart';
import 'package:mpesa_mobile/services/mpesa_parser_service.dart';

void main() {
  final parser = MpesaParserService();

  group('MpesaParserService.detectTransactionType', () {
    test('classifies sent money', () {
      const sms =
          'QK123ABC45 Confirmed. Ksh500.00 sent to JOHN DOE 0712345678 on 24/03/26 at 10:32 AM. New M-PESA balance is Ksh1,200.50.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.sentMoney);
      expect(result.amount, 500.00);
      expect(result.counterparty, 'JOHN DOE 0712345678');
      expect(result.transactionCode, 'QK123ABC45');
      expect(result.balance, 1200.50);
      expect(result.parseConfidence, ParseConfidence.high);
    });

    test('classifies received money without false sent classification', () {
      const sms =
          'QK223XYZ11 Confirmed. You have received Ksh2,150.00 from MARY WANJIKU 0722001100 on 24/03/26 at 3:40 PM. New M-PESA balance is Ksh5,600.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.receivedMoney);
      expect(result.counterparty, 'MARY WANJIKU 0722001100');
      expect(result.parseConfidence, ParseConfidence.high);
    });

    test('classifies paybill distinctly from buy goods', () {
      const sms =
          'QK778PAY22 Confirmed. Ksh1,800.00 paid to KPLC PREPAID PayBill 888880 Account: 123456 on 24/03/26 at 8:20 PM. New M-PESA balance is Ksh2,300.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.paybill);
      expect(result.accountReference, isNotNull);
      expect(result.parseConfidence, ParseConfidence.high);
    });

    test('classifies buy goods transaction', () {
      const sms =
          'QK998TILL33 Confirmed. Ksh350.00 paid to NAIVAS SUPERMARKET TILL 454545 on 24/03/26 at 1:22 PM. New M-PESA balance is Ksh980.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.buyGoods);
      expect(result.counterparty, contains('NAIVAS SUPERMARKET'));
    });

    test('classifies withdrawal transaction', () {
      const sms =
          'QK009WDR44 Confirmed. Ksh3,000.00 withdrawn at AGENT 123456 - NAIROBI CBD on 24/03/26 at 9:01 AM. New M-PESA balance is Ksh700.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.withdrawal);
    });

    test('classifies airtime purchase transaction', () {
      const sms =
          'QK665AIR55 Confirmed. You bought airtime of Ksh100.00 on 24/03/26 at 7:00 AM. New M-PESA balance is Ksh1,400.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.airtimePurchase);
    });

    test('classifies deposit transaction', () {
      const sms =
          'QK741DEP66 Confirmed. Cash deposited to M-PESA account Ksh4,000.00 by agent 654321 on 24/03/26 at 11:20 AM. New M-PESA balance is Ksh6,450.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.deposit);
    });

    test('classifies reversal with higher priority than transfer', () {
      const sms =
          'QK100REV77 Confirmed. Reversal of transaction QK123ABC45 has been completed. Ksh500.00 has been reversed to your account on 24/03/26 at 5:11 PM. New M-PESA balance is Ksh2,000.00.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.reversal);
      expect(result.parseConfidence, ParseConfidence.high);
    });

    test('classifies balance-only informational message', () {
      const sms = 'M-PESA balance is Ksh850.25 as at 24/03/26 18:10.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.balanceMessage);
      expect(result.amount, 850.25);
    });

    test('returns unknown with low confidence for non-mpesa message', () {
      const sms = 'Reminder: your weekly bundle expires tomorrow at midnight.';
      final result = parser.parse(sms);

      expect(result.transactionType, TransactionType.unknown);
      expect(result.parseConfidence, ParseConfidence.low);
      expect(result.rawMessage, sms);
    });
  });
}
