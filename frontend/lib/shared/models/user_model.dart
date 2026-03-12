class UserModel {
  const UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    required this.zodiacSign,
    required this.lifeNumber,
    required this.isPremium,
    required this.preferredLanguage,
    this.birthDate,
    this.authProvider,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as String,
        email: json['email'] as String,
        fullName: json['full_name'] as String,
        zodiacSign: json['zodiac_sign'] as String? ?? '',
        lifeNumber: json['life_number'] as int? ?? 0,
        isPremium: json['is_premium'] as bool? ?? false,
        preferredLanguage: json['preferred_language'] as String? ?? 'en',
        birthDate: json['birth_date'] as String?,
        authProvider: json['auth_provider'] as String?,
      );

  final String id;
  final String email;
  final String fullName;
  final String zodiacSign;
  final int lifeNumber;
  final bool isPremium;
  final String preferredLanguage;
  final String? birthDate;
  final String? authProvider;

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'full_name': fullName,
        'zodiac_sign': zodiacSign,
        'life_number': lifeNumber,
        'is_premium': isPremium,
        'preferred_language': preferredLanguage,
        'birth_date': birthDate,
        'auth_provider': authProvider,
      };
}
