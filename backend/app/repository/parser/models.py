"""
SVA Code Entity Models
======================

Defines the core data structures for static code entity extraction.
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    """Types of code entities that can be extracted."""

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    EXPORT = "export"
    API_ROUTE = "api_route"
    DATABASE_MODEL = "database_model"
    TEST = "test"
    CONFIGURATION = "configuration"


@dataclass
class CodeEntity:
    """
    A statically extracted structural entity from source code.
    
    Includes deterministic identity and source location data.
    """

    entity_id: str
    repository_id: str
    analysis_id: str
    file_path: str
    entity_type: EntityType
    name: str
    start_line: int
    end_line: int
    language: str
    extraction_method: str
    extraction_status: str = "SUCCESS"

    parent_entity_id: str | None = None
    
    # Contextual structural evidence (e.g., HTTP method for routes, decorator names)
    evidence: dict[str, Any] = field(default_factory=dict)


def generate_entity_id(
    repository_id: str,
    file_path: str,
    entity_type: EntityType,
    name: str,
    start_line: int,
) -> str:
    """
    Generate a deterministic, stable ID for a code entity.
    
    Relies purely on structural location and identity, avoiding timestamps
    or random UUIDs.
    """
    identity_string = f"{repository_id}:{file_path}:{entity_type.value}:{name}:{start_line}"
    return hashlib.sha256(identity_string.encode("utf-8")).hexdigest()
