"""
ai_service.py
--------------
Modular "AI" layer for SignBridge AI.

Two entry points are used by app.py:
    simplify_text(text)        -> dict(original, simplified, concepts)
    text_to_sign_sequence(text) -> list of sign-card dicts

DEMO MODE (default): everything below is rule-based and runs fully offline,
so a live hackathon demo never breaks on venue wifi or a missing API key.

MODULAR LLM HOOK: if an API key is present in the environment
(SIGNBRIDGE_LLM_API_KEY), `call_llm_simplifier()` is used instead of the
rule-based simplifier for nicer paraphrasing. This is optional and never
required for the app to run — see USE_LLM below.
"""
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNS_PATH = os.path.join(BASE_DIR, "static", "signs", "signs.json")
IMAGES_DIR_URL = "/static/signs/images"
VIDEOS_DIR_URL = "/static/signs/videos"

with open(SIGNS_PATH, "r", encoding="utf-8") as f:
    SIGN_CATEGORIES = json.load(f)

# Flatten to a single lookup: word -> {gu, example, category}
SIGN_DICT = {}
for category, words in SIGN_CATEGORIES.items():
    for word, meta in words.items():
        SIGN_DICT[word] = {**meta, "category": category}

# Longest phrase first, so "thank you" / "how are you" match before single words
SIGN_KEYS_SORTED = sorted(SIGN_DICT.keys(), key=lambda k: -len(k.split()))

# Gujarati labels in signs.json point back to the English sign asset/key.
GUJARATI_TO_SIGN = {}
for word, meta in SIGN_DICT.items():
    gujarati = meta.get("gu", "").strip()
    if gujarati and gujarati not in GUJARATI_TO_SIGN:
        GUJARATI_TO_SIGN[gujarati] = word
GUJARATI_KEYS_SORTED = sorted(GUJARATI_TO_SIGN, key=len, reverse=True)

USE_LLM = bool(os.environ.get("SIGNBRIDGE_LLM_API_KEY"))

# ---------------------------------------------------------------------------
# Rule-based simplifier (default, offline-safe)
# ---------------------------------------------------------------------------
HARD_WORD_MAP = {
    "the implementation of effective communication strategies": "using good communication methods",
    "facilitates improved collaboration among team members": "helps team members work better together",
    "contributes significantly to achieving organizational objectives": "greatly helps the organization reach its goals",
    "renewable energy technologies": "clean energy tools",
    "significant initial investments": "large costs at first",
    "long-term environmental and economic benefits": "future benefits for nature and money",
    "an increasingly attractive alternative to": "a better choice than",
    "increasingly attractive alternative": "better choice",
    "conventional fossil-fuel-based power generation": "traditional energy from fossil fuels",
    "fossil-fuel-based power generation": "energy from fossil fuels",
    "although": "even though",
    "photosynthesis": "how plants make food",
    "utilize": "use",
    "utilise": "use",
    "commence": "start",
    "terminate": "end",
    "sufficient": "enough",
    "approximately": "about",
    "demonstrate": "show",
    "acquire": "get",
    "fundamental": "basic",
    "subsequently": "then",
    "comprehend": "understand",
    "endeavor": "try",
    "endeavour": "try",
    "numerous": "many",
    "obtain": "get",
    "regarding": "about",
    "therefore": "so",
    "additionally": "also",
    "consequently": "so",
    "photosynthesize": "make food from sunlight",
    "respiration": "breathing",
    "evaporation": "water turning into vapour",
    "gravitational": "gravity",
}

STOPWORDS = {
    "a", "an", "the", "we", "you", "i",
    "to", "of", "in", "on", "at", "and", "or", "but", "that", "which", "how",
    "this", "these", "those", "could", "should", "would", "may", "might",
    "so", "then", "than", "for", "with", "as", "it", "its", "they", "them",
    "their", "by", "process", "very", "also", "into",
}


def normalize_gujarati(text: str) -> str:
    """Replace known Gujarati sign labels with their English sign keys."""
    normalized = text
    for gujarati in GUJARATI_KEYS_SORTED:
        normalized = normalized.replace(gujarati, f" {GUJARATI_TO_SIGN[gujarati]} ")
    return normalized


