import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import '../../../core/constants/colors.dart';
import '../providers/purchases_provider.dart';
import '../services/purchases_service.dart';

class PaywallScreen extends ConsumerWidget {
  const PaywallScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offeringAsync = ref.watch(offeringProvider);
    final purchaseState = ref.watch(purchaseNotifierProvider);

    return Scaffold(
      backgroundColor: CosmoColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: CosmoColors.textSecondary),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: offeringAsync.when(
        loading: () => const Center(
          child: CircularProgressIndicator(color: CosmoColors.primary),
        ),
        error: (_, __) => _buildErrorState(context),
        data: (offering) => _buildPaywall(context, ref, offering, purchaseState),
      ),
    );
  }

  Widget _buildPaywall(
    BuildContext context,
    WidgetRef ref,
    Offering? offering,
    AsyncValue<CustomerInfo?> purchaseState,
  ) {
    final monthly = offering?.availablePackages.where(
      (p) => p.packageType == PackageType.monthly,
    ).firstOrNull;

    final annual = offering?.availablePackages.where(
      (p) => p.packageType == PackageType.annual,
    ).firstOrNull;

    final isLoading = purchaseState.isLoading;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 8),

          // ── Header ────────────────────────────────────────────────
          const _GoldDivider(),
          const SizedBox(height: 20),
          const Text(
            '✦ COSMO PREMIUM ✦',
            style: TextStyle(
              color: CosmoColors.primary,
              fontSize: 13,
              letterSpacing: 3,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'Desbloquea el cosmos completo',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: CosmoColors.textPrimary,
              fontSize: 26,
              fontWeight: FontWeight.bold,
              height: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Lecturas ilimitadas, compatibilidad zodiacal\ny acceso a tu carta natal completa.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: CosmoColors.textSecondary,
              fontSize: 15,
              height: 1.5,
            ),
          ),

          const SizedBox(height: 28),

          // ── Feature comparison ────────────────────────────────────
          _buildFeatureList(),

          const SizedBox(height: 32),

          // ── Pricing cards ─────────────────────────────────────────
          if (annual != null)
            _PriceCard(
              package: annual,
              label: 'ANUAL',
              price: annual.storeProduct.priceString,
              badge: 'AHORRA 17%',
              description: 'Menos de \$4 al mes',
              isHighlighted: true,
              isLoading: isLoading,
              onTap: () => _purchase(context, ref, annual),
            ),

          const SizedBox(height: 12),

          if (monthly != null)
            _PriceCard(
              package: monthly,
              label: 'MENSUAL',
              price: monthly.storeProduct.priceString,
              badge: null,
              description: 'Facturado mensualmente',
              isHighlighted: false,
              isLoading: isLoading,
              onTap: () => _purchase(context, ref, monthly),
            ),

          // Fallback when RevenueCat products aren't loaded
          if (monthly == null && annual == null) _buildFallbackPricing(),

          const SizedBox(height: 20),

          // ── Legal + Restore ───────────────────────────────────────
          TextButton(
            onPressed: isLoading ? null : () => _restore(context, ref),
            child: const Text(
              'Restaurar compras',
              style: TextStyle(color: CosmoColors.textSecondary, fontSize: 13),
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Cancela cuando quieras • Sin compromisos\nSe renueva automáticamente',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: CosmoColors.textSecondary,
              fontSize: 11,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildFeatureList() {
    const features = [
      (Icons.auto_awesome, 'Lecturas de tarot ilimitadas'),
      (Icons.psychology, 'Interpretaciones IA profundas y personalizadas'),
      (Icons.favorite, 'Compatibilidad zodiacal completa'),
      (Icons.stars, 'Carta natal y análisis de planetas'),
      (Icons.history, 'Historial de lecturas sin límite'),
      (Icons.chat_bubble_outline, 'Pregunta al Tarotista: ilimitado'),
      (Icons.date_range, 'Horóscopo semanal premium'),
    ];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: CosmoColors.cardBorder.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: CosmoColors.primary.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: features.map((f) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 7),
            child: Row(
              children: [
                Icon(f.$1, color: CosmoColors.primary, size: 20),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    f.$2,
                    style: const TextStyle(
                      color: CosmoColors.textPrimary,
                      fontSize: 14,
                    ),
                  ),
                ),
                const Icon(Icons.check_circle, color: CosmoColors.success, size: 18),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFallbackPricing() {
    return Column(
      children: [
        _FallbackPriceCard(
          label: 'ANUAL',
          price: '\$44.44',
          badge: 'AHORRA 17%',
          description: 'al año',
          isHighlighted: true,
        ),
        const SizedBox(height: 12),
        _FallbackPriceCard(
          label: 'MENSUAL',
          price: '\$4.44',
          badge: null,
          description: 'al mes',
          isHighlighted: false,
        ),
      ],
    );
  }

  Widget _buildErrorState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.wifi_off, color: CosmoColors.textSecondary, size: 48),
            const SizedBox(height: 16),
            const Text(
              'No se pudieron cargar los precios.\nVerifica tu conexión.',
              textAlign: TextAlign.center,
              style: TextStyle(color: CosmoColors.textSecondary),
            ),
            const SizedBox(height: 20),
            OutlinedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Volver'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _purchase(
    BuildContext context,
    WidgetRef ref,
    Package package,
  ) async {
    final notifier = ref.read(purchaseNotifierProvider.notifier);
    final success = await notifier.purchase(package);

    if (!context.mounted) return;
    if (success) {
      _showSuccess(context, '¡Bienvenido a Premium! Las estrellas te esperan. ✨');
      Navigator.of(context).pop(true); // pop with true = purchased
    } else {
      final state = ref.read(purchaseNotifierProvider);
      if (state.hasError) {
        _showError(context, 'No se completó la compra. Inténtalo de nuevo.');
      }
    }
  }

  Future<void> _restore(BuildContext context, WidgetRef ref) async {
    final notifier = ref.read(purchaseNotifierProvider.notifier);
    final restored = await notifier.restore();

    if (!context.mounted) return;
    if (restored) {
      _showSuccess(context, 'Compras restauradas. ¡Bienvenido de vuelta! ✨');
      Navigator.of(context).pop(true);
    } else {
      _showError(context, 'No se encontraron compras anteriores.');
    }
  }

  void _showSuccess(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: CosmoColors.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: CosmoColors.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}


// ── Reusable widgets ──────────────────────────────────────────────────────────

class _GoldDivider extends StatelessWidget {
  const _GoldDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 1,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.transparent, CosmoColors.primary, Colors.transparent],
        ),
      ),
    );
  }
}

