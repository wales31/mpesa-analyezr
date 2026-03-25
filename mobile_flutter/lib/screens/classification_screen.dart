import 'package:flutter/material.dart';

import '../app.dart';

enum TxCategory {
  transport('Transport', Icons.directions_car_rounded),
  groceries('Groceries', Icons.shopping_basket_rounded),
  food('Food', Icons.restaurant_rounded),
  rent('Rent', Icons.home_rounded),
  bills('Bills', Icons.receipt_long_rounded),
  personal('Personal', Icons.person_rounded),
  other('Other', Icons.category_rounded);

  const TxCategory(this.label, this.icon);

  final String label;
  final IconData icon;
}

class TxItem {
  const TxItem({
    required this.id,
    required this.recipientRaw,
    required this.amount,
    required this.message,
    required this.timestamp,
  });

  final String id;
  final String recipientRaw;
  final double amount;
  final String message;
  final DateTime timestamp;
}

class TxGroup {
  const TxGroup({
    required this.patternKey,
    required this.transactions,
  });

  final String patternKey;
  final List<TxItem> transactions;

  String get recipientRaw => transactions.first.recipientRaw;
}

class ClassificationScreen extends StatefulWidget {
  const ClassificationScreen({super.key});

  @override
  State<ClassificationScreen> createState() => _ClassificationScreenState();
}

class _ClassificationScreenState extends State<ClassificationScreen> {
  late List<TxGroup> _groups;
  final Map<String, String> _aliases = {
    'BOLT*TRIP KENYA': 'Bolt Driver',
    'MAMA NALIACA': 'Mama Mboga',
  };
  final Map<String, Map<TxCategory, int>> _categoryFrequency = {};

  @override
  void initState() {
    super.initState();
    _groups = _groupTransactions(_seedTransactions());
  }

  List<TxItem> _seedTransactions() {
    return [
      TxItem(
        id: 'tx-1001',
        recipientRaw: 'BOLT*TRIP KENYA',
        amount: 460,
        message: 'Send money to BOLT*TRIP KENYA',
        timestamp: DateTime(2026, 3, 22, 18, 31),
      ),
      TxItem(
        id: 'tx-1002',
        recipientRaw: 'BOLT*TRIP KENYA',
        amount: 370,
        message: 'Send money to BOLT*TRIP KENYA',
        timestamp: DateTime(2026, 3, 23, 8, 10),
      ),
      TxItem(
        id: 'tx-1003',
        recipientRaw: 'MAMA NALIACA',
        amount: 950,
        message: 'Send money to MAMA NALIACA shopping',
        timestamp: DateTime(2026, 3, 23, 20, 20),
      ),
      TxItem(
        id: 'tx-1004',
        recipientRaw: 'JOHN KIPTOO',
        amount: 18500,
        message: 'Send money rent payment March',
        timestamp: DateTime(2026, 3, 21, 11, 45),
      ),
      TxItem(
        id: 'tx-1005',
        recipientRaw: 'KPLC PREPAID',
        amount: 2100,
        message: 'Send money power tokens',
        timestamp: DateTime(2026, 3, 24, 9, 2),
      ),
      TxItem(
        id: 'tx-1006',
        recipientRaw: 'MAMA NALIACA',
        amount: 870,
        message: 'Send money market groceries',
        timestamp: DateTime(2026, 3, 24, 17, 40),
      ),
    ];
  }

  List<TxGroup> _groupTransactions(List<TxItem> transactions) {
    final grouped = <String, List<TxItem>>{};
    for (final tx in transactions) {
      final key = _patternKey(tx);
      grouped.putIfAbsent(key, () => []).add(tx);
    }

    return grouped.entries
        .map((entry) => TxGroup(patternKey: entry.key, transactions: entry.value))
        .toList()
      ..sort(
        (a, b) => b.transactions.first.timestamp.compareTo(a.transactions.first.timestamp),
      );
  }

  String _patternKey(TxItem tx) {
    final normalizedRecipient = tx.recipientRaw.toUpperCase().replaceAll(RegExp(r'\s+'), ' ').trim();
    final normalizedMessage = tx.message.toLowerCase().replaceAll(RegExp(r'[^a-z ]'), ' ');
    final condensed = normalizedMessage.replaceAll(RegExp(r'\s+'), ' ').trim();

    if (condensed.contains('rent')) {
      return '$normalizedRecipient|rent';
    }
    if (condensed.contains('bolt') || condensed.contains('uber')) {
      return '$normalizedRecipient|transport';
    }
    return normalizedRecipient;
  }

  TxCategory _suggestCategory(TxGroup group) {
    final memory = _categoryFrequency[group.recipientRaw];
    if (memory != null && memory.isNotEmpty) {
      final sorted = memory.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
      final winner = sorted.first;
      if (winner.value >= 2) {
        return winner.key;
      }
    }

    final message = group.transactions.first.message.toLowerCase();
    final recipient = group.recipientRaw.toLowerCase();
    final amount = group.transactions.first.amount;

    if (message.contains('rent') || amount >= 15000) {
      return TxCategory.rent;
    }
    if (recipient.contains('kplc') || message.contains('token') || message.contains('power')) {
      return TxCategory.bills;
    }
    if (recipient.contains('bolt') || recipient.contains('uber') || recipient.contains('trip')) {
      return TxCategory.transport;
    }
    if (message.contains('market') || message.contains('grocer') || recipient.contains('mama')) {
      return TxCategory.groceries;
    }
    if (message.contains('lunch') || message.contains('restaurant')) {
      return TxCategory.food;
    }
    return TxCategory.personal;
  }

