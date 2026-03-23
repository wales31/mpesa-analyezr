import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/domain/models.dart';

final summaryProvider = FutureProvider.autoDispose<SummaryResponse?>((ref) async {
  final authState = ref.watch(authControllerProvider);
  final token = authState.token;
  if (token == null || token.isEmpty) return null;
  final client = ref.read(apiClientProvider);
  return client.getSummary(apiBase: authState.apiBase, token: token);
});

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  late final TextEditingController _apiBaseController;

  @override
  void initState() {
    super.initState();
    _apiBaseController = TextEditingController(text: ref.read(authControllerProvider).apiBase);
  }

  @override
  void dispose() {
    _apiBaseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final controller = ref.read(authControllerProvider.notifier);
    final summaryAsync = ref.watch(summaryProvider);

    _apiBaseController.value = _apiBaseController.value.copyWith(text: authState.apiBase, selection: TextSelection.collapsed(offset: authState.apiBase.length));

    return Scaffold(
      appBar: AppBar(title: const Text('M-PESA Dashboard')),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            await controller.refreshUser();
            ref.invalidate(summaryProvider);
            await ref.read(summaryProvider.future);
          },
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Signed in user', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text('Username: ${authState.user?.username ?? '-'}'),
                    Text('Email: ${authState.user?.email ?? '-'}'),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('API Settings', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextField(controller: _apiBaseController, keyboardType: TextInputType.url, decoration: const InputDecoration(hintText: 'http://192.168.1.24:8000')),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () async {
                              await controller.updateApiBase(_apiBaseController.text);
                              ref.invalidate(summaryProvider);
                            },
                            child: const Text('Save API Base'),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () async {
                              await controller.refreshUser();
                              ref.invalidate(summaryProvider);
                            },
                            child: const Text('Refresh Profile'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              _Card(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Summary', style: Theme.of(context).textTheme.titleMedium),
                        OutlinedButton(
                          onPressed: () => ref.invalidate(summaryProvider),
                          child: const Text('Refresh Summary'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    summaryAsync.when(
                      data: (summary) {
                        if (summary == null) return const Text('No summary yet.');
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Total spent', style: Theme.of(context).textTheme.bodySmall),
                            const SizedBox(height: 4),
                            Text(_formatAmount(summary.totalSpent, summary.currency), style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                            const SizedBox(height: 16),
                            Text('Categories', style: Theme.of(context).textTheme.titleSmall),
                            const SizedBox(height: 8),
                            if (summary.categories.isEmpty) const Text('No category data yet.'),
                            ...summary.categories.map(
                              (item) => Padding(
                                padding: const EdgeInsets.symmetric(vertical: 6),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [Text(item.category), Text(_formatAmount(item.amount, summary.currency))],
                                ),
                              ),
                            ),
                          ],
                        );
                      },
                      loading: () => const Center(child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator())),
                      error: (error, _) => Text('$error', style: const TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              FilledButton.tonal(
                onPressed: () async {
                  await controller.logout();
                },
                child: const Text('Sign Out'),
              ),
              if (authState.errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(authState.errorMessage!, style: const TextStyle(color: Colors.red)),
              ],
              if (authState.infoMessage != null) ...[
                const SizedBox(height: 12),
                Text(authState.infoMessage!, style: const TextStyle(color: Colors.green)),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _formatAmount(double value, String currency) {
    return '$currency ${value.toStringAsFixed(value.truncateToDouble() == value ? 0 : 2)}';
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
