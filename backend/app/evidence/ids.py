"""
SVA Evidence IDs
================

Deterministic ID generation for evidence items.
"""

import hashlib


def generate_evidence_id(
    repository_id: str,
    contract_id: str,
    evidence_type: str,
    description: str,
) -> str:
    """Generate a stable, deterministic evidence ID."""
    identity = f"{repository_id}:{contract_id}:{evidence_type}:{description}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def generate_obligation_id(contract_id: str, description: str) -> str:
    return hashlib.sha256(f"{contract_id}:obligation:{description}".encode()).hexdigest()


def generate_verification_result_id(contract_id: str) -> str:
    return hashlib.sha256(f"{contract_id}:verification_result".encode()).hexdigest()
