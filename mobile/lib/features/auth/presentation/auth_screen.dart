import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/auth_controller.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  bool _isLogin = true;
  late final TextEditingController _apiBaseController;
  final _identifierController = TextEditingController();
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _apiBaseController = TextEditingController(text: ref.read(authControllerProvider).apiBase);
  }

  @override
  void dispose() {
    _apiBaseController.dispose();
    _identifierController.dispose();
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(authControllerProvider);
    final controller = ref.read(authControllerProvider.notifier);
    _apiBaseController.value = _apiBaseController.value.copyWith(text: state.apiBase, selection: TextSelection.collapsed(offset: state.apiBase.length));

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('M-PESA Analyzer', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text('Phase 1 Flutter foundation', style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 16),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('API Base URL', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextField(controller: _apiBaseController, keyboardType: TextInputType.url, decoration: const InputDecoration(hintText: 'http://192.168.1.24:8000')),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => controller.updateApiBase(_apiBaseController.text),
                            child: const Text('Save API Base'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => controller.testApiBase(_apiBaseController.text),
                            child: const Text('Test API'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment<bool>(value: true, label: Text('Login')),
                  ButtonSegment<bool>(value: false, label: Text('Register')),
                ],
                selected: {_isLogin},
                onSelectionChanged: (selection) => setState(() => _isLogin = selection.first),
              ),
              const SizedBox(height: 12),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (_isLogin) ...[
                      TextField(controller: _identifierController, decoration: const InputDecoration(labelText: 'Email or Username')),
                      const SizedBox(height: 12),
                    ] else ...[
                      TextField(controller: _emailController, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email')),
                      const SizedBox(height: 12),
                      TextField(controller: _usernameController, decoration: const InputDecoration(labelText: 'Username')),
                      const SizedBox(height: 12),
                    ],
                    TextField(controller: _passwordController, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: state.busy
                          ? null
                          : () async {
                              if (_isLogin) {
                                await controller.login(
                                  identifier: _identifierController.text,
                                  password: _passwordController.text,
                                  apiBaseOverride: _apiBaseController.text,
                                );
                              } else {
                                await controller.register(
                                  email: _emailController.text,
                                  username: _usernameController.text,
                                  password: _passwordController.text,
                                  apiBaseOverride: _apiBaseController.text,
                                );
                              }
                            },
                      child: state.busy
                          ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : Text(_isLogin ? 'Sign In' : 'Create Account'),
                    ),
                  ],
                ),
              ),
              if (state.errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(state.errorMessage!, style: const TextStyle(color: Colors.red)),
              ],
              if (state.infoMessage != null) ...[
                const SizedBox(height: 12),
                Text(state.infoMessage!, style: const TextStyle(color: Colors.green)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Color(0xFFD6DEE8))),
      child: Padding(padding: const EdgeInsets.all(16), child: child),
    );
  }
}
