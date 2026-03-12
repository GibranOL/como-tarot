import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/colors.dart';
import '../../../core/router/app_router.dart';
import '../../auth/providers/auth_provider.dart';
import '../providers/tarot_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authNotifierProvider).valueOrNull;
    final tarotState = ref.watch(tarotReadingProvider);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: SafeArea(
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(child: _buildHeader(context, ref, user?.fullName)),
              SliverPadding(
                padding: const EdgeInsets.all(20),
                sliver: SliverList(
                  delegate: SliverChildListDelegate([
                    _buildDailyCard(context, tarotState),
                    const SizedBox(height: 20),
                    _buildQuickActionsGrid(context),
                    const SizedBox(height: 20),
                    if (!(user?.isPremium ?? false))
                      _buildPremiumBanner(context),
                  ]),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(
      BuildContext context, WidgetRef ref, String? name) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hola, ${name ?? 'Viajero'}',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: CosmoColors.textPrimary,
                    ),
              ),
              Text(
                _getGreeting(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: CosmoColors.textSecondary,
                    ),
              ),
            ],
          ),
          GestureDetector(
            onTap: () => context.push(AppRoutes.profile),
            child: CircleAvatar(
              radius: 22,
              backgroundColor: CosmoColors.secondary,
              child: Text(
                (name?.isNotEmpty == true ? name![0] : '?').toUpperCase(),
                style: const TextStyle(
                  color: CosmoColors.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Buenos días ✨';
    if (hour < 18) return 'Buenas tardes ✨';
    return 'Buenas noches ✨';
  }

  Widget _buildDailyCard(BuildContext context, AsyncValue tarotState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.style_outlined,
                    color: CosmoColors.primary, size: 20),
                const SizedBox(width: 8),
                Text(
                  'Tu lectura de hoy',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: CosmoColors.primary,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            tarotState.when(
              loading: () => const Center(
                child: CircularProgressIndicator(color: CosmoColors.primary),
              ),
              error: (_, __) => _buildReadingError(context),
              data: (reading) => reading != null
                  ? _buildReadingSummary(context, reading)
                  : _buildReadingError(context),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => context.push('/home/tarot/reading'),
                icon: const Icon(Icons.auto_awesome, size: 18),
                label: const Text('Ver lectura completa'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReadingSummary(BuildContext context, dynamic reading) {
    final cards = reading.cards as List;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: List.generate(
        cards.length.clamp(0, 3),
        (i) => _MiniCard(
          cardName: cards[i].name as String,
          position: reading.positionLabels[i],
          isReversed: cards[i].isReversed as bool,
        ),
      ),
    );
  }

  Widget _buildReadingError(BuildContext context) {
    return Center(
      child: Text(
        'Los astros están preparando tu lectura...',
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: CosmoColors.textSecondary,
              fontStyle: FontStyle.italic,
            ),
        textAlign: TextAlign.center,
      ),
    );
  }

  Widget _buildQuickActionsGrid(BuildContext context) {
    final actions = [
      _QuickAction(
        icon: Icons.wb_sunny_outlined,
        label: 'Horóscopo',
        route: AppRoutes.horoscope,
      ),
      _QuickAction(
        icon: Icons.calculate_outlined,
        label: 'Numerología',
        route: AppRoutes.numerology,
      ),
      _QuickAction(
        icon: Icons.favorite_border_outlined,
        label: 'Compatibilidad',
        route: AppRoutes.compatibility,
      ),
      _QuickAction(
        icon: Icons.chat_bubble_outline,
        label: 'Preguntar',
        route: '/home/tarot/reading',
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Explora',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: CosmoColors.textSecondary,
              ),
        ),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.4,
          children: actions
              .map((a) => _QuickActionTile(action: a, context: context))
              .toList(),
        ),
      ],
    );
  }

  Widget _buildPremiumBanner(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: LinearGradient(
          colors: [
            CosmoColors.secondary.withOpacity(0.3),
            CosmoColors.primary.withOpacity(0.2),
          ],
        ),
        border: Border.all(color: CosmoColors.primary.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.star_rounded, color: CosmoColors.primary, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Hazte Premium',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: CosmoColors.primary,
                      ),
                ),
                Text(
                  'Lecturas ilimitadas • Compatibilidad • Más',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: CosmoColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          Text(
            '\$4.44/mes',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: CosmoColors.primary,
                ),
          ),
        ],
      ),
    );
  }
}

class _MiniCard extends StatelessWidget {
  const _MiniCard({
    required this.cardName,
    required this.position,
    required this.isReversed,
  });

  final String cardName;
  final String position;
  final bool isReversed;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        RotatedBox(
          quarterTurns: isReversed ? 2 : 0,
          child: Container(
            width: 64,
            height: 96,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: CosmoColors.primary, width: 1.5),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF1A1A3E), Color(0xFF0A0A1A)],
              ),
            ),
            child: const Icon(
              Icons.auto_awesome,
              color: CosmoColors.primary,
              size: 28,
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          position,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: CosmoColors.textSecondary,
              ),
        ),
        SizedBox(
          width: 80,
          child: Text(
            cardName,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: CosmoColors.textPrimary,
                  fontSize: 10,
                ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _QuickAction {
  const _QuickAction({
    required this.icon,
    required this.label,
    required this.route,
  });

  final IconData icon;
  final String label;
  final String route;
}

class _QuickActionTile extends StatelessWidget {
  const _QuickActionTile({required this.action, required this.context});

  final _QuickAction action;
  final BuildContext context;

  @override
  Widget build(BuildContext ctx) {
    return GestureDetector(
      onTap: () => ctx.push(action.route),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          color: CosmoColors.cardBorder,
          border: Border.all(color: const Color(0xFF3A3A5E), width: 1),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(action.icon, color: CosmoColors.primary, size: 32),
            const SizedBox(height: 8),
            Text(
              action.label,
              style: Theme.of(ctx).textTheme.titleSmall?.copyWith(
                    color: CosmoColors.textPrimary,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
