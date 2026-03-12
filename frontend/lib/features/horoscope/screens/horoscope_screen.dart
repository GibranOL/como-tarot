import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/colors.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/horoscope_provider.dart';

class HoroscopeScreen extends ConsumerWidget {
  const HoroscopeScreen({super.key});

  static const Map<String, String> _zodiacEmoji = {
    'aries': '♈',
    'taurus': '♉',
    'gemini': '♊',
    'cancer': '♋',
    'leo': '♌',
    'virgo': '♍',
    'libra': '♎',
    'scorpio': '♏',
    'sagittarius': '♐',
    'capricorn': '♑',
    'aquarius': '♒',
    'pisces': '♓',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final horoscopeState = ref.watch(horoscopeProvider);
    final user = ref.watch(authNotifierProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(title: const Text('Horóscopo')),
      body: Container(
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: horoscopeState.when(
          loading: () => const Center(
            child: CircularProgressIndicator(color: CosmoColors.primary),
          ),
          error: (_, __) => _buildError(context),
          data: (horoscope) =>
              horoscope == null ? _buildError(context) : _buildContent(context, horoscope, user?.isPremium ?? false),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, HoroscopeModel horoscope, bool isPremium) {
    final sign = horoscope.zodiacSign.toLowerCase();
    final emoji = _zodiacEmoji[sign] ?? '✨';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Column(
              children: [
                Text(emoji, style: const TextStyle(fontSize: 72)),
                const SizedBox(height: 12),
                Text(
                  horoscope.zodiacSign.toUpperCase(),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        color: CosmoColors.primary,
                        letterSpacing: 2,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  horoscope.date,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: CosmoColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.wb_sunny_outlined,
                          color: CosmoColors.primary, size: 18),
                      const SizedBox(width: 8),
                      Text(
                        'Horóscopo de hoy',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: CosmoColors.primary,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    horoscope.horoscope,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          height: 1.8,
                        ),
                  ),
                ],
              ),
            ),
          ),
          if (isPremium && horoscope.weeklyHoroscope != null) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.calendar_view_week_outlined,
                            color: CosmoColors.secondary, size: 18),
                        const SizedBox(width: 8),
                        Text(
                          'Esta semana',
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(color: CosmoColors.secondary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      horoscope.weeklyHoroscope!,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            height: 1.8,
                          ),
                    ),
                  ],
                ),
              ),
            ),
          ] else if (!isPremium) ...[
            const SizedBox(height: 16),
            _buildPremiumTeaser(context),
          ],
        ],
      ),
    );
  }

  Widget _buildPremiumTeaser(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: CosmoColors.primary.withOpacity(0.4)),
        gradient: LinearGradient(
          colors: [
            CosmoColors.primary.withOpacity(0.1),
            CosmoColors.secondary.withOpacity(0.05),
          ],
        ),
      ),
      child: Column(
        children: [
          const Icon(Icons.lock_outlined, color: CosmoColors.primary, size: 32),
          const SizedBox(height: 8),
          Text(
            'Horóscopo semanal — Premium',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: CosmoColors.primary,
                ),
          ),
          const SizedBox(height: 4),
          Text(
            'Hazte premium para ver tu guía semanal completa',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: CosmoColors.textSecondary,
                ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildError(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'No pudimos obtener tu horóscopo.\nIntenta de nuevo.',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: CosmoColors.textSecondary,
                height: 1.8,
              ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
