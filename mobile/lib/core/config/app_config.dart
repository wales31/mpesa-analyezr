import 'dart:io';

class AppConfig {
  static const envApiBase = String.fromEnvironment('MPESA_API_BASE', defaultValue: '');
  static const androidEmulatorBase = 'http://10.0.2.2:8000';
  static const iosSimulatorBase = 'http://127.0.0.1:8000';

  static String defaultApiBase() {
    final env = normalizeApiBase(envApiBase);
    if (env.isNotEmpty) return env;

    if (Platform.isAndroid) return androidEmulatorBase;
    return iosSimulatorBase;
  }

  static String normalizeApiBase(String value) {
    var normalized = value.trim().replaceAll(RegExp(r'/+$'), '');
    if (normalized.isEmpty) return '';
    if (!RegExp(r'^[a-zA-Z][a-zA-Z\d+\-.]*://').hasMatch(normalized)) {
      normalized = 'http://$normalized';
    }

    final uri = Uri.tryParse(normalized);
    if (uri != null && (uri.host == '127.0.0.1' || uri.host == 'localhost' || uri.host == '10.0.2.2') && !uri.hasPort) {
      normalized = uri.replace(port: 8000).toString().replaceFirst(RegExp(r'/$'), '');
    }
    return normalized;
  }
}
