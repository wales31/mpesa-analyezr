import 'package:flutter/material.dart';

import '../app.dart';
import '../auth_controller.dart';

class AuthScreen extends StatelessWidget {
  const AuthScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'M-PESA Analyzer',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Flutter shell — authentication placeholder',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppColors.textSecondary,
                            ),
                      ),
                      const SizedBox(height: 20),
                      const _PlaceholderField(label: 'API Base URL'),
                      const SizedBox(height: 12),
                      const _PlaceholderField(label: 'Email or Username'),
                      const SizedBox(height: 12),
                      const _PlaceholderField(label: 'Password', obscureText: true),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: controller.signInPlaceholder,
                          child: const Text('Continue to Home Placeholder'),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Phase 1 goal: verify startup, auth gate, navigation, and theming before API integration.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.textSecondary,
                            ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PlaceholderField extends StatelessWidget {
  const _PlaceholderField({required this.label, this.obscureText = false});

  final String label;
  final bool obscureText;

  @override
  Widget build(BuildContext context) {
    return TextField(
      enabled: false,
      obscureText: obscureText,
      decoration: InputDecoration(
        labelText: label,
        hintText: 'Placeholder',
      ),
    );
  }
}

