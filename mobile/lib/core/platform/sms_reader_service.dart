import 'package:flutter/services.dart';

class SmsReadResult {
  const SmsReadResult({
    required this.id,
    required this.address,
    required this.body,
    required this.timestamp,
  });

  final String id;
  final String address;
  final String body;
  final DateTime? timestamp;

  factory SmsReadResult.fromMap(Map<dynamic, dynamic> payload) {
    final millis = payload['date'] as int?;
    return SmsReadResult(
      id: (payload['id'] ?? '').toString(),
      address: (payload['address'] ?? '').toString(),
      body: (payload['body'] ?? '').toString(),
      timestamp: millis == null ? null : DateTime.fromMillisecondsSinceEpoch(millis),
    );
  }
}

class SmsReaderService {
  SmsReaderService({MethodChannel? channel})
      : _channel = channel ?? const MethodChannel(_channelName);

  static const _channelName = 'mpesa_analyzer/sms_reader';
  final MethodChannel _channel;

  Future<List<SmsReadResult>> readRecentMpesaSms({int limit = 80}) async {
    final result = await _channel.invokeMethod<List<dynamic>>(
      'readRecentMpesaSms',
      {'limit': limit},
    );

    return (result ?? const [])
        .whereType<Map<dynamic, dynamic>>()
        .map(SmsReadResult.fromMap)
        .toList();
  }
}
