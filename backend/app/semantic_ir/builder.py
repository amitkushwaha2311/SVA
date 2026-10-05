"""
SVA Semantic IR Builder
=======================

Constructs SemanticRequirement objects from IntentCandidates.
"""

import hashlib
import re
from dataclasses import dataclass

from app.repository.intent.models import IntentCandidate, Provenance
from app.repository.parser.models import CodeEntity, EntityType
from app.semantic_ir.ids import generate_semantic_requirement_id
from app.semantic_ir.models import (
    Action,
    Actor,
    Assumption,
    BehaviorState,
    CodeEntityRef,
    ImplementationState,
    IntentState,
    Resource,
    SemanticRequirement,
    VerificationState,
)
from app.semantic_ir.validator import SemanticIRValidator


# ---------------------------------------------------------------------------
# Private extraction helpers
# ---------------------------------------------------------------------------

@dataclass
class _ExtractedSemantics:
    """Value object returned by _extract_semantics; all fields are optional."""
    actor: Actor | None = None
    action: Action | None = None
    resource: Resource | None = None
    assumptions: list[Assumption] | None = None


# Pattern: "only <actor-phrase> can <verb> <object-phrase>"
# Examples:
#   "Only project owners can delete projects."
#   "Only admins can access the dashboard."
#   "Only account owners can modify account settings."
_ONLY_ACTOR_CAN_VERB_OBJECT = re.compile(
    r"""
    \bonly\s+
    (?P<actor_phrase>[a-z ]+?)\s+     # actor phrase, e.g. "project owners"
    can\s+
    (?P<verb>[a-z]+)\s+               # verb, e.g. "delete"
    (?P<object_phrase>[a-z ]+?)       # object phrase, e.g. "projects"
    \s*[.?!]?\s*$                     # trailing punctuation / end of string
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Conservative plural stripping: only strip a trailing 's' if the word is
# at least 5 chars long (avoids "as" → "a", "is" → "i", etc.).
def _depluralize(word: str) -> str:
    """Very conservative depluralization — strip trailing 's' only when safe."""
    if len(word) >= 5 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _normalize_actor_phrase(phrase: str) -> str:
    """
    Normalize an actor phrase extracted from 'only <phrase> can …'.

    Examples:
      "project owners"  → "project owner"
      "admins"          → "admin"
      "account owners"  → "account owner"
    """
    words = phrase.strip().split()
    # Depluralize the last word only (the head noun).
    if words:
        words[-1] = _depluralize(words[-1])
    return " ".join(words)


def _normalize_object_phrase(phrase: str) -> str:
    """
    Normalize an object phrase (resource name).

    Examples:
      "projects"          → "project"
      "account settings"  → "account setting"
    """
    words = phrase.strip().split()
    if words:
        words[-1] = _depluralize(words[-1])
    return " ".join(words)


def _build_ownership_assumption(
    actor_name: str,
    resource_name: str,
    provenance: Provenance,
) -> Assumption:
    """
    Build a conservative ownership assumption from actor and resource names.

    We derive the resource field reference from the resource name:
      actor="project owner", resource="project"
      → "owner = resource.owner_id"

    We always use the generic form "owner = resource.owner_id" rather than
    inventing model-specific field names that are not in the statement.
    """
    assumption_statement = "owner = resource.owner_id"
    assumption_id = hashlib.sha256(
        f"{actor_name}:{resource_name}:{assumption_statement}".encode()
    ).hexdigest()
    return Assumption(
        id=assumption_id,
        statement=assumption_statement,
        provenance=provenance,
    )


def _extract_semantics(statement: str, provenance: Provenance) -> _ExtractedSemantics:
    """
    Deterministic, rule-based extraction of actor/action/resource/assumptions.

    Only patterns that are clearly and unambiguously supported by the statement
    are extracted.  If the statement does not match a known safe pattern,
    all fields are returned as None/[].

    Rules:
    - No LLM.  No external calls.
    - Invented entities are forbidden.
    - Provenance is inherited from the caller.
    - If extraction is uncertain, None is returned for that field.
    """

    # ── Pattern 1: "Only <actor> can <verb> <object>" ──────────────────────
    m = _ONLY_ACTOR_CAN_VERB_OBJECT.match(statement.strip())
    if m:
        actor_phrase  = m.group("actor_phrase").strip()
        verb          = m.group("verb").strip()
        object_phrase = m.group("object_phrase").strip()

        # Reject if any capture is empty (safety guard)
        if not actor_phrase or not verb or not object_phrase:
            return _ExtractedSemantics()

        actor_name    = _normalize_actor_phrase(actor_phrase)
        resource_name = _normalize_object_phrase(object_phrase)

        actor    = Actor(name=actor_name)
        action   = Action(name=verb.lower())
        resource = Resource(name=resource_name)

        # Ownership assumption: present when actor phrase contains "owner"
        assumptions: list[Assumption] = []
        if "owner" in actor_phrase.lower():
            assumptions.append(
                _build_ownership_assumption(actor_name, resource_name, provenance)
            )

        return _ExtractedSemantics(
            actor=actor,
            action=action,
            resource=resource,
            assumptions=assumptions,
        )

    # ── No other patterns matched — return empty (conservative) ────────────
    return _ExtractedSemantics()


# ---------------------------------------------------------------------------
# Private reference resolution helpers
# ---------------------------------------------------------------------------

def _build_module_index(
    code_entities: list[CodeEntity],
) -> dict[str, CodeEntity]:
    """
    Build a lookup table: file_path → MODULE CodeEntity.

    Only MODULE entities are indexed.  Every source file has exactly one
    MODULE entity (structural identity), making this a 1-to-1 deterministic
    mapping.  No fuzzy matching is performed.
    """
    index: dict[str, CodeEntity] = {}
    for entity in code_entities:
        if entity.entity_type is EntityType.MODULE:
            # Last writer wins for duplicates; in practice there is only one
            # MODULE per file_path.
            index[entity.file_path] = entity
    return index


def _resolve_module_refs(
    candidate: IntentCandidate,
    module_index: dict[str, CodeEntity],
) -> list[CodeEntityRef]:
    """
    Resolve CodeEntityRefs from a candidate's SourceLocations.

    A ref is emitted if and only if:
      - The candidate has a SourceLocation whose ``path`` exactly matches a
        key in the MODULE index.

    This is the only deterministic relationship available without external
    metadata: source file path == MODULE entity file_path (exact string
    equality, no normalisation, no case-folding, no fuzzy matching).

    Duplicates are collapsed so that each entity_id appears at most once.
    """
    seen: set[str] = set()
    refs: list[CodeEntityRef] = []
    for source in candidate.sources:
        entity = module_index.get(source.path)
        if entity is not None and entity.entity_id not in seen:
            seen.add(entity.entity_id)
            refs.append(
                CodeEntityRef(
                    entity_id=entity.entity_id,
                    match_reason=(
                        "exact:source_path==module_file_path"
                        f":{source.path}"
                    ),
                )
            )
    return refs


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

class SemanticIRBuilder:
    """Safely constructs SemanticRequirements without inflating intent."""

    def __init__(self) -> None:
        self.validator = SemanticIRValidator()

    def build_from_candidate(
        self,
        repository_id: str,
        candidate: IntentCandidate,
        *,
        code_entities: list[CodeEntity] | None = None,
    ) -> SemanticRequirement:
        """
        Builds a conservative SemanticRequirement from a candidate.

        Semantic interpretation fields (actor, action, resource) are populated
        only when the statement matches a known, safe, rule-based pattern.
        If no pattern matches, they remain None, preserving the conservative
        behaviour of the original implementation.

        ``code_entities`` — when provided, the builder will attempt to resolve
        ``code_entity_refs`` via a deterministic MODULE-entity lookup (exact
        source-file path equality).  When absent the field stays empty.

        Does NOT set human_confirmed=True — that is a separate human-driven step.
        Does NOT call any LLM or external API.
        Does NOT perform fuzzy matching or name-based guessing.
        """

        # Use the normalized statement if available, otherwise the original
        statement = candidate.normalized_statement or candidate.original_statement

        req_id = generate_semantic_requirement_id(
            repository_id=repository_id,
            candidate_id=candidate.candidate_id,
            semantic_statement=statement,
        )

        # Map CandidateStatus to IntentState safely
        intent_state_map = {
            "CANDIDATE": IntentState.CANDIDATE,
            "CLARIFICATION_REQUIRED": IntentState.CLARIFICATION_REQUIRED,
            "REJECTED": IntentState.REJECTED,
        }
        mapped_intent_state = intent_state_map.get(candidate.status.value, IntentState.CANDIDATE)

        # Determine human confirmation
        # If the candidate was human confirmed, the intent state should be HUMAN_CONFIRMED
        if candidate.human_confirmed:
            mapped_intent_state = IntentState.HUMAN_CONFIRMED

        verification_state = VerificationState(
            intent=mapped_intent_state,
            implementation=ImplementationState.UNKNOWN,
            behavior=BehaviorState.UNKNOWN,
        )

        # ── Rule-based semantic extraction ──────────────────────────────────
        # Only populates fields when the statement matches a known safe pattern.
        # Provenance of extracted semantics is the same as the candidate's source.
        extracted = _extract_semantics(statement, candidate.provenance)

        # ── Deterministic MODULE-entity reference resolution ─────────────────
        # Emits a CodeEntityRef for each candidate source whose file path
        # exactly matches a MODULE entity in the supplied code_entities list.
        # No fuzzy matching; no entity creation; empty when code_entities is None.
        if code_entities:
            module_index = _build_module_index(code_entities)
            resolved_refs = _resolve_module_refs(candidate, module_index)
        else:
            resolved_refs = []

        req = SemanticRequirement(
            requirement_id=req_id,
            candidate_id=candidate.candidate_id,
            analysis_id=candidate.analysis_id,
            statement=statement,
            original_statement=candidate.original_statement,
            provenance=candidate.provenance,
            sources=list(candidate.sources),  # Create a copy of the list
            status=candidate.status,
            human_confirmed=candidate.human_confirmed,

            actor=extracted.actor,
            action=extracted.action,
            resource=extracted.resource,
            preconditions=[],
            postconditions=[],
            forbidden_behaviors=[],
            assumptions=extracted.assumptions or [],
            interpretation_notes=None,

            evidence_refs=[],
            code_entity_refs=resolved_refs,
            verification_state=verification_state,
        )

        # Validate the constructed object against strict boundaries
        self.validator.validate(req)

        return req

    def build_all(
        self,
        repository_id: str,
        candidates: list[IntentCandidate],
        *,
        code_entities: list[CodeEntity] | None = None,
    ) -> list[SemanticRequirement]:
        """Builds semantic requirements for a list of candidates.

        ``code_entities`` is forwarded to every ``build_from_candidate`` call;
        pass the full list once rather than per-candidate for efficiency.
        """
        # Build the MODULE index once for the whole batch.
        module_index: dict[str, CodeEntity] = (
            _build_module_index(code_entities) if code_entities else {}
        )
        reqs = []
        for c in candidates:
            # We don't resolve contradictions. Every candidate gets a SemanticRequirement.
            if module_index:
                resolved_refs = _resolve_module_refs(c, module_index)
                # Pass resolved refs directly to avoid re-building the index per call.
                req = self._build_from_candidate_with_refs(repository_id, c, resolved_refs)
            else:
                req = self.build_from_candidate(repository_id, c)
            reqs.append(req)
        return reqs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_from_candidate_with_refs(
        self,
        repository_id: str,
        candidate: IntentCandidate,
        code_entity_refs: list[CodeEntityRef],
    ) -> SemanticRequirement:
        """Internal path used by build_all to inject pre-resolved refs."""
        statement = candidate.normalized_statement or candidate.original_statement

        req_id = generate_semantic_requirement_id(
            repository_id=repository_id,
            candidate_id=candidate.candidate_id,
            semantic_statement=statement,
        )

        intent_state_map = {
            "CANDIDATE": IntentState.CANDIDATE,
            "CLARIFICATION_REQUIRED": IntentState.CLARIFICATION_REQUIRED,
            "REJECTED": IntentState.REJECTED,
        }
        mapped_intent_state = intent_state_map.get(candidate.status.value, IntentState.CANDIDATE)
        if candidate.human_confirmed:
            mapped_intent_state = IntentState.HUMAN_CONFIRMED

        verification_state = VerificationState(
            intent=mapped_intent_state,
            implementation=ImplementationState.UNKNOWN,
            behavior=BehaviorState.UNKNOWN,
        )

        extracted = _extract_semantics(statement, candidate.provenance)

        req = SemanticRequirement(
            requirement_id=req_id,
            candidate_id=candidate.candidate_id,
            analysis_id=candidate.analysis_id,
            statement=statement,
            original_statement=candidate.original_statement,
            provenance=candidate.provenance,
            sources=list(candidate.sources),
            status=candidate.status,
            human_confirmed=candidate.human_confirmed,
            actor=extracted.actor,
            action=extracted.action,
            resource=extracted.resource,
            preconditions=[],
            postconditions=[],
            forbidden_behaviors=[],
            assumptions=extracted.assumptions or [],
            interpretation_notes=None,
            evidence_refs=[],
            code_entity_refs=code_entity_refs,
            verification_state=verification_state,
        )

        self.validator.validate(req)
        return req
