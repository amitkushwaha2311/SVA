"""
SVA Contract Normalization
==========================

Deterministic normalization of semantic contract fields.
"""

import re


def normalize_statement(statement: str) -> str:
    """
    Deterministically normalize a requirement statement for stable comparisons.

    Rules (applied in order):
    1. Strip leading/trailing whitespace.
    2. Collapse internal whitespace runs to a single space.
    3. Strip trailing punctuation.
    4. Lowercase.
    """
    s = statement.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.rstrip(".?!")
    return s.lower()


def normalize_actor(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw.strip().lower()


def normalize_action(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw.strip().lower()


def normalize_resource(raw: str | None) -> str | None:
    if raw is None:
        return None
    return raw.strip().lower()
