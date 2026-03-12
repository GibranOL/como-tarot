"""
Numerology service — Step 3 will flesh this out fully.
Stub provides calculate_life_number() needed by the auth service on registration.
"""
from datetime import date

MASTER_NUMBERS = {11, 22, 33}


def _reduce(n: int) -> int:
    """Reduce n to a single digit or a master number."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def calculate_life_number(birth_date: date) -> int:
    """
    Pythagorean life-path number from birth date.
    Example: 1990-07-25 → 1+9+9+0 + 0+7 + 2+5 = 33 (master number, not reduced).
    """
    digit_sum = (
        sum(int(d) for d in str(birth_date.year))
        + sum(int(d) for d in str(birth_date.month).zfill(2))
        + sum(int(d) for d in str(birth_date.day).zfill(2))
    )
    return _reduce(digit_sum)
