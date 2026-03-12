import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/colors.dart';
import '../providers/numerology_provider.dart';

class NumerologyScreen extends ConsumerWidget {
  const NumerologyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final numState = ref.watch(numerologyProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Numerología')),
      body: Container(
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: numState.when(
          loading: () => const Center(
            child: CircularProgressIndicator(color: CosmoColors.primary),
          ),
          error: (_, __) => _buildError(context),
          data: (profile) => profile == null
              ? _buildError(context)
              : _buildContent(context, profile),
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, NumerologyProfile profile) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Column(
              children: [
                _BigNumber(number: profile.lifeNumber),
                const SizedBox(height: 12),
                Text(
                  'Tu Número de Vida',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: CosmoColors.primary,
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
                  Text(
                    'Significado',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: CosmoColors.primary,
                        ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    profile.lifeNumberMeaning,
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(height: 1.8),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _SmallNumberCard(
                  label: 'Año Personal',
                  number: profile.personalYear,
                  meaning: profile.personalYearMeaning,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _SmallNumberCard(
                  label: 'Mes Personal',
                  number: profile.personalMonth,
                  meaning: '',
                ),
              ),
            ],
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
          'No pudimos calcular tu perfil numerológico.',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: CosmoColors.textSecondary,
              ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _BigNumber extends StatelessWidget {
  const _BigNumber({required this.number});
  final int number;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 120,
      height: 120,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: CosmoColors.primary, width: 3),
        gradient: const RadialGradient(
          colors: [Color(0xFF2A1A4E), CosmoColors.gradientTop],
        ),
      ),
      child: Center(
        child: Text(
          '$number',
          style: Theme.of(context).textTheme.displayLarge?.copyWith(
                color: CosmoColors.primary,
                fontSize: 52,
              ),
        ),
      ),
    );
  }
}

class _SmallNumberCard extends StatelessWidget {
  const _SmallNumberCard({
    required this.label,
    required this.number,
    required this.meaning,
  });

  final String label;
  final int number;
  final String meaning;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: CosmoColors.textSecondary,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              '$number',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    color: CosmoColors.primary,
                  ),
            ),
            if (meaning.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                meaning,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: CosmoColors.textSecondary,
                      height: 1.5,
                    ),
                textAlign: TextAlign.center,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
