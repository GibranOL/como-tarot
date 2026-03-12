import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/models/user_model.dart';
import '../services/auth_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(apiClient: ref.watch(apiClientProvider));
});

/// Provides the currently authenticated user (null = not logged in).
final authStateProvider = FutureProvider<UserModel?>((ref) async {
  final api = ref.watch(apiClientProvider);
  final token = await api.getToken();
  if (token == null) return null;

  try {
    return await ref.watch(authServiceProvider).getMe();
  } catch (_) {
    await api.clearToken();
    return null;
  }
});

/// Notifier for login / register / logout actions.
final authNotifierProvider =
    AsyncNotifierProvider<AuthNotifier, UserModel?>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<UserModel?> {
  @override
  Future<UserModel?> build() async {
    final api = ref.watch(apiClientProvider);
    final token = await api.getToken();
    if (token == null) return null;
    try {
      return await ref.watch(authServiceProvider).getMe();
    } catch (_) {
      await api.clearToken();
      return null;
    }
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final service = ref.read(authServiceProvider);
      await service.login(email: email, password: password);
      return service.getMe();
    });
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
    required String birthDate,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final service = ref.read(authServiceProvider);
      await service.register(
        email: email,
        password: password,
        fullName: fullName,
        birthDate: birthDate,
      );
      // Auto-login after registration
      await service.login(email: email, password: password);
      return service.getMe();
    });
  }

  Future<void> logout() async {
    await ref.read(authServiceProvider).logout();
    state = const AsyncData(null);
  }
}
