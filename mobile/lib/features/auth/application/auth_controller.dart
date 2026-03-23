import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/app_config.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_error.dart';
import '../../../core/storage/app_storage.dart';
import '../domain/models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final appStorageProvider = Provider<AppStorage>((ref) => AppStorage());
final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  final controller = AuthController(ref.read(apiClientProvider), ref.read(appStorageProvider));
  controller.bootstrap();
  return controller;
});

class AuthState {
  const AuthState({
    required this.booting,
    required this.busy,
    required this.apiBase,
    this.token,
    this.user,
    this.errorMessage,
    this.infoMessage,
  });

  final bool booting;
  final bool busy;
  final String apiBase;
  final String? token;
  final AuthUser? user;
  final String? errorMessage;
  final String? infoMessage;

  factory AuthState.initial() => AuthState(booting: true, busy: false, apiBase: AppConfig.defaultApiBase());

  AuthState copyWith({
    bool? booting,
    bool? busy,
    String? apiBase,
    String? token,
    AuthUser? user,
    String? errorMessage,
    String? infoMessage,
    bool clearToken = false,
    bool clearUser = false,
    bool clearMessages = false,
  }) {
    return AuthState(
      booting: booting ?? this.booting,
      busy: busy ?? this.busy,
      apiBase: apiBase ?? this.apiBase,
      token: clearToken ? null : token ?? this.token,
      user: clearUser ? null : user ?? this.user,
      errorMessage: clearMessages ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearMessages ? null : infoMessage ?? this.infoMessage,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._client, this._storage) : super(AuthState.initial());

  final ApiClient _client;
  final AppStorage _storage;

  Future<void> bootstrap() async {
    try {
      final persistedApiBase = AppConfig.normalizeApiBase(await _storage.loadApiBase() ?? '');
      final persistedToken = await _storage.loadToken();
      final persistedUser = await _storage.loadUser();

      state = state.copyWith(
        apiBase: persistedApiBase.isEmpty ? AppConfig.defaultApiBase() : persistedApiBase,
        token: persistedToken,
        user: persistedUser,
      );

      if (persistedToken != null && persistedToken.isNotEmpty) {
        try {
          final freshUser = await _client.currentUser(apiBase: state.apiBase, token: persistedToken);
          await _storage.saveUser(freshUser);
          state = state.copyWith(user: freshUser);
        } on ApiError catch (error) {
          if (error.statusCode == 401) {
            await logout();
          }
        }
      }
    } finally {
      state = state.copyWith(booting: false);
    }
  }

  Future<void> updateApiBase(String value) async {
    final normalized = AppConfig.normalizeApiBase(value);
    if (normalized.isEmpty) {
      state = state.copyWith(errorMessage: 'API base URL is required.', infoMessage: null);
      return;
    }

    await _storage.saveApiBase(normalized);
    state = state.copyWith(apiBase: normalized, infoMessage: 'API base updated.', errorMessage: null);
  }

  Future<void> login({required String identifier, required String password, String? apiBaseOverride}) async {
    await _authenticate(
      request: () => _client.login(
        apiBase: apiBaseOverride ?? state.apiBase,
        identifier: identifier.trim(),
        password: password.trim(),
      ),
    );
  }

  Future<void> register({required String email, required String username, required String password, String? apiBaseOverride}) async {
    await _authenticate(
      request: () => _client.register(
        apiBase: apiBaseOverride ?? state.apiBase,
        email: email.trim(),
        username: username.trim(),
        password: password.trim(),
      ),
    );
  }

  Future<void> _authenticate({required Future<AuthResponse> Function() request}) async {
    state = state.copyWith(busy: true, clearMessages: true);
    try {
      final result = await request();
      await _storage.saveToken(result.accessToken);
      await _storage.saveUser(result.user);
      state = state.copyWith(token: result.accessToken, user: result.user, busy: false, infoMessage: null, errorMessage: null);
    } on ApiError catch (error) {
      state = state.copyWith(busy: false, errorMessage: error.message, infoMessage: null);
    } catch (error) {
      state = state.copyWith(busy: false, errorMessage: error.toString(), infoMessage: null);
    }
  }

  Future<void> testApiBase(String value) async {
    final normalized = AppConfig.normalizeApiBase(value);
    if (normalized.isEmpty) {
      state = state.copyWith(errorMessage: 'API base URL is required.', infoMessage: null);
      return;
    }

    try {
      final response = await _client.health(normalized);
      final message = response['message'] as String? ?? 'API reachable.';
      state = state.copyWith(errorMessage: null, infoMessage: 'API reachable: $message');
    } on ApiError catch (error) {
      state = state.copyWith(errorMessage: error.message, infoMessage: null);
    }
  }

  Future<void> refreshUser() async {
    final token = state.token;
    if (token == null || token.isEmpty) return;

    try {
      final user = await _client.currentUser(apiBase: state.apiBase, token: token);
      await _storage.saveUser(user);
      state = state.copyWith(user: user, infoMessage: 'User profile refreshed.', errorMessage: null);
    } on ApiError catch (error) {
      state = state.copyWith(errorMessage: error.message, infoMessage: null);
    }
  }

  Future<void> logout() async {
    await _storage.clearToken();
    await _storage.clearUser();
    state = state.copyWith(clearToken: true, clearUser: true, infoMessage: null, errorMessage: null);
  }
}
