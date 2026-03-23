import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/auth/domain/models.dart';

class AppStorage {
  AppStorage({FlutterSecureStorage? secureStorage}) : _secureStorage = secureStorage ?? const FlutterSecureStorage();

  static const tokenKey = 'mpesa_mobile_auth_token';
  static const userKey = 'mpesa_mobile_auth_user';
  static const apiBaseKey = 'mpesa_mobile_api_base';

  final FlutterSecureStorage _secureStorage;

  Future<void> saveToken(String token) => _secureStorage.write(key: tokenKey, value: token);
  Future<String?> loadToken() => _secureStorage.read(key: tokenKey);
  Future<void> clearToken() => _secureStorage.delete(key: tokenKey);

  Future<void> saveUser(AuthUser user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(userKey, jsonEncode(user.toJson()));
  }

  Future<AuthUser?> loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(userKey);
    if (raw == null || raw.isEmpty) return null;
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) return null;
    return AuthUser.fromJson(decoded);
  }

  Future<void> clearUser() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(userKey);
  }

  Future<void> saveApiBase(String apiBase) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(apiBaseKey, apiBase);
  }

  Future<String?> loadApiBase() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(apiBaseKey);
  }
}
