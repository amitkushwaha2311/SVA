"""
SVA Ambiguity Engine IDs
========================

Deterministic ID generation for ambiguity tracking.
"""

import hashlib


def generate_ambiguity_id(repository_id: str, statement: str) -> str:
    """Generate a stable ID for an ambiguity case."""
    return hashlib.sha256(f"{repository_id}:{statement}".encode("utf-8")).hexdigest()


def generate_interpretation_id(ambiguity_id: str, statement: str) -> str:
    """Generate a stable ID for an interpretation."""
    return hashlib.sha256(f"{ambiguity_id}:{statement}".encode("utf-8")).hexdigest()


def generate_scenario_id(ambiguity_id: str, description: str) -> str:
    """Generate a stable ID for a distinguishing scenario."""
    return hashlib.sha256(f"{ambiguity_id}:{description}".encode("utf-8")).hexdigest()


def generate_question_id(ambiguity_id: str, question: str) -> str:
    """Generate a stable ID for a clarification question."""
    return hashlib.sha256(f"{ambiguity_id}:{question}".encode("utf-8")).hexdigest()
