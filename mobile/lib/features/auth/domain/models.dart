class AuthUser {
  const AuthUser({required this.id, required this.email, required this.username});

  final String id;
  final String email;
  final String username;

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        id: json['id'] as String,
        email: json['email'] as String,
        username: json['username'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'username': username,
      };
}

class AuthResponse {
  const AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.expiresAt,
    required this.user,
  });

  final String accessToken;
  final String tokenType;
  final DateTime expiresAt;
  final AuthUser user;

  factory AuthResponse.fromJson(Map<String, dynamic> json) => AuthResponse(
        accessToken: json['access_token'] as String,
        tokenType: json['token_type'] as String? ?? 'bearer',
        expiresAt: DateTime.parse(json['expires_at'] as String),
        user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
      );
}

class SummaryCategory {
  const SummaryCategory({required this.category, required this.amount});

  final String category;
  final double amount;

  factory SummaryCategory.fromJson(Map<String, dynamic> json) => SummaryCategory(
        category: json['category'] as String,
        amount: (json['amount'] as num).toDouble(),
      );
}

class SummaryResponse {
  const SummaryResponse({
    required this.currency,
    required this.totalSpent,
    required this.categories,
  });

  final String currency;
  final double totalSpent;
  final List<SummaryCategory> categories;

  factory SummaryResponse.fromJson(Map<String, dynamic> json) => SummaryResponse(
        currency: json['currency'] as String,
        totalSpent: (json['total_spent'] as num).toDouble(),
        categories: ((json['categories'] as List<dynamic>? ?? const [])
            .map((item) => SummaryCategory.fromJson(item as Map<String, dynamic>))
            .toList()),
      );
}

class TransactionItem {
  const TransactionItem({
    required this.id,
    required this.amount,
    required this.currency,
    required this.category,
    required this.direction,
    required this.recipient,
    required this.occurredAt,
  });

  final int id;
  final double amount;
  final String currency;
  final String category;
  final String direction;
  final String? recipient;
  final DateTime? occurredAt;

  factory TransactionItem.fromJson(Map<String, dynamic> json) => TransactionItem(
        id: json['id'] as int,
        amount: (json['amount'] as num).toDouble(),
        currency: json['currency'] as String? ?? 'KES',
        category: json['category'] as String? ?? 'other',
        direction: json['direction'] as String? ?? 'expense',
        recipient: json['recipient'] as String?,
        occurredAt: json['occurred_at'] == null
            ? null
            : DateTime.tryParse(json['occurred_at'] as String),
      );
}

class TransactionsResponse {
  const TransactionsResponse({required this.count, required this.transactions});

  final int count;
  final List<TransactionItem> transactions;

  factory TransactionsResponse.fromJson(Map<String, dynamic> json) {
    final items = (json['transactions'] as List<dynamic>? ?? const [])
        .map((item) => TransactionItem.fromJson(item as Map<String, dynamic>))
        .toList();
    return TransactionsResponse(
      count: json['count'] as int? ?? items.length,
      transactions: items,
    );
  }
}

class BudgetLimitResponse {
  const BudgetLimitResponse({required this.monthlyBudget, required this.currency});

  final double monthlyBudget;
  final String currency;

  factory BudgetLimitResponse.fromJson(Map<String, dynamic> json) =>
      BudgetLimitResponse(
        monthlyBudget: (json['monthly_budget'] as num).toDouble(),
        currency: json['currency'] as String? ?? 'KES',
      );
}