class _PriceCard extends StatelessWidget {
  const _PriceCard({
    required this.package,
    required this.label,
    required this.price,
    required this.badge,
    required this.description,
    required this.isHighlighted,
    required this.isLoading,
    required this.onTap,
  });

  final Package package;
  final String label;
  final String price;
  final String? badge;
  final String description;
  final bool isHighlighted;
  final bool isLoading;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isLoading ? null : onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isHighlighted
              ? CosmoColors.primary.withValues(alpha: 0.12)
              : CosmoColors.cardBorder.withValues(alpha: 0.3),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isHighlighted ? CosmoColors.primary : CosmoColors.cardBorder,
            width: isHighlighted ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            // Plan info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        label,
                        style: TextStyle(
                          color: isHighlighted
                              ? CosmoColors.primary
                              : CosmoColors.textSecondary,
                          fontSize: 12,
                          letterSpacing: 1.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (badge != null) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: CosmoColors.primary,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            badge!,
                            style: const TextStyle(
                              color: Colors.black,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: const TextStyle(
                      color: CosmoColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            // Price
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  price,
                  style: TextStyle(
                    color: isHighlighted
                        ? CosmoColors.primary
                        : CosmoColors.textPrimary,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (isLoading)
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: CosmoColors.primary,
                    ),
                  )
                else
                  const Icon(
                    Icons.arrow_forward_ios,
                    color: CosmoColors.primary,
                    size: 16,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _FallbackPriceCard extends StatelessWidget {
  const _FallbackPriceCard({
    required this.label,
    required this.price,
    required this.badge,
    required this.description,
    required this.isHighlighted,
  });

  final String label;
  final String price;
  final String? badge;
  final String description;
  final bool isHighlighted;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isHighlighted
            ? CosmoColors.primary.withValues(alpha: 0.12)
            : CosmoColors.cardBorder.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isHighlighted ? CosmoColors.primary : CosmoColors.cardBorder,
          width: isHighlighted ? 1.5 : 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      label,
                      style: TextStyle(
                        color: isHighlighted
                            ? CosmoColors.primary
                            : CosmoColors.textSecondary,
                        fontSize: 12,
                        letterSpacing: 1.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (badge != null) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: CosmoColors.primary,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          badge!,
                          style: const TextStyle(
                            color: Colors.black,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  description,
                  style: const TextStyle(
                    color: CosmoColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          Text(
            price,
            style: TextStyle(
              color: isHighlighted
                  ? CosmoColors.primary
                  : CosmoColors.textPrimary,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
