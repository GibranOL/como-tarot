import '../../shared/models/tarot_reading_model.dart';

/// Maps a [TarotCard] to its corresponding WebP asset path.
///
/// Folder structure:
///   assets/images/Cartas_WebP_Ready/
///     Major Arcana/           → 00_the_fool.webp … 21_the_world.webp
///     Minor Arcana — Cups/    → 01_ace_of_cups.webp … 14_king_of_cups.webp
///     Minor Arcana — Pentacles/
///     Minor Arcana — Swords/
///     Minor Arcana — Wands/
///     Assets Especiales/      → card_back.webp, app_icon_draft.webp
class TarotCardImageHelper {
  static const _basePath = 'assets/images/Cartas_WebP_Ready';
  static const cardBackPath = '$_basePath/Assets Especiales/card_back.webp';

  /// Returns the asset path for the given [card], or [cardBackPath] if not found.
  static String imagePath(TarotCard card) {
    if (card.arcana == 'Major') {
      return _majorPath(card.name);
    }
    return _minorPath(card.name, card.suit ?? '');
  }

  // ── Major Arcana ──────────────────────────────────────────────────────────

  static const _majorFolder = '$_basePath/Major Arcana';

  static const _majorIndex = <String, String>{
    'The Fool': '00_the_fool',
    'The Magician': '01_the_magician',
    'The High Priestess': '02_the_high_priestess',
    'The Empress': '03_the_empress',
    'The Emperor': '04_the_emperor',
    'The Hierophant': '05_the_hierophant',
    'The Lovers': '06_the_lovers',
    'The Chariot': '07_the_chariot',
    'Strength': '08_strength',
    'The Hermit': '09_the_hermit',
    'Wheel of Fortune': '10_wheel_of_fortune',
    'Justice': '11_justice',
    'The Hanged Man': '12_the_hanged_man',
    'Death': '13_death',
    'Temperance': '14_temperance',
    'The Devil': '15_the_devil',
    'The Tower': '16_the_tower',
    'The Star': '17_the_star',
    'The Moon': '18_the_moon',
    'The Sun': '19_the_sun',
    'Judgement': '20_judgement',
    'The World': '21_the_world',
  };

  static String _majorPath(String cardName) {
    final file = _majorIndex[cardName];
    if (file == null) return cardBackPath;
    return '$_majorFolder/$file.webp';
  }

  // ── Minor Arcana ──────────────────────────────────────────────────────────

  static const _minorNumbers = <String, String>{
    'Ace': '01',
    'Two': '02',
    'Three': '03',
    'Four': '04',
    'Five': '05',
    'Six': '06',
    'Seven': '07',
    'Eight': '08',
    'Nine': '09',
    'Ten': '10',
    'Page': '11',
    'Knight': '12',
    'Queen': '13',
    'King': '14',
  };

  static String _minorPath(String cardName, String suit) {
    final folder = _suitFolder(suit);
    if (folder == null) return cardBackPath;

    // cardName format: "Ace of Cups", "King of Wands", "Seven of Swords" …
    final firstWord = cardName.split(' ').first;
    final number = _minorNumbers[firstWord];
    if (number == null) return cardBackPath;

    // Build file name: "07_seven_of_swords"
    final fileName =
        '${number}_${cardName.toLowerCase().replaceAll(' ', '_')}';
    return '$folder/$fileName.webp';
  }

  static String? _suitFolder(String suit) {
    switch (suit) {
      case 'Cups':
        return '$_basePath/Minor Arcana — Cups';
      case 'Pentacles':
        return '$_basePath/Minor Arcana — Pentacles';
      case 'Swords':
        return '$_basePath/Minor Arcana — Swords';
      case 'Wands':
        return '$_basePath/Minor Arcana — Wands';
      default:
        return null;
    }
  }
}
