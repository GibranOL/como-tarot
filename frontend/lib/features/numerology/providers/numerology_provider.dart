import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class NumerologyProfile {
  const NumerologyProfile({
    required this.lifeNumber,
    required this.personalYear,
    required this.personalMonth,
    required this.lifeNumberMeaning,
    required this.personalYearMeaning,
  });

  factory NumerologyProfile.fromJson(Map<String, dynamic> json) =>
      NumerologyProfile(
        lifeNumber: json['life_number'] as int? ?? 0,
        personalYear: json['personal_year'] as int? ?? 0,
        personalMonth: json['personal_month'] as int? ?? 0,
        lifeNumberMeaning: json['life_number_meaning'] as String? ?? '',
        personalYearMeaning: json['personal_year_meaning'] as String? ?? '',
      );

  final int lifeNumber;
  final int personalYear;
  final int personalMonth;
  final String lifeNumberMeaning;
  final String personalYearMeaning;
}

final numerologyProvider = FutureProvider<NumerologyProfile?>((ref) async {
  try {
    final api = ref.read(apiClientProvider);
    final response = await api.dio.get('/api/numerology/profile');
    return NumerologyProfile.fromJson(response.data as Map<String, dynamic>);
  } catch (_) {
    return null;
  }
});
