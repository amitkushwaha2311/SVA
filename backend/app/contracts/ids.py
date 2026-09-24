"""
SVA Contract IDs
================

Deterministic ID generation for semantic contracts.
"""

import hashlib


def generate_contract_id(
    repository_id: str,
    requirement_id: str,
    contract_version: str = "1",
) -> str:
    """
    Generate a stable, deterministic ID for a semantic contract.

    The version is included so that a materially changed requirement
    can produce a new contract ID, making the old one SUPERSEDED.
    """
    identity = f"{repository_id}:{requirement_id}:v{contract_version}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def generate_behavior_id(contract_id: str, description: str) -> str:
    return hashlib.sha256(f"{contract_id}:behavior:{description}".encode()).hexdigest()


def generate_invariant_id(contract_id: str, statement: str) -> str:
    return hashlib.sha256(f"{contract_id}:invariant:{statement}".encode()).hexdigest()


def generate_assumption_id(contract_id: str, statement: str) -> str:
    return hashlib.sha256(f"{contract_id}:assumption:{statement}".encode()).hexdigest()


def generate_target_id(contract_id: str, description: str) -> str:
    return hashlib.sha256(f"{contract_id}:target:{description}".encode()).hexdigest()
