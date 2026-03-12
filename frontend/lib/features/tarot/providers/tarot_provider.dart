import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/models/tarot_reading_model.dart';

final tarotReadingProvider =
    AsyncNotifierProvider<TarotReadingNotifier, TarotReadingModel?>(
  TarotReadingNotifier.new,
);

class TarotReadingNotifier extends AsyncNotifier<TarotReadingModel?> {
  @override
  Future<TarotReadingModel?> build() => _fetchDaily();

  Future<TarotReadingModel?> _fetchDaily() async {
    try {
      final api = ref.read(apiClientProvider);
      final response = await api.dio.get('/api/tarot/daily');
      return TarotReadingModel.fromJson(
          response.data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchDaily);
  }

  Future<String?> askTarotist(String question) async {
    try {
      final api = ref.read(apiClientProvider);
      final response = await api.dio.post(
        '/api/tarot/ask',
        data: {'question': question},
      );
      return response.data['answer'] as String?;
    } catch (e) {
      return null;
    }
  }
}
