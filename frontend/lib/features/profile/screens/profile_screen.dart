import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/colors.dart';
import '../../../core/router/app_router.dart';
import '../../auth/providers/auth_provider.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authNotifierProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(title: const Text('Mi Perfil')),
      body: Container(
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: user == null
            ? const Center(
                child: CircularProgressIndicator(color: CosmoColors.primary))
            : SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildAvatar(context, user.fullName),
                    const SizedBox(height: 24),
                    _buildInfoCard(context, user),
                    const SizedBox(height: 16),
                    _buildSubscriptionCard(context, user.isPremium),
                    const SizedBox(height: 24),
                    OutlinedButton.icon(
                      onPressed: () async {
                        await ref.read(authNotifierProvider.notifier).logout();
                        if (context.mounted) context.go(AppRoutes.login);
                      },
                      icon: const Icon(Icons.logout, size: 18),
                      label: const Text('Cerrar sesión'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: CosmoColors.error,
                        side: const BorderSide(color: CosmoColors.error),
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildAvatar(BuildContext context, String name) {
    return Column(
      children: [
        CircleAvatar(
          radius: 48,
          backgroundColor: CosmoColors.secondary,
          child: Text(
            name.isNotEmpty ? name[0].toUpperCase() : '?',
            style: const TextStyle(
              fontSize: 40,
              color: CosmoColors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Text(
          name,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: CosmoColors.textPrimary,
              ),
        ),
      ],
    );
  }

  Widget _buildInfoCard(BuildContext context, dynamic user) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Información',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: CosmoColors.primary,
                  ),
            ),
            const SizedBox(height: 16),
            _InfoRow(
              icon: Icons.email_outlined,
              label: 'Correo',
              value: user.email as String,
            ),
            const Divider(height: 24),
            _InfoRow(
              icon: Icons.stars_outlined,
              label: 'Signo zodiacal',
              value: user.zodiacSign as String,
            ),
            const Divider(height: 24),
            _InfoRow(
              icon: Icons.calculate_outlined,
              label: 'Número de vida',
              value: '${user.lifeNumber}',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubscriptionCard(BuildContext context, bool isPremium) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Icon(
              isPremium ? Icons.star_rounded : Icons.star_border_rounded,
              color: CosmoColors.primary,
              size: 32,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isPremium ? 'Premium activo' : 'Plan gratuito',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: CosmoColors.primary,
                        ),
                  ),
                  Text(
                    isPremium
                        ? 'Tienes acceso completo'
                        : '1 lectura/día · Funciones básicas',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: CosmoColors.textSecondary,
                        ),
                  ),
                ],
              ),
            ),
            if (!isPremium)
              TextButton(
                onPressed: () => context.push(AppRoutes.paywall),
                child: const Text(
                  'Mejorar',
                  style: TextStyle(color: CosmoColors.primary),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: CosmoColors.textSecondary, size: 20),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: CosmoColors.textSecondary,
                  ),
            ),
            Text(
              value,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: CosmoColors.textPrimary,
                  ),
            ),
          ],
        ),
      ],
    );
  }
}
