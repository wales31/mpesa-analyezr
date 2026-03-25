import 'dart:math' as math;

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

final transactionsProvider =
    FutureProvider.autoDispose<TransactionsResponse?>((ref) async {
  final authState = ref.watch(authControllerProvider);
  final token = authState.token;
  if (token == null || token.isEmpty) return null;
  final client = ref.read(apiClientProvider);
  return client.listTransactions(
    apiBase: authState.apiBase,
    token: token,
    limit: 60,
  );
});

final budgetProvider = FutureProvider.autoDispose<BudgetLimitResponse?>((ref) async {
  final authState = ref.watch(authControllerProvider);
  final token = authState.token;
  if (token == null || token.isEmpty) return null;
  final client = ref.read(apiClientProvider);
  return client.getBudgetLimit(apiBase: authState.apiBase, token: token);
});

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _currentTab = 0;
  late final TextEditingController _apiBaseController;
  late final TextEditingController _budgetController;

  @override
  void initState() {
    super.initState();
    _apiBaseController =
        TextEditingController(text: ref.read(authControllerProvider).apiBase);
    _budgetController = TextEditingController();
  }

  @override
  void dispose() {
    _apiBaseController.dispose();
    _budgetController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final controller = ref.read(authControllerProvider.notifier);
    final summaryAsync = ref.watch(summaryProvider);
    final transactionsAsync = ref.watch(transactionsProvider);
    final budgetAsync = ref.watch(budgetProvider);

    _apiBaseController.value = _apiBaseController.value.copyWith(
      text: authState.apiBase,
      selection: TextSelection.collapsed(offset: authState.apiBase.length),
    );

    final pages = [
      _buildHomeTab(context, summaryAsync, budgetAsync, transactionsAsync),
      _buildTransactionsTab(context, transactionsAsync),
      _buildAnalyticsTab(context, summaryAsync, transactionsAsync),
      _buildSettingsTab(context, authState, controller, budgetAsync),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('M-PESA Analyzer'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => _refreshAll(controller),
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: SafeArea(child: pages[_currentTab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentTab,
        onDestinationSelected: (index) => setState(() => _currentTab = index),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home_rounded),
              label: 'Home'),
          NavigationDestination(
              icon: Icon(Icons.receipt_long_outlined),
              selectedIcon: Icon(Icons.receipt_long_rounded),
              label: 'Transactions'),
          NavigationDestination(
              icon: Icon(Icons.insights_outlined),
              selectedIcon: Icon(Icons.insights_rounded),
              label: 'Analytics'),
          NavigationDestination(
              icon: Icon(Icons.settings_outlined),
              selectedIcon: Icon(Icons.settings_rounded),
              label: 'Settings'),
        ],
      ),
    );
  }

  Widget _buildHomeTab(
    BuildContext context,
    AsyncValue<SummaryResponse?> summaryAsync,
    AsyncValue<BudgetLimitResponse?> budgetAsync,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    return RefreshIndicator(
      onRefresh: () => _refreshAll(ref.read(authControllerProvider.notifier)),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          _Card(
            child: summaryAsync.when(
              data: (summary) {
                if (summary == null) {
                  return const Text('No spending data yet.');
                }
                final budget = budgetAsync.valueOrNull?.monthlyBudget;
                final progress = budget == null || budget <= 0
                    ? 0.0
                    : (summary.totalSpent / budget).clamp(0.0, 1.0);
                final progressLabel = budget == null
                    ? 'Set a monthly budget in Settings to track progress.'
                    : '${(progress * 100).round()}% of ${summary.currency} ${budget.toStringAsFixed(0)}';

                return Row(
                  children: [
                    SizedBox(
                      width: 94,
                      height: 94,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: progress,
                            strokeWidth: 10,
                            backgroundColor: const Color(0xFFE4EBE7),
                            color: const Color(0xFF0D8A43),
                          ),
                          Text('${(progress * 100).round()}%'),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'This Month Spending',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _formatAmount(summary.totalSpent, summary.currency),
                            style: Theme.of(context)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: 6),
                          Text(progressLabel,
                              style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Text('$error',
                  style: const TextStyle(color: Colors.redAccent)),
            ),
          ),
          const SizedBox(height: 12),
          _Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Quick Categories',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                summaryAsync.when(
                  data: (summary) {
                    final categories = summary?.categories.take(6).toList() ?? [];
                    if (categories.isEmpty) {
                      return const Text('No categories yet.');
                    }
                    return SizedBox(
                      height: 92,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemBuilder: (_, index) {
                          final item = categories[index];
                          return Container(
                            width: 140,
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF7FAF8),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFDDE8E1)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(_iconForCategory(item.category),
                                    color: const Color(0xFF0D8A43), size: 20),
                                const SizedBox(height: 8),
                                Text(item.category,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style:
                                        Theme.of(context).textTheme.bodySmall),
                                const Spacer(),
                                Text(
                                  _formatAmount(item.amount, summary!.currency),
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodyMedium
                                      ?.copyWith(fontWeight: FontWeight.w700),
                                ),
                              ],
                            ),
                          );
                        },
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemCount: categories.length,
                      ),
                    );
                  },
                  loading: () => const LinearProgressIndicator(),
                  error: (error, _) => Text('$error'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Recent Transactions',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 10),
                transactionsAsync.when(
                  data: (payload) {
                    final items = payload?.transactions.take(5).toList() ?? [];
                    if (items.isEmpty) {
                      return const Text('No transactions available.');
                    }
                    return Column(
                      children: items
                          .map(
                            (tx) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: CircleAvatar(
                                backgroundColor: const Color(0xFFE5F2EA),
                                child: Icon(_iconForCategory(tx.category),
                                    color: const Color(0xFF0D8A43)),
                              ),
                              title: Text(tx.category),
                              subtitle: Text(
                                  tx.recipient ??
                                      (tx.occurredAt
                                          ?.toIso8601String()
                                          .split('T')
                                          .first ??
                                      'Unknown date'),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis),
                              trailing: Text(
                                _formatAmount(tx.amount, tx.currency),
                                style: TextStyle(
                                  color: tx.direction == 'expense'
                                      ? Colors.red.shade700
                                      : const Color(0xFF0D8A43),
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    );
                  },
                  loading: () => const LinearProgressIndicator(),
                  error: (error, _) => Text('$error'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTransactionsTab(
    BuildContext context,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    return transactionsAsync.when(
      data: (payload) {
        final items = payload?.transactions ?? [];
        if (items.isEmpty) {
          return const Center(child: Text('No transaction history yet.'));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          itemBuilder: (_, index) {
            final tx = items[index];
            return _Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: const Color(0xFFE5F2EA),
                    child: Icon(_iconForCategory(tx.category),
                        color: const Color(0xFF0D8A43)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(tx.category,
                            style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text(tx.recipient ?? 'M-PESA transaction',
                            style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ),
                  Text(
                    _formatAmount(tx.amount, tx.currency),
                    style: TextStyle(
                      color: tx.direction == 'expense'
                          ? Colors.red.shade700
                          : const Color(0xFF0D8A43),
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(child: Text('$error')),
    );
  }

  Widget _buildAnalyticsTab(
    BuildContext context,
    AsyncValue<SummaryResponse?> summaryAsync,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Spending Trend', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              transactionsAsync.when(
                data: (payload) {
                  final points = _trendPoints(payload?.transactions ?? []);
                  if (points.length < 2) {
                    return const Text('Need more data for trend chart.');
                  }
                  return SizedBox(
                    height: 170,
                    child: CustomPaint(
                      painter: _TrendPainter(points),
                      child: const SizedBox.expand(),
                    ),
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => Text('$error'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Top Categories', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              summaryAsync.when(
                data: (summary) {
                  final categories = summary?.categories.take(8).toList() ?? [];
                  if (categories.isEmpty) {
                    return const Text('No category data yet.');
                  }
                  return Column(
                    children: categories
                        .map(
                          (item) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 6),
                            child: Row(
                              children: [
                                Icon(_iconForCategory(item.category),
                                    color: const Color(0xFF0D8A43)),
                                const SizedBox(width: 10),
                                Expanded(child: Text(item.category)),
                                Text(_formatAmount(item.amount, summary!.currency),
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700)),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => Text('$error'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSettingsTab(
    BuildContext context,
    AuthState authState,
    AuthController controller,
    AsyncValue<BudgetLimitResponse?> budgetAsync,
  ) {
    if (_budgetController.text.isEmpty && budgetAsync.valueOrNull != null) {
      _budgetController.text = budgetAsync.valueOrNull!.monthlyBudget.toStringAsFixed(0);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Profile', style: Theme.of(context).textTheme.titleMedium),
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
              Text('API Base URL', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              TextField(
                controller: _apiBaseController,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(hintText: 'http://10.0.2.2:8000'),
              ),
              const SizedBox(height: 10),
              FilledButton.tonal(
                onPressed: () async {
                  await controller.updateApiBase(_apiBaseController.text);
                  ref.invalidate(summaryProvider);
                  ref.invalidate(transactionsProvider);
                  ref.invalidate(budgetProvider);
                },
                child: const Text('Save API Base'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _Card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Budget Goal', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              TextField(
                controller: _budgetController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    const InputDecoration(labelText: 'Monthly budget (KES)'),
              ),
              const SizedBox(height: 10),
              FilledButton.tonal(
                onPressed: () async {
                  final amount = double.tryParse(_budgetController.text.trim());
                  final token = authState.token;
                  if (amount == null || token == null) return;
                  await ref.read(apiClientProvider).upsertBudgetLimit(
                        apiBase: authState.apiBase,
                        token: token,
                        monthlyBudget: amount,
                      );
                  ref.invalidate(budgetProvider);
                },
                child: const Text('Save Budget Goal'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _Card(
          child: Column(
            children: [
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: false,
                onChanged: null,
                title: const Text('Dark mode (coming soon)'),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: false,
                onChanged: null,
                title: const Text('Biometric login (coming soon)'),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.notifications_active_outlined),
                title: const Text('Budget alerts'),
                subtitle: const Text('Get notified near your monthly limit.'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: null,
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        FilledButton.tonal(
          onPressed: () => controller.logout(),
          child: const Text('Sign Out'),
        ),
      ],
    );
  }

  Future<void> _refreshAll(AuthController controller) async {
    await controller.refreshUser();
    ref.invalidate(summaryProvider);
    ref.invalidate(transactionsProvider);
    ref.invalidate(budgetProvider);
  }

  String _formatAmount(double value, String currency) {
    return '$currency ${value.toStringAsFixed(value.truncateToDouble() == value ? 0 : 2)}';
  }

  List<double> _trendPoints(List<TransactionItem> transactions) {
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, 1);
    final dailyTotals = <int, double>{};

    for (final tx in transactions) {
      if (tx.direction != 'expense' || tx.occurredAt == null) continue;
      if (tx.occurredAt!.isBefore(start)) continue;
      dailyTotals.update(tx.occurredAt!.day, (value) => value + tx.amount,
          ifAbsent: () => tx.amount);
    }

    final daysElapsed = now.day;
    return List<double>.generate(
      daysElapsed,
      (index) => dailyTotals[index + 1] ?? 0,
      growable: false,
    );
  }

  IconData _iconForCategory(String category) {
    final normalized = category.toLowerCase();
    if (normalized.contains('food') || normalized.contains('restaurant')) {
      return Icons.restaurant_rounded;
    }
    if (normalized.contains('transport')) return Icons.directions_bus_rounded;
    if (normalized.contains('utility')) return Icons.lightbulb_rounded;
    if (normalized.contains('airtime')) return Icons.phone_android_rounded;
    if (normalized.contains('shopping')) return Icons.shopping_bag_rounded;
    if (normalized.contains('rent')) return Icons.home_work_rounded;
    return Icons.payments_rounded;
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.margin});

  final Widget child;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFDDE5DF)),
      ),
      child: Padding(padding: const EdgeInsets.all(16), child: child),
    );
  }
}

class _TrendPainter extends CustomPainter {
  _TrendPainter(this.values);

  final List<double> values;

  @override
  void paint(Canvas canvas, Size size) {
    final axisPaint = Paint()
      ..color = const Color(0xFFCAD6CF)
      ..strokeWidth = 1;
    final linePaint = Paint()
      ..color = const Color(0xFF0D8A43)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(
      Offset(0, size.height - 2),
      Offset(size.width, size.height - 2),
      axisPaint,
    );

    final maxValue = values.reduce(math.max);
    if (maxValue <= 0) return;

    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final double x = values.length == 1 ? 0 : (i / (values.length - 1)) * size.width;
      final double y = size.height - ((values[i] / maxValue) * (size.height - 16)) - 2;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    canvas.drawPath(path, linePaint);
  }

  @override
  bool shouldRepaint(covariant _TrendPainter oldDelegate) {
    return oldDelegate.values != values;
  }
}
