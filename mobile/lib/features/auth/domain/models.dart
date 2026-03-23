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
  const SummaryResponse({required this.currency, required this.totalSpent, required this.categories});

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
