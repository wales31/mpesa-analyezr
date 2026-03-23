import 'dart:async';

import 'package:flutter/foundation.dart';

enum AuthStatus { loading, unauthenticated, authenticated }

class AuthController extends ChangeNotifier {
  AuthStatus _status = AuthStatus.loading;
  String _statusMessage = 'Bootstrapping Flutter shell';
  bool _hasSession = false;

  AuthStatus get status => _status;
  String get statusMessage => _statusMessage;
  bool get hasSession => _hasSession;

  Future<void> bootstrap() async {
    _status = AuthStatus.loading;
    _statusMessage = 'Checking for an existing session';
    notifyListeners();

    await Future<void>.delayed(const Duration(milliseconds: 900));

    _status = _hasSession ? AuthStatus.authenticated : AuthStatus.unauthenticated;
    _statusMessage = _hasSession ? 'Session restored' : 'No saved session found';
    notifyListeners();
  }

  Future<void> signInPlaceholder() async {
    _status = AuthStatus.loading;
    _statusMessage = 'Creating placeholder session';
    notifyListeners();

    await Future<void>.delayed(const Duration(milliseconds: 500));

    _hasSession = true;
    _status = AuthStatus.authenticated;
    _statusMessage = 'Signed in';
    notifyListeners();
  }

  Future<void> signOutPlaceholder() async {
    _status = AuthStatus.loading;
    _statusMessage = 'Clearing placeholder session';
    notifyListeners();

    await Future<void>.delayed(const Duration(milliseconds: 300));

    _hasSession = false;
    _status = AuthStatus.unauthenticated;
    _statusMessage = 'Signed out';
    notifyListeners();
  }
}

