"""
Astrology service — zodiac sign calculation, characteristics, and compatibility.
All logic is pure Python with no external dependencies (easy to test).
"""
import json
from datetime import date
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"

# (month, day) upper boundary → sign name
# Ordered so the first entry whose (month, day) >= birth (month, day) is the sign.
_ZODIAC_BOUNDARIES: list[tuple[tuple[int, int], str]] = [
    ((1, 19), "Capricorn"),
    ((2, 18), "Aquarius"),
    ((3, 20), "Pisces"),
    ((4, 19), "Aries"),
    ((5, 20), "Taurus"),
    ((6, 20), "Gemini"),
    ((7, 22), "Cancer"),
    ((8, 22), "Leo"),
    ((9, 22), "Virgo"),
    ((10, 22), "Libra"),
    ((11, 21), "Scorpio"),
    ((12, 21), "Sagittarius"),
    ((12, 31), "Capricorn"),
]


def _load_zodiac_data() -> dict:
    path = _DATA_DIR / "zodiac_signs.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


_ZODIAC_DATA: dict = _load_zodiac_data()

# Element compatibility scores (same element = high, complementary = medium, etc.)
_ELEMENT_COMPAT: dict[tuple[str, str], int] = {
    ("fire", "fire"): 85,
    ("earth", "earth"): 85,
    ("air", "air"): 85,
    ("water", "water"): 85,
    ("fire", "air"): 80,
    ("air", "fire"): 80,
    ("earth", "water"): 80,
    ("water", "earth"): 80,
    ("fire", "earth"): 50,
    ("earth", "fire"): 50,
    ("air", "water"): 50,
    ("water", "air"): 50,
    ("fire", "water"): 35,
    ("water", "fire"): 35,
    ("earth", "air"): 35,
    ("air", "earth"): 35,
}


def get_zodiac_sign(birth_date: date) -> str:
    """Return the Western zodiac sign for a given birth date."""
    md = (birth_date.month, birth_date.day)
    for (cutoff_month, cutoff_day), sign in _ZODIAC_BOUNDARIES:
        if md <= (cutoff_month, cutoff_day):
            return sign
    return "Capricorn"  # fallback (should never be reached)


def get_sign_info(sign: str) -> dict | None:
    """Return the full info dict for a zodiac sign, or None if not found."""
    return _ZODIAC_DATA.get(sign)


def get_sign_element(sign: str) -> str | None:
    """Return the element ('fire', 'earth', 'air', 'water') for a sign."""
    info = _ZODIAC_DATA.get(sign)
    return info["element"] if info else None


def calculate_compatibility(sign_a: str, sign_b: str) -> dict:
    """
    Calculate compatibility between two zodiac signs.

    Returns a dict with:
      - score: int (1–100)
      - level: str ('excellent' | 'good' | 'moderate' | 'challenging')
      - description_en: str
      - description_es: str
    """
    info_a = _ZODIAC_DATA.get(sign_a)
    info_b = _ZODIAC_DATA.get(sign_b)

    if not info_a or not info_b:
        raise ValueError(f"Unknown zodiac sign(s): {sign_a!r}, {sign_b!r}")

    # Base score from element harmony
    elem_a = info_a["element"]
    elem_b = info_b["element"]
    base_score = _ELEMENT_COMPAT.get((elem_a, elem_b), 50)

    # Bonus: traditional compatible pairs listed in the data
    if sign_b in info_a.get("compatible_signs", []):
        base_score = min(100, base_score + 10)

    # Penalty: known incompatible pairs
    if sign_b in info_a.get("incompatible_signs", []):
        base_score = max(1, base_score - 15)

    # Same sign
    if sign_a == sign_b:
        base_score = 75  # strong connection but potential mirroring issues

    score = base_score

    if score >= 80:
        level = "excellent"
        desc_en = (
            f"{sign_a} and {sign_b} share a powerful natural harmony. "
            "Your connection flows with ease and mutual understanding."
        )
        desc_es = (
            f"{sign_a} y {sign_b} comparten una poderosa armonía natural. "
            "Su conexión fluye con facilidad y comprensión mutua."
        )
    elif score >= 65:
        level = "good"
        desc_en = (
            f"{sign_a} and {sign_b} complement each other well. "
            "With openness and communication, this bond can flourish."
        )
        desc_es = (
            f"{sign_a} y {sign_b} se complementan bien. "
            "Con apertura y comunicación, este vínculo puede florecer."
        )
    elif score >= 45:
        level = "moderate"
        desc_en = (
            f"{sign_a} and {sign_b} approach life differently, but differences can spark growth. "
            "Patience and curiosity will carry you far."
        )
        desc_es = (
            f"{sign_a} y {sign_b} se acercan a la vida de manera diferente, "
            "pero las diferencias pueden impulsar el crecimiento. "
            "La paciencia y la curiosidad los llevarán lejos."
        )
    else:
        level = "challenging"
        desc_en = (
            f"{sign_a} and {sign_b} navigate opposing energies. "
            "This pairing demands conscious effort, but can forge remarkable depth."
        )
        desc_es = (
            f"{sign_a} y {sign_b} navegan energías opuestas. "
            "Esta combinación exige esfuerzo consciente, pero puede forjar una profundidad notable."
        )

    return {
        "sign_a": sign_a,
        "sign_b": sign_b,
        "score": score,
        "level": level,
        "element_a": elem_a,
        "element_b": elem_b,
        "description_en": desc_en,
        "description_es": desc_es,
    }


VALID_SIGNS: frozenset[str] = frozenset(_ZODIAC_DATA.keys())
