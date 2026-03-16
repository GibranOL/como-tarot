import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/models/tarot_reading_model.dart';

part 'tarot_provider.g.dart';

@riverpod
class TarotReadingNotifier extends _$TarotReadingNotifier {
  @override
  FutureOr<TarotReadingModel?> build() => _fetchDaily();

  Future<TarotReadingModel?> _fetchDaily() async {
    final api = ref.watch(apiClientProvider);
    final response = await api.dio.get('/api/tarot/daily');
    
    // Si la respuesta es exitosa pero vacía, o si hay un error de negocio
    // el interceptor de Dio ya lo maneja o lanza una excepción.
    return TarotReadingModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Refresca la lectura diaria. Los errores se propagarán al estado del provider.
  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetchDaily);
  }

  /// Envía una pregunta al tarotista AI. 
  /// Mantiene la lectura actual mientras se espera la respuesta.
  Future<String> askTarotist(String question) async {
    final api = ref.watch(apiClientProvider);
    final response = await api.dio.post(
      '/api/tarot/ask',
      data: {'question': question},
    );
    
    final answer = response.data['answer'] as String?;
    if (answer == null) {
      throw Exception('El universo no ha podido responder en este momento.');
    }
    return answer;
  }
}
