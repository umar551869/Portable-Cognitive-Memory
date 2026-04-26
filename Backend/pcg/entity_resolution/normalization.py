from __future__ import annotations

import re
import string


_PUNCT_TRANSLATION = str.maketrans("", "", string.punctuation)


def normalize(text: str) -> str:
    """Canonicalize text for deterministic entity identity checks."""

    normalized = text.lower().translate(_PUNCT_TRANSLATION)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
