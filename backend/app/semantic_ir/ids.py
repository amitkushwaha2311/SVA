"""
SVA Semantic IR IDs
===================

Deterministic ID generation for Semantic Requirements.
"""

import hashlib


def generate_semantic_requirement_id(
    repository_id: str,
    candidate_id: str,
    semantic_statement: str,
) -> str:
    """
    Generate a deterministic, stable ID for a semantic requirement.
    
    The ID is derived from stable inputs: repository, the originating candidate,
    and the interpreted semantic statement.
    """
    identity_string = f"{repository_id}:{candidate_id}:{semantic_statement}"
    return hashlib.sha256(identity_string.encode("utf-8")).hexdigest()
