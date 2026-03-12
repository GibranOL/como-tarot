import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get dark => ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: CosmoColors.background,
        colorScheme: const ColorScheme.dark(
          primary: CosmoColors.primary,
          secondary: CosmoColors.secondary,
          surface: CosmoColors.cardBorder,
          error: CosmoColors.error,
          onPrimary: CosmoColors.background,
          onSecondary: CosmoColors.textPrimary,
          onSurface: CosmoColors.textPrimary,
          onError: CosmoColors.textPrimary,
        ),
        textTheme: _buildTextTheme(),
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          titleTextStyle: GoogleFonts.cinzel(
            color: CosmoColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
          iconTheme: const IconThemeData(color: CosmoColors.primary),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: CosmoColors.primary,
            foregroundColor: CosmoColors.background,
            textStyle: GoogleFonts.lato(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            minimumSize: const Size.fromHeight(52),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: CosmoColors.primary,
            side: const BorderSide(color: CosmoColors.primary, width: 1.5),
            textStyle: GoogleFonts.lato(
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            minimumSize: const Size.fromHeight(52),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: CosmoColors.cardBorder,
          hintStyle: GoogleFonts.lato(color: CosmoColors.textSecondary),
          labelStyle: GoogleFonts.lato(color: CosmoColors.textSecondary),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: CosmoColors.cardBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: CosmoColors.cardBorder),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: CosmoColors.primary, width: 2),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: CosmoColors.error),
          ),
          focusedErrorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: CosmoColors.error, width: 2),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        cardTheme: CardThemeData(
          color: CosmoColors.cardBorder,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF3A3A5E), width: 1),
          ),
          elevation: 0,
        ),
        dividerTheme: const DividerThemeData(
          color: CosmoColors.cardBorder,
          thickness: 1,
        ),
        useMaterial3: true,
      );

  static TextTheme _buildTextTheme() => TextTheme(
        displayLarge: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 32,
          fontWeight: FontWeight.w700,
        ),
        displayMedium: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 28,
          fontWeight: FontWeight.w600,
        ),
        displaySmall: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
        headlineLarge: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 22,
          fontWeight: FontWeight.w600,
        ),
        headlineMedium: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w500,
        ),
        headlineSmall: GoogleFonts.cinzel(
          color: CosmoColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w500,
        ),
        titleLarge: GoogleFonts.lato(
          color: CosmoColors.textPrimary,
          fontSize: 17,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: GoogleFonts.lato(
          color: CosmoColors.textPrimary,
          fontSize: 15,
          fontWeight: FontWeight.w600,
        ),
        titleSmall: GoogleFonts.lato(
          color: CosmoColors.textSecondary,
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: GoogleFonts.lato(
          color: CosmoColors.textPrimary,
          fontSize: 16,
          height: 1.6,
        ),
        bodyMedium: GoogleFonts.lato(
          color: CosmoColors.textPrimary,
          fontSize: 14,
          height: 1.5,
        ),
        bodySmall: GoogleFonts.lato(
          color: CosmoColors.textSecondary,
          fontSize: 12,
          height: 1.4,
        ),
        labelLarge: GoogleFonts.lato(
          color: CosmoColors.textPrimary,
          fontSize: 14,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.5,
        ),
        labelSmall: GoogleFonts.lato(
          color: CosmoColors.textSecondary,
          fontSize: 11,
          letterSpacing: 0.5,
        ),
      );
}
