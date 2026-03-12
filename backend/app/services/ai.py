"""
AI service — Google Gemini 2.0 Flash integration.

Uses the current google-genai SDK (google.genai).
All user input is sanitized before reaching this layer.
No PII is sent to Gemini: only zodiac sign, card names/keywords,
anonymized questions, and language preference.
"""
import logging
import time

from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from app.config import settings
from app.security.sanitizer import sanitize_input, SanitizationError

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
_MODEL_NAME = "gemini-2.0-flash"
_TIMEOUT_SECONDS = 30
_MAX_RETRIES = 2
_RETRY_BASE_DELAY = 2.0  # seconds, doubles on each retry

# ── Fallback messages (bilingual) ─────────────────────────────────────────────
_FALLBACKS = {
    "tarot": {
        "es": (
            "Las estrellas guardan silencio en este momento. "
            "Las cartas revelan que el universo te pide pausa y reflexión. "
            "Confía en tu intuición — ella conoce el camino."
        ),
        "en": (
            "The stars are silent right now. "
            "The cards reveal that the universe asks you to pause and reflect. "
            "Trust your intuition — it knows the way."
        ),
    },
    "horoscope": {
        "es": (
            "El cosmos se encuentra en transición. "
            "Hoy es un día para la introspección y la paciencia. "
            "Las energías se alinean en tu favor — mantente abierto a lo inesperado."
        ),
        "en": (
            "The cosmos is in transition. "
            "Today is a day for introspection and patience. "
            "Energies are aligning in your favor — stay open to the unexpected."
        ),
    },
    "compatibility": {
        "es": (
            "El universo contempla esta unión con interés. "
            "Toda relación es un espejo del alma. "
            "La clave está en la comunicación honesta y el respeto mutuo."
        ),
        "en": (
            "The universe contemplates this union with interest. "
            "Every relationship is a mirror of the soul. "
            "The key lies in honest communication and mutual respect."
        ),
    },
}


# ── Personality system prompts ────────────────────────────────────────────────
def _build_system_prompt(onboarding_answers: dict | None, language: str) -> str:
    """
    Build a personality-aware system prompt based on the user's onboarding answers.

    onboarding_answers keys:
      - reading_style: "direct" | "reflective" | "poetic"
      - destiny_view: "everything_is_written" | "you_decide" | "balance"
    """
    answers = onboarding_answers or {}
    style = answers.get("reading_style", "reflective")
    destiny = answers.get("destiny_view", "balance")

    style_instructions = {
        "direct": (
            "Speak directly and honestly. No metaphors — clear, practical insights."
            if language == "en"
            else "Habla de forma directa y honesta. Sin metáforas — perspectivas claras y prácticas."
        ),
        "reflective": (
            "Speak with warmth and depth. Ask gentle questions that invite self-reflection."
            if language == "en"
            else "Habla con calidez y profundidad. Haz preguntas suaves que inviten a la reflexión personal."
        ),
        "poetic": (
            "Speak in lyrical, evocative language. Use imagery, metaphor, and a sense of mystery."
            if language == "en"
            else "Habla con lenguaje lírico y evocador. Usa imágenes, metáforas y un sentido de misterio."
        ),
    }

    destiny_instructions = {
        "everything_is_written": (
            "Frame insights as revelations of what is already unfolding."
            if language == "en"
            else "Enmarca las perspectivas como revelaciones de lo que ya se está desarrollando."
        ),
        "you_decide": (
            "Emphasize free will and the power of choice in shaping outcomes."
            if language == "en"
            else "Enfatiza el libre albedrío y el poder de la elección para moldear los resultados."
        ),
        "balance": (
            "Acknowledge both fate and free will — destiny as a dance between the two."
            if language == "en"
            else "Reconoce tanto el destino como el libre albedrío — el destino como una danza entre los dos."
        ),
    }

    if language == "en":
        base = (
            "You are CosmoTarot, a wise and compassionate mystical guide. "
            "You offer tarot readings, horoscopes, and spiritual guidance. "
            "Keep responses focused and meaningful — 150 to 250 words. "
            "Never claim to predict the future with certainty. "
            "Never give medical, legal, or financial advice. "
        )
    else:
        base = (
            "Eres CosmoTarot, una guía mística sabia y compasiva. "
            "Ofreces lecturas de tarot, horóscopos y orientación espiritual. "
            "Mantén las respuestas enfocadas y significativas — entre 150 y 250 palabras. "
            "Nunca afirmes predecir el futuro con certeza. "
            "Nunca des consejos médicos, legales o financieros. "
        )

    return (
        base
        + style_instructions.get(style, style_instructions["reflective"])
        + " "
        + destiny_instructions.get(destiny, destiny_instructions["balance"])
    )


# ── Gemini client factory ─────────────────────────────────────────────────────
def _get_client() -> genai.Client:
    """Return a configured Gemini client."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


# ── Core generation helper ─────────────────────────────────────────────────────
def _generate_with_retry(prompt: str, system_prompt: str) -> str | None:
    """
    Call Gemini with exponential backoff on rate-limit errors.
    Returns the text response or None on unrecoverable failure.
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.85,
        max_output_tokens=400,
    )
    delay = _RETRY_BASE_DELAY

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=prompt,
                config=config,
            )
            text = response.text.strip() if response.text else ""
            return text if text else None

        except ResourceExhausted:
            if attempt < _MAX_RETRIES:
                logger.warning("Gemini rate limit hit, retrying in %.1fs", delay)
                time.sleep(delay)
                delay *= 2
            else:
                logger.error("Gemini rate limit exceeded after %d retries", _MAX_RETRIES)
                return None

        except ServiceUnavailable:
            logger.error("Gemini service unavailable")
            return None

        except TimeoutError:
            logger.error("Gemini request timed out")
            return None

        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected Gemini error: %s", exc)
            return None

    return None


