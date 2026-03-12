import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../../shared/models/user_model.dart';

class AuthService {
  AuthService({required ApiClient apiClient}) : _api = apiClient;

  final ApiClient _api;

  Future<UserModel> register({
    required String email,
    required String password,
    required String fullName,
    required String birthDate,
  }) async {
    final response = await _api.dio.post(
      '/api/auth/register',
      data: {
        'email': email,
        'password': password,
        'full_name': fullName,
        'birth_date': birthDate,
      },
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<String> login({
    required String email,
    required String password,
  }) async {
    final response = await _api.dio.post(
      '/api/auth/login',
      data: {'email': email, 'password': password},
    );
    final token = response.data['access_token'] as String;
    await _api.saveToken(token);
    return token;
  }

  Future<UserModel> getMe() async {
    final response = await _api.dio.get('/api/auth/me');
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> logout() async {
    try {
      await _api.dio.post('/api/auth/logout');
    } on DioException {
      // Ignore network errors on logout — clear token regardless
    } finally {
      await _api.clearToken();
    }
  }
}
