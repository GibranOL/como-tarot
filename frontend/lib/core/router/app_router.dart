import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/splash_screen.dart';
import '../../features/auth/screens/onboarding_screen.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/tarot/screens/home_screen.dart';
import '../../features/tarot/screens/tarot_reading_screen.dart';
import '../../features/horoscope/screens/horoscope_screen.dart';
import '../../features/compatibility/screens/compatibility_screen.dart';
import '../../features/numerology/screens/numerology_screen.dart';
import '../../features/profile/screens/profile_screen.dart';

// Route name constants
class AppRoutes {
  AppRoutes._();

  static const splash = '/';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const register = '/register';
  static const home = '/home';
  static const tarotReading = '/tarot/reading';
  static const horoscope = '/horoscope';
  static const compatibility = '/compatibility';
  static const numerology = '/numerology';
  static const profile = '/profile';
}

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authNotifierProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull != null;
      final isAuthRoute = state.matchedLocation == AppRoutes.login ||
          state.matchedLocation == AppRoutes.register ||
          state.matchedLocation == AppRoutes.onboarding ||
          state.matchedLocation == AppRoutes.splash;

      if (authState.isLoading) return null;

      if (!isLoggedIn && !isAuthRoute) return AppRoutes.login;
      if (isLoggedIn &&
          (state.matchedLocation == AppRoutes.login ||
              state.matchedLocation == AppRoutes.register)) {
        return AppRoutes.home;
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoutes.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: AppRoutes.home,
        builder: (context, state) => const HomeScreen(),
        routes: [
          GoRoute(
            path: 'tarot/reading',
            builder: (context, state) => const TarotReadingScreen(),
          ),
        ],
      ),
      GoRoute(
        path: AppRoutes.horoscope,
        builder: (context, state) => const HoroscopeScreen(),
      ),
      GoRoute(
        path: AppRoutes.compatibility,
        builder: (context, state) => const CompatibilityScreen(),
      ),
      GoRoute(
        path: AppRoutes.numerology,
        builder: (context, state) => const NumerologyScreen(),
      ),
      GoRoute(
        path: AppRoutes.profile,
        builder: (context, state) => const ProfileScreen(),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      backgroundColor: const Color(0xFF0A0A1A),
      body: Center(
        child: Text(
          'Page not found',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
      ),
    ),
  );
});
