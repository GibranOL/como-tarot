import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class CompatibilityResult {
  const CompatibilityResult({
    required this.partnerZodiac,
    required this.compatibilityScore,
    required this.aiInterpretation,
  });

  factory CompatibilityResult.fromJson(Map<String, dynamic> json) =>
      CompatibilityResult(
        partnerZodiac: json['partner_zodiac'] as String? ?? '',
        compatibilityScore: json['compatibility_score'] as int? ?? 0,
        aiInterpretation: json['ai_interpretation'] as String? ?? '',
      );

  final String partnerZodiac;
  final int compatibilityScore;
  final String aiInterpretation;
}

final compatibilityNotifierProvider =
    AsyncNotifierProvider<CompatibilityNotifier, CompatibilityResult?>(
  CompatibilityNotifier.new,
);

class CompatibilityNotifier extends AsyncNotifier<CompatibilityResult?> {
  @override
  Future<CompatibilityResult?> build() async => null;

  Future<void> check(String partnerZodiac) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final api = ref.read(apiClientProvider);
      final response = await api.dio.post(
        '/api/compatibility/check',
        data: {'partner_zodiac': partnerZodiac},
      );
      return CompatibilityResult.fromJson(
          response.data as Map<String, dynamic>);
    });
  }
}
