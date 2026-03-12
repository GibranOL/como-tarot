import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';

class HoroscopeModel {
  const HoroscopeModel({
    required this.zodiacSign,
    required this.horoscope,
    required this.date,
    this.weeklyHoroscope,
  });

  factory HoroscopeModel.fromJson(Map<String, dynamic> json) => HoroscopeModel(
        zodiacSign: json['zodiac_sign'] as String? ?? '',
        horoscope: json['horoscope'] as String? ?? '',
        date: json['date'] as String? ?? '',
        weeklyHoroscope: json['weekly_horoscope'] as String?,
      );

  final String zodiacSign;
  final String horoscope;
  final String date;
  final String? weeklyHoroscope;
}

final horoscopeProvider = FutureProvider<HoroscopeModel?>((ref) async {
  try {
    final api = ref.read(apiClientProvider);
    final response = await api.dio.get('/api/horoscope/daily');
    return HoroscopeModel.fromJson(response.data as Map<String, dynamic>);
  } catch (_) {
    return null;
  }
});
