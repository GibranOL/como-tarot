import 'package:flutter/material.dart';

class CosmoColors {
  CosmoColors._();

  static const Color background = Color(0xFF0A0A1A);
  static const Color primary = Color(0xFFC9A84C);
  static const Color secondary = Color(0xFF7B2FBE);
  static const Color accent = Color(0xFFE8D5B7);
  static const Color textPrimary = Color(0xFFF0E6D3);
  static const Color textSecondary = Color(0xFF8E8E93);
  static const Color error = Color(0xFFE74C3C);
  static const Color success = Color(0xFF2ECC71);
  static const Color cardBorder = Color(0xFF2A2A3E);
  static const Color gradientTop = Color(0xFF1A1A2E);
  static const Color gradientBottom = Color(0xFF0A0A1A);

  static const LinearGradient backgroundGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [gradientTop, gradientBottom],
  );

  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFD4B468), Color(0xFFC9A84C)],
  );
}
