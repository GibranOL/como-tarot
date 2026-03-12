"""
Astrology service — Step 3 will flesh this out fully.
Stub provides get_zodiac_sign() which is needed by the auth service on registration.
"""
from datetime import date


# (month, day) boundaries → sign name
_ZODIAC = [
    ((1, 20), "Capricorn"),
    ((2, 19), "Aquarius"),
    ((3, 20), "Pisces"),
    ((4, 20), "Aries"),
    ((5, 21), "Taurus"),
    ((6, 21), "Gemini"),
    ((7, 22), "Cancer"),
    ((8, 23), "Leo"),
    ((9, 23), "Virgo"),
    ((10, 23), "Libra"),
    ((11, 22), "Scorpio"),
    ((12, 22), "Sagittarius"),
    ((12, 31), "Capricorn"),
]


def get_zodiac_sign(birth_date: date) -> str:
    """Return the Western zodiac sign for a given birth date."""
    md = (birth_date.month, birth_date.day)
    for (cutoff_month, cutoff_day), sign in _ZODIAC:
        if md <= (cutoff_month, cutoff_day):
            return sign
    return "Capricorn"  # Dec 22–31 fallback