# ── Public API ────────────────────────────────────────────────────────────────

def generate_tarot_interpretation(
    cards: list[dict],
    spread_type: str,
    question: str | None,
    zodiac_sign: str,
    language: str,
    onboarding_answers: dict | None = None,
) -> str:
    """
    Generate a personalized AI interpretation for a 3-card tarot spread.

    No PII is sent — only zodiac sign, card names/keywords, and the
    sanitized question (max 500 chars).
    """
    lang = language if language in ("en", "es") else "es"
    system_prompt = _build_system_prompt(onboarding_answers, lang)

    # Sanitize the question before including it in the prompt
    clean_question: str | None = None
    if question:
        try:
            clean_question = sanitize_input(question, max_length=500)
        except SanitizationError:
            logger.warning("Tarot question blocked by sanitizer")
            clean_question = None

    # Build the card summary — no PII, only card metadata
    card_lines = []
    for card in cards:
        orientation = card.get("orientation", "upright")
        position = card.get("position", f"card {card.get('position_index', 0) + 1}")
        name = card.get("name") if lang == "en" else card.get("name_es", card.get("name"))
        keywords_key = f"keywords_{lang}"
        keywords = ", ".join(card.get(keywords_key, card.get("keywords_en", [])))
        card_lines.append(f"- {position.upper()}: {name} ({orientation}) — {keywords}")

    cards_text = "\n".join(card_lines)

    if lang == "en":
        prompt = (
            f"Spread type: {spread_type.replace('_', ' ')}\n"
            f"Querent's zodiac sign: {zodiac_sign}\n"
            f"Cards drawn:\n{cards_text}\n"
        )
        if clean_question:
            prompt += f"Question: {clean_question}\n"
        prompt += "\nProvide a cohesive interpretation of this spread."
    else:
        prompt = (
            f"Tipo de tirada: {spread_type.replace('_', ' ')}\n"
            f"Signo zodiacal del consultante: {zodiac_sign}\n"
            f"Cartas sacadas:\n{cards_text}\n"
        )
        if clean_question:
            prompt += f"Pregunta: {clean_question}\n"
        prompt += "\nProporciona una interpretación coherente de esta tirada."

    result = _generate_with_retry(prompt, system_prompt)
    if not result:
        return _FALLBACKS["tarot"][lang]
    return result


def generate_daily_horoscope(
    zodiac_sign: str,
    current_date: str,
    language: str,
    onboarding_answers: dict | None = None,
) -> str:
    """
    Generate a daily horoscope for a zodiac sign.
    `current_date` should be ISO format (YYYY-MM-DD).
    """
    lang = language if language in ("en", "es") else "es"
    system_prompt = _build_system_prompt(onboarding_answers, lang)

    if lang == "en":
        prompt = (
            f"Write a daily horoscope for {zodiac_sign} on {current_date}. "
            "Cover energy, relationships, and one area to focus on today."
        )
    else:
        prompt = (
            f"Escribe el horóscopo diario para {zodiac_sign} el {current_date}. "
            "Cubre la energía, las relaciones y un área en la que enfocarse hoy."
        )

    result = _generate_with_retry(prompt, system_prompt)
    if not result:
        return _FALLBACKS["horoscope"][lang]
    return result


def generate_compatibility_analysis(
    sign_a: str,
    sign_b: str,
    score: int,
    level: str,
    element_a: str,
    element_b: str,
    language: str,
    onboarding_answers: dict | None = None,
) -> str:
    """
    Generate a narrative compatibility analysis between two zodiac signs.
    Numeric score and level are pre-calculated by the astrology service.
    """
    lang = language if language in ("en", "es") else "es"
    system_prompt = _build_system_prompt(onboarding_answers, lang)

    if lang == "en":
        prompt = (
            f"Write a compatibility reading for {sign_a} ({element_a}) and {sign_b} ({element_b}). "
            f"Their compatibility score is {score}/100 ({level}). "
            "Explore what unites them, what challenges them, and what they can build together."
        )
    else:
        prompt = (
            f"Escribe una lectura de compatibilidad para {sign_a} ({element_a}) y {sign_b} ({element_b}). "
            f"Su puntuación de compatibilidad es {score}/100 ({level}). "
            "Explora lo que los une, lo que los desafía y lo que pueden construir juntos."
        )

    result = _generate_with_retry(prompt, system_prompt)
    if not result:
        return _FALLBACKS["compatibility"][lang]
    return result


def answer_tarotist_question(
    question: str,
    zodiac_sign: str,
    language: str,
    onboarding_answers: dict | None = None,
) -> str:
    """
    Answer a free-form question through the tarotist persona.
    Input is sanitized before being sent to Gemini.
    """
    lang = language if language in ("en", "es") else "es"
    system_prompt = _build_system_prompt(onboarding_answers, lang)

    try:
        clean_question = sanitize_input(question, max_length=500)
    except SanitizationError:
        logger.warning("Tarotist question blocked by sanitizer")
        return _FALLBACKS["tarot"][lang]

    if lang == "en":
        prompt = (
            f"The querent is a {zodiac_sign}. "
            f"They ask: {clean_question}\n"
            "Respond as CosmoTarot with insight, wisdom, and compassion."
        )
    else:
        prompt = (
            f"El consultante es {zodiac_sign}. "
            f"Pregunta: {clean_question}\n"
            "Responde como CosmoTarot con perspicacia, sabiduría y compasión."
        )

    result = _generate_with_retry(prompt, system_prompt)
    if not result:
        return _FALLBACKS["tarot"][lang]
    return result