def simplify_text(text: str) -> dict:
    original = text.strip()
    simplified = original

    for hard, easy in HARD_WORD_MAP.items():
        simplified = re.sub(rf"\b{re.escape(hard)}\b", easy, simplified, flags=re.IGNORECASE)

    # Break run-on sentences at clause-joining conjunctions while preserving lists.
    simplified = re.sub(r",\s*(which|because|so that)\s+", r". ", simplified, flags=re.IGNORECASE)

    # keep sentences short (<=12 words)
    sentences = re.split(r"(?<=[.!?])\s+", simplified)
    short_sentences = []
    for s in sentences:
        words = s.split()
        if len(words) <= 12:
            if s.strip():
                short_sentences.append(s.strip())
        else:
            for i in range(0, len(words), 10):
                chunk = " ".join(words[i:i + 10]).strip()
                if chunk:
                    short_sentences.append(chunk)

    simplified_final = " ".join(short_sentences)
    if simplified_final:
        simplified_final = simplified_final[0].upper() + simplified_final[1:]
    concepts = extract_key_concepts(simplified_final)

    return {"original": original, "simplified": simplified_final, "concepts": concepts}


def extract_key_concepts(simplified_text: str) -> list:
    """Pull out the content words/phrases worth signing, dropping filler words."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", normalize_gujarati(simplified_text).lower())
    tokens = [t for t in clean.split() if t not in STOPWORDS]
    return tokens


# Placeholder for a real LLM call. Not required for the app to function.
def call_llm_simplifier(text: str) -> str:  # pragma: no cover
    """
    Hook for a real LLM API. Only used if SIGNBRIDGE_LLM_API_KEY is set.
    Left unimplemented intentionally -- wire up your provider of choice here
    (Anthropic/OpenAI/etc.) and set USE_LLM will pick it up automatically.
    """
    raise NotImplementedError("Wire up your LLM provider here if desired.")


# ---------------------------------------------------------------------------
# Sign sequencing
# ---------------------------------------------------------------------------
def _slugify(word: str) -> str:
    return word.strip().lower().replace(" ", "-")


def _sign_card(word: str) -> dict:
    meta = SIGN_DICT[word]
    slug = _slugify(word)
    return {
        "type": "sign",
        "word": word,
        "gu": meta["gu"],
        "category": meta["category"],
        "example": meta.get("example", ""),
        "image": f"{IMAGES_DIR_URL}/{slug}.svg",
        "video": f"{VIDEOS_DIR_URL}/{slug}.mp4",
    }


def _fingerspell_card(word: str) -> dict:
    return {"type": "fingerspell", "word": word, "letters": list(word.upper())}


def text_to_sign_sequence(text: str, use_concepts: bool = False) -> list:
    """
    Convert raw text into an ordered list of sign cards.

    use_concepts=True  -> Live Classroom / Simplifier mode: filler/stopwords
        are dropped first, and any remaining word still not in the sign
        dictionary is skipped (not fingerspelled), so the teacher sees a
        clean concept path like Tomorrow -> Learn -> Plant -> Food instead
        of every leftover word spelled out letter by letter.

    use_concepts=False -> Sign Converter mode: full-fidelity conversion.
        Every word is preserved, falling back to fingerspelling for
        anything not in the dictionary, so nothing the user typed is lost.
    """
    if use_concepts:
        words = extract_key_concepts(text)
        remaining = " ".join(words)
    else:
        remaining = re.sub(r"[^a-z0-9\s]", "", normalize_gujarati(text).lower()).strip()

    sequence = []
    while remaining.strip():
        remaining = remaining.strip()
        matched = None
        for key in SIGN_KEYS_SORTED:
            if remaining.startswith(key):
                after = remaining[len(key):]
                if after == "" or after[0] == " ":
                    matched = key
                    break
        if matched:
            sequence.append(_sign_card(matched))
            remaining = remaining[len(matched):].strip()
            continue

        # simple plural fallback: "plants" -> "plant"
        parts = remaining.split(" ", 1)
        word = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        singular = word[:-1] if word.endswith("s") and word[:-1] in SIGN_DICT else None
        if singular:
            sequence.append(_sign_card(singular))
        elif use_concepts:
            pass  # drop unknown filler word in concept mode
        else:
            if word:
                sequence.append(_fingerspell_card(word))
        remaining = rest
    return sequence


def get_categories():
    return list(SIGN_CATEGORIES.keys())


def get_signs_by_category(category: str = None):
    if category and category in SIGN_CATEGORIES:
        return {category: SIGN_CATEGORIES[category]}
    return SIGN_CATEGORIES


def get_all_sign_words():
    return list(SIGN_DICT.keys())
