import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/colors.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/compatibility_provider.dart';

class CompatibilityScreen extends ConsumerStatefulWidget {
  const CompatibilityScreen({super.key});

  @override
  ConsumerState<CompatibilityScreen> createState() =>
      _CompatibilityScreenState();
}

class _CompatibilityScreenState extends ConsumerState<CompatibilityScreen> {
  String? _selectedSign;

  static const _signs = [
    ('aries', '♈', 'Aries'),
    ('taurus', '♉', 'Tauro'),
    ('gemini', '♊', 'Géminis'),
    ('cancer', '♋', 'Cáncer'),
    ('leo', '♌', 'Leo'),
    ('virgo', '♍', 'Virgo'),
    ('libra', '♎', 'Libra'),
    ('scorpio', '♏', 'Escorpio'),
    ('sagittarius', '♐', 'Sagitario'),
    ('capricorn', '♑', 'Capricornio'),
    ('aquarius', '♒', 'Acuario'),
    ('pisces', '♓', 'Piscis'),
  ];

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authNotifierProvider).valueOrNull;
    final isPremium = user?.isPremium ?? false;
    final compatState = ref.watch(compatibilityNotifierProvider);

    if (!isPremium) {
      return Scaffold(
        appBar: AppBar(title: const Text('Compatibilidad')),
        body: Container(
          decoration:
              const BoxDecoration(gradient: CosmoColors.backgroundGradient),
          child: _buildPremiumGate(context),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Compatibilidad')),
      body: Container(
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Selecciona el signo de tu pareja',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: CosmoColors.textSecondary,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              _buildSignGrid(context),
              const SizedBox(height: 24),
              if (_selectedSign != null)
                ElevatedButton(
                  onPressed: compatState.isLoading
                      ? null
                      : () => ref
                          .read(compatibilityNotifierProvider.notifier)
                          .check(_selectedSign!),
                  child: compatState.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: CosmoColors.background,
                          ),
                        )
                      : const Text('Ver compatibilidad'),
                ),
              const SizedBox(height: 24),
              compatState.when(
                loading: () => const SizedBox.shrink(),
                error: (e, _) => Text(
                  e.toString(),
                  style: const TextStyle(color: CosmoColors.error),
                  textAlign: TextAlign.center,
                ),
                data: (result) =>
                    result == null ? const SizedBox.shrink() : _buildResult(context, result),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSignGrid(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
        childAspectRatio: 0.85,
      ),
      itemCount: _signs.length,
      itemBuilder: (context, i) {
        final (key, emoji, name) = _signs[i];
        final isSelected = _selectedSign == key;
        return GestureDetector(
          onTap: () => setState(() => _selectedSign = key),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              color: isSelected
                  ? CosmoColors.primary.withOpacity(0.2)
                  : CosmoColors.cardBorder,
              border: Border.all(
                color: isSelected ? CosmoColors.primary : Colors.transparent,
                width: 2,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(emoji, style: const TextStyle(fontSize: 24)),
                const SizedBox(height: 4),
                Text(
                  name,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: isSelected
                            ? CosmoColors.primary
                            : CosmoColors.textSecondary,
                        fontSize: 10,
                      ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildResult(BuildContext context, CompatibilityResult result) {
    return Column(
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                Text(
                  'Puntuación de compatibilidad',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: CosmoColors.textSecondary,
                      ),
                ),
                const SizedBox(height: 16),
                Stack(
                  alignment: Alignment.center,
                  children: [
                    SizedBox(
                      width: 120,
                      height: 120,
                      child: CircularProgressIndicator(
                        value: result.compatibilityScore / 100,
                        strokeWidth: 10,
                        backgroundColor: CosmoColors.cardBorder,
                        color: _scoreColor(result.compatibilityScore),
                      ),
                    ),
                    Text(
                      '${result.compatibilityScore}%',
                      style: Theme.of(context)
                          .textTheme
                          .headlineLarge
                          ?.copyWith(
                              color: _scoreColor(result.compatibilityScore)),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  result.aiInterpretation,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.8,
                      ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Color _scoreColor(int score) {
    if (score >= 75) return CosmoColors.success;
    if (score >= 50) return CosmoColors.primary;
    return CosmoColors.error;
  }

  Widget _buildPremiumGate(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.favorite_border,
                color: CosmoColors.primary, size: 64),
            const SizedBox(height: 24),
            Text(
              'Compatibilidad Zodiacal',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: CosmoColors.primary,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'Descubre qué tan bien te llevas con cada signo.\nFunción exclusiva para miembros Premium.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: CosmoColors.textSecondary,
                    height: 1.7,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {},
              child: const Text('Hazte Premium — \$4.44/mes'),
            ),
          ],
        ),
      ),
    );
  }
}
