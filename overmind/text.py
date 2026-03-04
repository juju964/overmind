from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter
from typing import Iterable

_WORD_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9]{2,}")
_STOPWORDS = {
    "the", "and", "for", "that", "with", "from", "this", "are", "was", "were", "have", "has",
    "you", "your", "sur", "les", "des", "pour", "dans", "avec", "une", "est", "pas", "mais",
    "plus", "tout", "dont", "par", "que", "qui", "du", "le", "la", "de", "et", "en", "un",
}


def clean_html(raw_html: str) -> str:
    text = re.sub(r"<script.*?>.*?</script>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    tokens = [normalize(m.group()) for m in _WORD_RE.finditer(text)]
    return [t for t in tokens if t not in _STOPWORDS]


def term_freq(tokens: Iterable[str]) -> Counter[str]:
    return Counter(tokens)


def detect_language(text: str) -> str:
    sample = normalize(text)
    fr_hits = sum(word in sample for word in (" le ", " la ", " les ", " des ", " est ", " pas "))
    en_hits = sum(word in sample for word in (" the ", " and ", " is ", " are ", " with ", " for "))
    if fr_hits > en_hits:
        return "fr"
    if en_hits > fr_hits:
        return "en"
    return "unknown"
