import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import '../services/purchases_service.dart';

/// Current RevenueCat offering (packages available for purchase).
final offeringProvider = FutureProvider<Offering?>((ref) async {
  return PurchasesService.getOffering();
});

/// Whether the current user has an active premium entitlement.
final premiumStatusProvider = FutureProvider<bool>((ref) async {
  return PurchasesService.hasPremium();
});

/// Notifier that manages the purchase flow state.
final purchaseNotifierProvider =
    AsyncNotifierProvider<PurchaseNotifier, CustomerInfo?>(PurchaseNotifier.new);

class PurchaseNotifier extends AsyncNotifier<CustomerInfo?> {
  @override
  Future<CustomerInfo?> build() async {
    return PurchasesService.getCustomerInfo();
  }

  /// Attempt to purchase [package]. Updates state with the new CustomerInfo.
  Future<bool> purchase(Package package) async {
    state = const AsyncLoading();
    final result = await AsyncValue.guard(
      () => PurchasesService.purchasePackage(package),
    );
    state = result;

    if (result.hasValue && result.value != null) {
      // Invalidate premium status so UI rebuilds
      ref.invalidate(premiumStatusProvider);
      return true;
    }
    return false;
  }

  /// Restore previous purchases (iOS requirement).
  Future<bool> restore() async {
    state = const AsyncLoading();
    final result = await AsyncValue.guard(
      () => PurchasesService.restorePurchases(),
    );
    state = result;

    if (result.hasValue) {
      ref.invalidate(premiumStatusProvider);
      final info = result.value;
      return info?.entitlements.active.isNotEmpty ?? false;
    }
    return false;
  }
}
