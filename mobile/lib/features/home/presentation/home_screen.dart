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
  bool _darkModeEnabled = false;
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
      _buildHomeTab(context, authState, summaryAsync, budgetAsync, transactionsAsync),
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
      body: SafeArea(child: AnimatedSwitcher(duration: const Duration(milliseconds: 250), child: pages[_currentTab])),
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
    AuthState authState,
    AsyncValue<SummaryResponse?> summaryAsync,
    AsyncValue<BudgetLimitResponse?> budgetAsync,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    final budget = budgetAsync.valueOrNull?.monthlyBudget;
    final summary = summaryAsync.valueOrNull;
    final alertVisible = summary != null && budget != null && budget > 0
        ? (summary.totalSpent / budget) >= 0.9
        : false;

    return RefreshIndicator(
      onRefresh: () => _refreshAll(ref.read(authControllerProvider.notifier)),
      child: ListView(
        key: const ValueKey('home-tab'),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          Text('Hello, ${authState.user?.username ?? 'User'}',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(color: const Color(0xFF5D6F65))),
          Text(
            'Your M-PESA Dashboard',
            style: Theme.of(context)
                .textTheme
                .headlineSmall
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          if (alertVisible) ...[
            const SizedBox(height: 12),
            _Card(
              child: Row(
                children: [
                  const Icon(Icons.notifications_active_rounded,
                      color: Color(0xFF0D8A43)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Budget alert: you are close to your monthly limit.',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 12),
          _buildMonthlySummaryCard(context, summaryAsync, budgetAsync, authState),
          const SizedBox(height: 12),
          _buildTrendCard(context, transactionsAsync),
          const SizedBox(height: 12),
          _buildTopCategoriesCard(context, summaryAsync, budgetAsync),
          const SizedBox(height: 12),
          _buildRecentTransactionsCard(context, transactionsAsync),
        ],
      ),
    );
  }

  Widget _buildMonthlySummaryCard(
    BuildContext context,
    AsyncValue<SummaryResponse?> summaryAsync,
    AsyncValue<BudgetLimitResponse?> budgetAsync,
    AuthState authState,
  ) {
    return _Card(
      gradient: const LinearGradient(
        colors: [Color(0xFF0D8A43), Color(0xFF1AA75A)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      child: summaryAsync.when(
        data: (summary) {
          final budget = budgetAsync.valueOrNull?.monthlyBudget;
          final spent = summary?.totalSpent ?? 0;
          final currency = summary?.currency ?? 'KES';
          final progress = budget == null || budget <= 0
              ? 0.0
              : (spent / budget).clamp(0.0, 1.0);

          return Row(
            children: [
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: progress),
                duration: const Duration(milliseconds: 700),
                builder: (_, animatedProgress, __) {
                  return SizedBox(
                    width: 96,
                    height: 96,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        CircularProgressIndicator(
                          value: animatedProgress,
                          strokeWidth: 9,
                          backgroundColor: Colors.white24,
                          color: Colors.white,
                        ),
                        Text(
                          '${(animatedProgress * 100).round()}%',
                          style: const TextStyle(
                              color: Colors.white, fontWeight: FontWeight.w700),
                        ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('This Month\'s Spending',
                        style: TextStyle(color: Colors.white70)),
                    const SizedBox(height: 4),
                    Text(
                      _formatAmount(spent, currency),
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Colors.white, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      budget == null
                          ? 'Set monthly budget to unlock tracking'
                          : 'of ${_formatAmount(budget, currency)} budget',
                      style: const TextStyle(color: Colors.white70),
                    ),
                    const SizedBox(height: 10),
                    FilledButton.tonal(
                      style: FilledButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF0D8A43),
                      ),
                      onPressed: () => _showBudgetEditor(context, authState, budget),
                      child: Text(budget == null ? 'Set Budget' : 'Update Budget'),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: Colors.white)),
        error: (error, _) => Text(
          '$error',
          style: const TextStyle(color: Colors.white),
        ),
      ),
    );
  }

  Widget _buildTrendCard(
    BuildContext context,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Spending Trend', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          transactionsAsync.when(
            data: (payload) {
              final trend = _weeklyTrend(payload?.transactions ?? []);
              if (trend.values.every((value) => value == 0)) {
                return const Text('Not enough trend data yet.');
              }
              return Column(
                children: [
                  SizedBox(
                    height: 170,
                    child: CustomPaint(
                      painter: _TrendPainter(trend.values),
                      child: const SizedBox.expand(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: trend.labels
                        .map((day) => Text(day,
                            style: Theme.of(context).textTheme.bodySmall))
                        .toList(),
                  ),
                ],
              );
            },
            loading: () => const LinearProgressIndicator(),
            error: (error, _) => Text('$error'),
          ),
        ],
      ),
    );
  }

  Widget _buildTopCategoriesCard(
    BuildContext context,
    AsyncValue<SummaryResponse?> summaryAsync,
    AsyncValue<BudgetLimitResponse?> budgetAsync,
  ) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Top Spending Categories',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          summaryAsync.when(
            data: (summary) {
              final categories = summary?.categories.take(4).toList() ?? [];
              if (categories.isEmpty) {
                return const Text('No categories yet.');
              }
              final total = summary?.totalSpent ?? 0;
              final budget = budgetAsync.valueOrNull?.monthlyBudget ?? 0;

              return GridView.builder(
                itemCount: categories.length,
                physics: const NeverScrollableScrollPhysics(),
                shrinkWrap: true,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  childAspectRatio: 1.5,
                ),
                itemBuilder: (_, index) {
                  final item = categories[index];
                  final share = total <= 0 ? 0.0 : (item.amount / total).clamp(0.0, 1.0);
                  final budgetShare = budget <= 0 ? 0.0 : (item.amount / budget).clamp(0.0, 1.0);
                  return Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF7FAF8),
                      borderRadius: BorderRadius.circular(16),
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
                            style: Theme.of(context).textTheme.bodySmall),
                        const Spacer(),
                        Text(
                          _formatAmount(item.amount, summary?.currency ?? 'KES'),
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 6),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(99),
                          child: LinearProgressIndicator(
                            value: budget > 0 ? budgetShare : share,
                            minHeight: 6,
                            backgroundColor: const Color(0xFFDDE8E1),
                            color: const Color(0xFF0D8A43),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              );
            },
            loading: () => const LinearProgressIndicator(),
            error: (error, _) => Text('$error'),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentTransactionsCard(
    BuildContext context,
    AsyncValue<TransactionsResponse?> transactionsAsync,
  ) {
    return _Card(
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
                        onTap: () => _showTransactionDetail(context, tx),
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFFE5F2EA),
                          child: Icon(_iconForCategory(tx.category),
                              color: const Color(0xFF0D8A43)),
                        ),
                        title: Text(tx.recipient ?? tx.category),
                        subtitle: Text(
                          tx.occurredAt?.toIso8601String().split('T').first ??
                              'Unknown date',
                        ),
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
          key: const ValueKey('transactions-tab'),
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
      key: const ValueKey('analytics-tab'),
      padding: const EdgeInsets.all(16),
      children: [
        _buildTrendCard(context, transactionsAsync),
        const SizedBox(height: 12),
        _buildTopCategoriesCard(context, summaryAsync, ref.watch(budgetProvider)),
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
      key: const ValueKey('settings-tab'),
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
            children: [
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _darkModeEnabled,
                onChanged: (value) => setState(() => _darkModeEnabled = value),
                title: const Text('Dark mode preview'),
                subtitle: const Text('Global theme support can be enabled next.'),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.notifications_active_outlined),
                title: const Text('Budget alerts'),
                subtitle: const Text('Get notified near your monthly limit.'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () {},
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

  Future<void> _showBudgetEditor(
    BuildContext context,
    AuthState authState,
    double? currentBudget,
  ) async {
    _budgetController.text = currentBudget?.toStringAsFixed(0) ?? '';

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 8,
            bottom: MediaQuery.of(context).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Set Monthly Budget',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              TextField(
                controller: _budgetController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Budget amount (KES)'),
              ),
              const SizedBox(height: 12),
              FilledButton(
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
                  if (mounted) Navigator.of(context).pop();
                },
                child: const Text('Save Budget'),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showTransactionDetail(BuildContext context, TransactionItem tx) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(tx.recipient ?? tx.category,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              Text('Category: ${tx.category}'),
              Text('Amount: ${_formatAmount(tx.amount, tx.currency)}'),
              Text('Direction: ${tx.direction}'),
              Text(
                  'Date: ${tx.occurredAt?.toIso8601String().split('T').first ?? 'Unknown'}'),
            ],
          ),
        );
      },
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

  ({List<String> labels, List<double> values}) _weeklyTrend(
      List<TransactionItem> transactions) {
    final now = DateTime.now();
    final days = List<DateTime>.generate(
      7,
      (index) => DateTime(now.year, now.month, now.day).subtract(Duration(days: 6 - index)),
    );
    final totals = <String, double>{};
    for (final day in days) {
      totals['${day.year}-${day.month}-${day.day}'] = 0;
    }

    for (final tx in transactions) {
      final occurred = tx.occurredAt;
      if (tx.direction != 'expense' || occurred == null) continue;
      final key = '${occurred.year}-${occurred.month}-${occurred.day}';
      if (!totals.containsKey(key)) continue;
      totals[key] = (totals[key] ?? 0) + tx.amount;
    }

    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final mappedLabels = days.map((day) => labels[(day.weekday - 1) % 7]).toList();
    final values = days
        .map((day) => totals['${day.year}-${day.month}-${day.day}'] ?? 0)
        .toList();

    return (labels: mappedLabels, values: values);
  }

  IconData _iconForCategory(String category) {
    final normalized = category.toLowerCase();
    if (normalized.contains('food') || normalized.contains('restaurant')) {
      return Icons.restaurant_rounded;
    }
    if (normalized.contains('transport')) return Icons.directions_bus_rounded;
    if (normalized.contains('utility') || normalized.contains('bill')) {
      return Icons.home_rounded;
    }
    if (normalized.contains('airtime')) return Icons.phone_android_rounded;
    if (normalized.contains('shopping')) return Icons.shopping_bag_rounded;
    if (normalized.contains('rent')) return Icons.home_work_rounded;
    return Icons.payments_rounded;
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.margin, this.gradient});

  final Widget child;
  final EdgeInsetsGeometry? margin;
  final Gradient? gradient;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: gradient == null ? Colors.white : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFDDE5DF)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
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
    final areaPaint = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0x551AA75A), Color(0x101AA75A)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;

    canvas.drawLine(
      Offset(0, size.height - 2),
      Offset(size.width, size.height - 2),
      axisPaint,
    );

    final maxValue = values.reduce(math.max);
    if (maxValue <= 0) return;

    final linePath = Path();
    final areaPath = Path();
    for (var i = 0; i < values.length; i++) {
      final x = values.length == 1 ? 0 : (i / (values.length - 1)) * size.width;
      final y = size.height - ((values[i] / maxValue) * (size.height - 16)) - 2;
      if (i == 0) {
        linePath.moveTo(x, y);
        areaPath
          ..moveTo(x, size.height - 2)
          ..lineTo(x, y);
      } else {
        linePath.lineTo(x, y);
        areaPath.lineTo(x, y);
      }
    }

    areaPath
      ..lineTo(size.width, size.height - 2)
      ..close();

    canvas.drawPath(areaPath, areaPaint);
    canvas.drawPath(linePath, linePaint);
  }

  @override
  bool shouldRepaint(covariant _TrendPainter oldDelegate) {
    return oldDelegate.values != values;
  }
}
