class TarotCard {
  const TarotCard({
    required this.name,
    required this.arcana,
    required this.orientation,
    this.suit,
    this.keywords = const [],
  });

  factory TarotCard.fromJson(Map<String, dynamic> json) => TarotCard(
        name: json['name'] as String? ?? '',
        arcana: json['arcana'] as String? ?? '',
        orientation: json['orientation'] as String? ?? 'upright',
        suit: json['suit'] as String?,
        keywords: (json['keywords'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ??
            [],
      );

  final String name;
  final String arcana;
  final String orientation;
  final String? suit;
  final List<String> keywords;

  bool get isReversed => orientation == 'reversed';
}

class TarotReadingModel {
  const TarotReadingModel({
    required this.id,
    required this.cards,
    required this.aiInterpretation,
    required this.readingDate,
    required this.spreadType,
  });

  factory TarotReadingModel.fromJson(Map<String, dynamic> json) {
    final cardsRaw =
        (json['cards_drawn'] as List<dynamic>?) ?? [];
    return TarotReadingModel(
      id: json['id'] as String? ?? '',
      cards: cardsRaw
          .map((c) => TarotCard.fromJson(c as Map<String, dynamic>))
          .toList(),
      aiInterpretation: json['ai_interpretation'] as String? ?? '',
      readingDate: json['reading_date'] as String? ?? '',
      spreadType: json['spread_type'] as String? ?? 'past_present_future',
    );
  }

  final String id;
  final List<TarotCard> cards;
  final String aiInterpretation;
  final String readingDate;
  final String spreadType;

  List<String> get positionLabels {
    if (spreadType == 'situation_action_outcome') {
      return ['Situación', 'Acción', 'Resultado'];
    }
    return ['Pasado', 'Presente', 'Futuro'];
  }
}
