import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cosmo_tarot/app.dart';

void main() {
  testWidgets('App smoke test — renders without crashing',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: CosmoTarotApp()),
    );

    // Pump one frame to let the initial build complete
    await tester.pump(Duration.zero);

    // Verify the app widget tree builds (MaterialApp is the root)
    expect(find.byType(MaterialApp), findsOneWidget);
  }, skip: true);
}