  void _recordLearning(String recipient, TxCategory category) {
    final memory = _categoryFrequency.putIfAbsent(recipient, () => {});
    memory.update(category, (value) => value + 1, ifAbsent: () => 1);
  }

  void _classifySingle(TxGroup group, TxCategory category) {
    setState(() {
      _groups.remove(group);
      _recordLearning(group.recipientRaw, category);
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Classified ${_displayName(group.recipientRaw)} as ${category.label}.'),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _classifyAll(TxGroup group, TxCategory category) {
    setState(() {
      _groups.removeWhere((item) => item.patternKey == group.patternKey || item.recipientRaw == group.recipientRaw);
      _recordLearning(group.recipientRaw, category);
      _recordLearning(group.recipientRaw, category);
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Marked all ${_displayName(group.recipientRaw)} transfers as ${category.label}.'),
      ),
    );
  }

  void _skip(TxGroup group) {
    setState(() {
      _groups.remove(group);
    });
  }

  String _displayName(String recipientRaw) => _aliases[recipientRaw] ?? recipientRaw;

  Future<void> _renameAlias(String recipientRaw) async {
    final aliases = [
      'Bolt Driver',
      'Mama Mboga',
      'Landlord',
      'Utility Provider',
      'Family',
      'Friend',
      'School',
    ];

    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Text(
                  'Rename $recipientRaw',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(width: double.infinity),
                for (final alias in aliases)
                  ActionChip(
                    label: Text(alias),
                    onPressed: () => Navigator.of(context).pop(alias),
                  ),
              ],
            ),
          ),
        );
      },
    );

    if (selected == null) {
      return;
    }

    setState(() {
      _aliases[recipientRaw] = selected;
    });
  }

  @override
  Widget build(BuildContext context) {
    final pendingCount = _groups.fold<int>(0, (sum, g) => sum + g.transactions.length);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Classify Send-Money'),
        backgroundColor: Colors.transparent,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
              child: Row(
                children: [
                  Text(
                    '$pendingCount pending',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const Spacer(),
                  const Icon(Icons.swipe_left_rounded, color: AppColors.textSecondary),
                  const SizedBox(width: 6),
                  Text(
                    'Swipe to accept suggestion',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _groups.isEmpty
                  ? Center(
                      child: Text(
                        'All transactions classified 🎉',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                      itemCount: _groups.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final group = _groups[index];
                        final suggestion = _suggestCategory(group);
                        final label = _displayName(group.recipientRaw);

                        return Dismissible(
                          key: ValueKey(group.patternKey),
                          direction: DismissDirection.endToStart,
                          background: Container(
                            decoration: BoxDecoration(
                              color: AppColors.primary,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            alignment: Alignment.centerRight,
                            padding: const EdgeInsets.symmetric(horizontal: 20),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                const Icon(Icons.check_circle_rounded, color: Colors.white),
                                const SizedBox(width: 8),
                                Text(
                                  'Confirm ${suggestion.label}',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          onDismissed: (_) => _classifySingle(group, suggestion),
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              label,
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .titleMedium
                                                  ?.copyWith(fontWeight: FontWeight.w700),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              '${group.transactions.length} similar transfer(s)',
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .bodySmall
                                                  ?.copyWith(color: AppColors.textSecondary),
                                            ),
                                          ],
                                        ),
                                      ),
                                      IconButton(
                                        onPressed: () => _renameAlias(group.recipientRaw),
                                        icon: const Icon(Icons.edit_outlined),
                                        tooltip: 'Rename recipient',
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    'KSh ${group.transactions.first.amount.toStringAsFixed(0)} • ${group.transactions.first.message}',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(color: AppColors.textSecondary),
                                  ),
                                  const SizedBox(height: 12),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 8,
                                    children: [
                                      for (final category in TxCategory.values)
                                        ChoiceChip(
                                          avatar: Icon(
                                            category.icon,
                                            size: 16,
                                            color: suggestion == category ? Colors.white : AppColors.textSecondary,
                                          ),
                                          label: Text(category.label),
                                          selected: suggestion == category,
                                          selectedColor: AppColors.primary,
                                          labelStyle: TextStyle(
                                            color: suggestion == category ? Colors.white : AppColors.textPrimary,
                                            fontWeight:
                                                suggestion == category ? FontWeight.w700 : FontWeight.w500,
                                          ),
                                          onSelected: (_) => _classifySingle(group, category),
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 12),
                                  Row(
                                    children: [
                                      TextButton.icon(
                                        onPressed: () => _classifyAll(group, suggestion),
                                        icon: const Icon(Icons.done_all_rounded),
                                        label: Text('Mark all as ${suggestion.label}'),
                                      ),
                                      const Spacer(),
                                      TextButton(
                                        onPressed: () => _skip(group),
                                        child: const Text('Skip'),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
