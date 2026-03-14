import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:flutter/foundation.dart';

/// RevenueCat product identifiers — must match App Store Connect / Play Console.
class PurchaseIds {
  PurchaseIds._();

  // Replace with your actual RevenueCat API keys
  static const String appleApiKey = 'appl_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';
  static const String googleApiKey = 'goog_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';

  static const String monthlyProductId = 'cosmo_premium_monthly';
  static const String annualProductId = 'cosmo_premium_annual';
  static const String entitlementId = 'premium';
  static const String offeringId = 'default';
}

class PurchasesService {
  /// Initialize the RevenueCat SDK.
  /// Call this once in main() after the user is identified.
  static Future<void> configure(String userId) async {
    final apiKey = defaultTargetPlatform == TargetPlatform.iOS
        ? PurchaseIds.appleApiKey
        : PurchaseIds.googleApiKey;

    final config = PurchasesConfiguration(apiKey)..appUserID = userId;
    await Purchases.configure(config);
  }

  /// Log in with our backend user UUID so RevenueCat ties purchases to our user.
  static Future<void> logIn(String userId) async {
    await Purchases.logIn(userId);
  }

  /// Log out (call on user sign-out).
  static Future<void> logOut() async {
    await Purchases.logOut();
  }

  /// Fetch the default offering (monthly + annual packages).
  static Future<Offering?> getOffering() async {
    try {
      final offerings = await Purchases.getOfferings();
      return offerings.current;
    } catch (e) {
      debugPrint('PurchasesService.getOffering error: $e');
      return null;
    }
  }

  /// Purchase a specific package. Returns the updated CustomerInfo on success.
  static Future<CustomerInfo?> purchasePackage(Package package) async {
    try {
      final result = await Purchases.purchasePackage(package);
      return result;
    } on PurchasesErrorCode catch (e) {
      if (e == PurchasesErrorCode.purchaseCancelledError) {
        return null; // User cancelled — not an error
      }
      rethrow;
    }
  }

  /// Restore previous purchases (required by App Store guidelines).
  static Future<CustomerInfo> restorePurchases() async {
    return Purchases.restorePurchases();
  }

  /// Check if user currently has an active premium entitlement.
  static Future<bool> hasPremium() async {
    try {
      final info = await Purchases.getCustomerInfo();
      return info.entitlements.active.containsKey(PurchaseIds.entitlementId);
    } catch (_) {
      return false;
    }
  }

  /// Get full CustomerInfo (entitlements, active subscriptions, etc.).
  static Future<CustomerInfo?> getCustomerInfo() async {
    try {
      return await Purchases.getCustomerInfo();
    } catch (_) {
      return null;
    }
  }
}
