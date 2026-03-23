import 'package:flutter/material.dart';

import 'auth_controller.dart';
import 'screens/auth_screen.dart';
import 'screens/home_screen.dart';

class AppColors {
  static const background = Color(0xFFF2F6FB);
  static const surface = Colors.white;
  static const primary = Color(0xFF0D8A43);
  static const textPrimary = Color(0xFF0F1722);
  static const textSecondary = Color(0xFF44556A);
  static const border = Color(0xFFD6DEE8);
}

class MpesaAnalyzerApp extends StatefulWidget {
  const MpesaAnalyzerApp({super.key});

  @override
  State<MpesaAnalyzerApp> createState() => _MpesaAnalyzerAppState();
}

class _MpesaAnalyzerAppState extends State<MpesaAnalyzerApp> {
  late final AuthController _authController;

  @override
  void initState() {
    super.initState();
    _authController = AuthController()..bootstrap();
  }

  @override
  void dispose() {
    _authController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _authController,
      builder: (context, _) {
        return MaterialApp(
          title: 'M-PESA Analyzer',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: AppColors.primary,
              brightness: Brightness.light,
            ),
            scaffoldBackgroundColor: AppColors.background,
            useMaterial3: true,
            textTheme: Theme.of(context).textTheme.apply(
                  bodyColor: AppColors.textPrimary,
                  displayColor: AppColors.textPrimary,
                ),
            cardTheme: const CardThemeData(
              color: AppColors.surface,
              elevation: 0,
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.all(Radius.circular(16)),
                side: BorderSide(color: AppColors.border),
              ),
            ),
            inputDecorationTheme: const InputDecorationTheme(
              filled: true,
              fillColor: Color(0xFFF9FBFD),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                borderSide: BorderSide(color: AppColors.border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                borderSide: BorderSide(color: AppColors.border),
              ),
            ),
          ),
          onGenerateRoute: (settings) {
            final screen = switch (_authController.status) {
              AuthStatus.loading => LoadingScreen(controller: _authController),
              AuthStatus.authenticated => HomeScreen(controller: _authController),
              AuthStatus.unauthenticated => AuthScreen(controller: _authController),
            };

            return MaterialPageRoute<void>(
              builder: (_) => screen,
              settings: settings,
            );
          },
        );
      },
    );
  }
}

class LoadingScreen extends StatelessWidget {
  const LoadingScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 16),
                Text(
                  'Starting app...',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  controller.statusMessage,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

