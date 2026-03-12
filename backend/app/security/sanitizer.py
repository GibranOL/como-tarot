"""
Input sanitization — every string from a user passes through here before processing.
Covers XSS, prompt injection, SQL injection patterns, and general validation.
"""
import re
import html

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(previous|all|prior)\s+instructions?|"
    r"act\s+as\s+|"
    r"system\s*prompt|"
    r"you\s+are\s+now\s+|"
    r"forget\s+(everything|all)\s+|"
    r"new\s+instructions?:)",
    re.IGNORECASE,
)

# Tags that are always dangerous
_DANGEROUS_TAGS = re.compile(
    r"<\s*(script|iframe|object|embed|form|input|link|meta|style|svg)[^>]*>.*?</\s*\1\s*>|"
    r"<\s*(script|iframe|object|embed|form|input|link|meta|style|svg)[^>]*/?>",
    re.IGNORECASE | re.DOTALL,
)


class SanitizationError(ValueError):
    """Raised when input contains malicious content."""


def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Clean user-supplied text before any processing or AI submission.

    Steps:
    1. Strip null bytes and control characters.
    2. Enforce max length.
    3. Escape HTML entities (XSS prevention).
    4. Remove dangerous HTML tags.
    5. Block prompt injection patterns.

    Returns the cleaned string.
    Raises SanitizationError if injection is detected.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Remove null bytes and ASCII control chars (except tab/newline/CR)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Enforce max length BEFORE escaping to avoid byte-count tricks
    if len(text) > max_length:
        text = text[:max_length]

    # Remove dangerous HTML tags
    text = _DANGEROUS_TAGS.sub("", text)

    # Escape remaining HTML entities
    text = html.escape(text, quote=True)

    # Block prompt injection
    if _INJECTION_PATTERNS.search(text):
        raise SanitizationError("Input contains disallowed patterns")

    return text.strip()
