import re

def normalize_whitespace(text: str) -> str:
    """
    Normalizes a string by trimming leading/trailing whitespace,
    and reducing multiple inner whitespaces/newlines to a single space.
    """
    if not text:
        return ""
    # Replace all unicode whitespace (including newlines) with a single space
    normalized = re.sub(r'\s+', ' ', text)
    return normalized.strip()

def normalize_next_purpose(purpose: str) -> str:
    """
    Dedicated normalization layer for Next Purpose.
    Handles harmless formatting differences without merging semantically
    different values.
    """
    return normalize_whitespace(purpose)
