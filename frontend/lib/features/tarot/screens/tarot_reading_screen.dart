import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/colors.dart';
import '../../../core/utils/tarot_card_image_helper.dart';
import '../../../shared/models/tarot_reading_model.dart';
import '../providers/tarot_provider.dart';
import '../widgets/flip_card_widget.dart';

class TarotReadingScreen extends ConsumerStatefulWidget {
  const TarotReadingScreen({super.key});

  @override
  ConsumerState<TarotReadingScreen> createState() => _TarotReadingScreenState();
}

class _TarotReadingScreenState extends ConsumerState<TarotReadingScreen> {
  final List<bool> _flipped = [false, false, false];
  final _questionController = TextEditingController();
  String? _aiAnswer;
  bool _isAsking = false;
  String? _askError;

  @override
  void dispose() {
    _questionController.dispose();
    super.dispose();
  }

  Future<void> _askTarotist() async {
    final q = _questionController.text.trim();
    if (q.isEmpty) return;

    setState(() {
      _isAsking = true;
      _aiAnswer = null;
      _askError = null;
    });

    try {
      final answer = await ref
          .read(tarotReadingNotifierProvider.notifier)
          .askTarotist(q);

      if (mounted) {
        setState(() {
          _isAsking = false;
          _aiAnswer = answer;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isAsking = false;
          _askError = 'El cosmos está ocupado en este momento. Inténtalo de nuevo.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Nota: El generador usa el nombre de la clase sin 'Notifier' por defecto
    // pero como la clase se llama TarotReadingNotifier, el provider es tarotReadingNotifierProvider.
    final readingState = ref.watch(tarotReadingNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tu Lectura de Hoy'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Container(
        height: double.infinity,
        decoration: const BoxDecoration(gradient: CosmoColors.backgroundGradient),
        child: readingState.when(
          loading: () => const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(color: CosmoColors.primary),
                SizedBox(height: 16),
                Text('Consultando a los astros...', 
                  style: TextStyle(color: CosmoColors.textSecondary)),
              ],
            ),
          ),
          error: (e, _) => _buildError(context, e),
          data: (reading) =>
              reading == null ? _buildEmpty(context) : _buildReading(context, reading),
        ),
      ),
    );
  }

  Widget _buildError(BuildContext context, Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off, color: CosmoColors.error, size: 48),
            const SizedBox(height: 16),
            Text(
              'No pudimos conectar con el universo',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: CosmoColors.textPrimary,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Asegúrate de tener conexión a internet o inténtalo más tarde.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: CosmoColors.textSecondary,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref.read(tarotReadingNotifierProvider.notifier).refresh(),
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.auto_awesome, color: CosmoColors.textSecondary, size: 48),
            const SizedBox(height: 16),
            Text(
              'Tu lectura de hoy aún no está lista.\nVuelve pronto.',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: CosmoColors.textSecondary,
                    height: 1.8,
                  ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReading(BuildContext context, TarotReadingModel reading) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Toca cada carta para revelarla',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: CosmoColors.textSecondary,
                ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          _buildCardsRow(context, reading),
          const SizedBox(height: 32),
          if (_flipped.every((f) => f)) ...[
            _buildInterpretation(context, reading.aiInterpretation),
            const SizedBox(height: 24),
            _buildAskTarotist(context),
          ] else
            Center(
              child: Text(
                'Revela las ${_flipped.where((f) => !f).length} carta(s) restante(s)',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: CosmoColors.primary,
                    ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCardsRow(BuildContext context, TarotReadingModel reading) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: List.generate(
        reading.cards.length.clamp(0, 3),
        (i) {
          final card = reading.cards[i];
          return Column(
            children: [
              Text(
                reading.positionLabels[i],
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: CosmoColors.primary,
                      letterSpacing: 1.2,
                    ),
              ),
              const SizedBox(height: 8),
              FlipCardWidget(
                isFlipped: _flipped[i],
                isReversed: card.isReversed,
                cardName: card.name,
                cardImagePath: TarotCardImageHelper.imagePath(card),
                onTap: () => setState(() => _flipped[i] = true),
              ),
              if (_flipped[i]) ...[
                const SizedBox(height: 6),
                SizedBox(
                  width: 90,
                  child: Text(
                    card.name,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: CosmoColors.textPrimary,
                          fontSize: 10,
                        ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (card.isReversed)
                  Text(
                    '(invertida)',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: CosmoColors.textSecondary,
                          fontSize: 9,
                        ),
                  ),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _buildInterpretation(BuildContext context, String text) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.auto_awesome,
                    color: CosmoColors.primary, size: 18),
                const SizedBox(width: 8),
                Text(
                  'Interpretación',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: CosmoColors.primary,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              text,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    height: 1.8,
                    color: CosmoColors.textPrimary,
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAskTarotist(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.chat_bubble_outline,
                    color: CosmoColors.secondary, size: 18),
                const SizedBox(width: 8),
                Text(
                  'Pregunta al Tarotista',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: CosmoColors.secondary,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _questionController,
              style: const TextStyle(color: CosmoColors.textPrimary),
              decoration: const InputDecoration(
                hintText: '¿Qué quieres saber?',
                hintStyle: TextStyle(color: CosmoColors.textSecondary),
              ),
              maxLength: 500,
              maxLines: 3,
              minLines: 1,
            ),
            if (_askError != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _askError!,
                  style: const TextStyle(color: CosmoColors.error, fontSize: 12),
                ),
              ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: _isAsking ? null : _askTarotist,
                child: _isAsking
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: CosmoColors.primary,
                        ),
                      )
                    : const Text('Preguntar'),
              ),
            ),
            if (_aiAnswer != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  color: CosmoColors.secondary.withOpacity(0.1),
                  border: Border.all(
                      color: CosmoColors.secondary.withOpacity(0.3)),
                ),
                child: Text(
                  _aiAnswer!,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        height: 1.7,
                        color: CosmoColors.textPrimary,
                      ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
