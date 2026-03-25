import 'package:flutter/material.dart';

import '../auth_controller.dart';
import 'classification_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const ClassificationScreen(),
        Positioned(
          right: 20,
          bottom: 24,
          child: FloatingActionButton.extended(
            onPressed: controller.signOutPlaceholder,
            icon: const Icon(Icons.logout_rounded),
            label: const Text('Sign out'),
          ),
        ),
      ],
    );
  }
}
