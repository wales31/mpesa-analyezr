import 'dart:io';

import 'package:dio/dio.dart';

import '../../features/auth/domain/models.dart';
import '../config/app_config.dart';
import 'api_error.dart';

class ApiClient {
  ApiClient({Dio? dio}) : _dio = dio ?? Dio();

  final Dio _dio;

  Future<Map<String, dynamic>> health(String apiBase) async {
    return _request(apiBase: apiBase, path: '/');
  }

  Future<AuthResponse> register({required String apiBase, required String email, required String username, required String password}) async {
    final response = await _request(
      apiBase: apiBase,
      path: '/auth/register',
      method: 'POST',
      body: {'email': email, 'username': username, 'password': password},
    );
    return AuthResponse.fromJson(response);
  }

  Future<AuthResponse> login({required String apiBase, required String identifier, required String password}) async {
    final response = await _request(
      apiBase: apiBase,
      path: '/auth/login',
      method: 'POST',
      body: {'identifier': identifier, 'password': password},
    );
    return AuthResponse.fromJson(response);
  }

  Future<AuthUser> currentUser({required String apiBase, required String token}) async {
    final response = await _request(apiBase: apiBase, path: '/auth/me', token: token);
    return AuthUser.fromJson(response);
  }

  Future<SummaryResponse> getSummary({required String apiBase, required String token}) async {
    final response = await _request(apiBase: apiBase, path: '/summary', token: token);
    return SummaryResponse.fromJson(response);
  }

  Future<Map<String, dynamic>> _request({
    required String apiBase,
    required String path,
    String method = 'GET',
    String? token,
    Map<String, dynamic>? body,
  }) async {
    final normalized = AppConfig.normalizeApiBase(apiBase);
    if (normalized.isEmpty) throw ApiError('API base URL is required.');

    final bases = <String>[normalized, ..._fallbackBases(normalized)].toSet().toList();
    DioException? lastError;

    for (final base in bases) {
      try {
        final response = await _dio.request<Map<String, dynamic>>(
          '$base$path',
          data: body,
          options: Options(
            method: method,
            headers: {
              HttpHeaders.acceptHeader: 'application/json',
              if (token != null && token.isNotEmpty) HttpHeaders.authorizationHeader: 'Bearer $token',
            },
            responseType: ResponseType.json,
            validateStatus: (_) => true,
          ),
        );

        final payload = response.data ?? <String, dynamic>{};
        if (response.statusCode != null && response.statusCode! >= 200 && response.statusCode! < 300) {
          return payload;
        }

        throw ApiError(_extractMessage(payload, response.statusMessage), statusCode: response.statusCode);
      } on DioException catch (error) {
        lastError = error;
      }
    }

    throw ApiError(
      'Could not reach API at $normalized. Make sure the backend is running and reachable from your device. Last error: ${lastError?.message ?? 'unknown'}',
    );
  }

  List<String> _fallbackBases(String normalized) {
    if (!Platform.isAndroid) return const [];

    final fallbackBases = <String>{
      AppConfig.normalizeApiBase(normalized.replaceFirst('://127.0.0.1', '://10.0.2.2')),
      AppConfig.normalizeApiBase(normalized.replaceFirst('://localhost', '://10.0.2.2')),
      AppConfig.normalizeApiBase(normalized.replaceFirst('://10.0.2.2', '://127.0.0.1')),
      AppConfig.normalizeApiBase(normalized.replaceFirst('://localhost', '://127.0.0.1')),
    };

    fallbackBases.remove('');
    fallbackBases.remove(normalized);
    return fallbackBases.toList();
  }

  String _extractMessage(Map<String, dynamic> payload, String? fallback) {
    final detail = payload['detail'];
    if (detail is String && detail.trim().isNotEmpty) return detail.trim();
    final message = payload['message'];
    if (message is String && message.trim().isNotEmpty) return message.trim();
    return fallback?.trim().isNotEmpty == true ? fallback!.trim() : 'Request failed.';
  }
}
