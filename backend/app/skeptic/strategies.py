"""
SVA Skeptic Strategies
======================

Deterministic, rule-based counterexample generation strategies.

NO LLM is used here. All generation is grounded in the SemanticContract
structure and Phase 6 / Phase 10 models.
"""

from __future__ import annotations

from app.contracts.models import BehaviorExpectation, SemanticContract
from app.skeptic.models import (
    Counterexample,
    CounterexampleActor,
    CounterexamplePriority,
    CounterexampleStatus,
    SkepticStrategy,
    generate_counterexample_id,
)
from app.evidence.ids import generate_obligation_id

# Authorization keywords used to detect boundary-relevant obligations
_AUTH_KEYWORDS = frozenset([
    "owner", "authenticated", "authorized", "admin", "role",
    "permission", "access", "credential", "user", "member",
    "privileged", "unprivileged", "unauthenticated", "non-owner",
])

_INPUT_KEYWORDS = frozenset(["empty", "missing", "null", "invalid", "malformed", "boundary"])
_RESOURCE_KEYWORDS = frozenset(["resource", "project", "file", "entity", "object", "item", "record"])
_SCOPE_KEYWORDS = frozenset(["notification", "subscription", "category", "scope", "filter"])


def _has_auth_concepts(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _AUTH_KEYWORDS)


def _has_resource_concepts(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _RESOURCE_KEYWORDS)


def _has_scope_concepts(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in _SCOPE_KEYWORDS)


# ─────────────────────────────────────────────
# Individual strategy functions
# ─────────────────────────────────────────────

def strategy_negative_space(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    For every positive behavior, generate the corresponding negative-space challenge.
    Example: 'Owner can delete' → 'Can a non-owner delete?'
    """
    candidates = []

    desc = behavior.description
    action = behavior.action or "perform the operation"
    actor_hint = "non-owner" if "owner" in desc.lower() else "unauthorized user"

    canonical = f"NEGATIVE_SPACE:{obligation_id}:{actor_hint}:{action}"
    cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.NEGATIVE_SPACE.value, canonical)

    candidates.append(Counterexample(
        counterexample_id=cid,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"A {actor_hint} may be able to {action} even though the contract restricts this to privileged actors.",
        preconditions=["System is running", "Target resource exists"],
        actor=CounterexampleActor(role=actor_hint, is_authenticated=True, is_owner=False),
        action=action,
        resource="target resource",
        expected_behavior=f"The operation is denied for a {actor_hint}.",
        violating_behavior=f"The operation succeeds for a {actor_hint}.",
        strategy=SkepticStrategy.NEGATIVE_SPACE,
        priority=CounterexamplePriority.HIGH,
        priority_reason="Positive-only evidence does not verify the corresponding negative restriction.",
        assumptions=["The system enforces authorization at the API level."],
    ))
    return candidates


def strategy_authorization_boundary(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    Generate scenarios crossing authentication/authorization boundaries.
    """
    if not _has_auth_concepts(behavior.description):
        return []

    candidates = []
    action = behavior.action or "perform the operation"

    # Scenario 1: Unauthenticated user
    canonical_unauth = f"AUTH_BOUNDARY:UNAUTHENTICATED:{obligation_id}:{action}"
    cid_unauth = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.AUTHORIZATION_BOUNDARY.value, canonical_unauth)
    candidates.append(Counterexample(
        counterexample_id=cid_unauth,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"An unauthenticated user may be able to {action}.",
        preconditions=["Target resource exists", "No authentication token provided"],
        actor=CounterexampleActor(role="unauthenticated_user", is_authenticated=False, is_owner=False),
        action=action,
        resource="target resource",
        expected_behavior="The operation is rejected with an authentication error.",
        violating_behavior="The operation succeeds without authentication.",
        strategy=SkepticStrategy.AUTHORIZATION_BOUNDARY,
        priority=CounterexamplePriority.HIGH,
        priority_reason="Authorization requirements must be tested against unauthenticated actors.",
        assumptions=["Authentication is required per the contract."],
    ))

    # Scenario 2: Authenticated non-owner
    canonical_nonowner = f"AUTH_BOUNDARY:NON_OWNER:{obligation_id}:{action}"
    cid_nonowner = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.AUTHORIZATION_BOUNDARY.value, canonical_nonowner)
    candidates.append(Counterexample(
        counterexample_id=cid_nonowner,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"An authenticated non-owner may be able to {action}.",
        preconditions=["Target resource exists", "Valid auth token for non-owner"],
        actor=CounterexampleActor(role="authenticated_non_owner", is_authenticated=True, is_owner=False),
        action=action,
        resource="target resource",
        expected_behavior="The operation is rejected with a forbidden/authorization error.",
        violating_behavior="The operation succeeds for a non-owner.",
        strategy=SkepticStrategy.AUTHORIZATION_BOUNDARY,
        priority=CounterexamplePriority.HIGH,
        priority_reason="Authorization requirements must be tested against authenticated non-owners.",
        assumptions=["The system enforces owner-level restrictions."],
    ))

    return candidates


def strategy_input_boundary(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    Generate scenarios challenging input validation.
    """
    action = behavior.action or "perform the operation"

    canonical = f"INPUT_BOUNDARY:EMPTY:{obligation_id}:{action}"
    cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.INPUT_BOUNDARY.value, canonical)

    return [Counterexample(
        counterexample_id=cid,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"The system may not correctly handle missing or malformed input for {action}.",
        preconditions=["System is running"],
        actor=CounterexampleActor(role="any_actor", is_authenticated=True),
        action=action,
        resource="malformed/empty input payload",
        expected_behavior="The system rejects invalid input with a clear error.",
        violating_behavior="The system accepts or silently ignores invalid input, producing incorrect state.",
        strategy=SkepticStrategy.INPUT_BOUNDARY,
        priority=CounterexamplePriority.MEDIUM,
        priority_reason="Input validation must be explicitly verified.",
        assumptions=["The contract implies valid input handling."],
    )]


def strategy_resource_boundary(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    Generate scenarios challenging resource identity boundaries.
    Only applied when resource concepts are present in the contract.
    """
    if not _has_resource_concepts(behavior.description):
        return []

    action = behavior.action or "access the resource"
    canonical = f"RESOURCE_BOUNDARY:WRONG_OWNER:{obligation_id}:{action}"
    cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.RESOURCE_BOUNDARY.value, canonical)

    return [Counterexample(
        counterexample_id=cid,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"An actor may be able to {action} a resource belonging to a different owner.",
        preconditions=["Resource belonging to another user exists", "Valid auth token for requesting user"],
        actor=CounterexampleActor(role="authenticated_user", is_authenticated=True, is_owner=False),
        action=action,
        resource="resource owned by another user",
        expected_behavior="The operation is denied since the actor does not own this resource.",
        violating_behavior="The operation succeeds, exposing another user's resource.",
        strategy=SkepticStrategy.RESOURCE_BOUNDARY,
        priority=CounterexamplePriority.HIGH,
        priority_reason="Resource isolation must be independently verified.",
        assumptions=["Resources are scoped to their owners."],
    )]


def strategy_scope_boundary(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    Generate scenarios challenging scoping/subscription conditions.
    Only applied when scope concepts are present.
    """
    if not _has_scope_concepts(behavior.description):
        return []

    action = behavior.action or "receive the notification"
    canonical = f"SCOPE_BOUNDARY:EXCLUDED:{obligation_id}:{action}"
    cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.SCOPE_BOUNDARY.value, canonical)

    return [Counterexample(
        counterexample_id=cid,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"A user outside the defined scope may still {action}.",
        preconditions=["User lacks required subscription/membership", "Event occurs"],
        actor=CounterexampleActor(role="out_of_scope_user", is_authenticated=True),
        action=action,
        resource="scoped resource",
        expected_behavior="The out-of-scope user does not receive the action/notification.",
        violating_behavior="The out-of-scope user receives the action/notification.",
        strategy=SkepticStrategy.SCOPE_BOUNDARY,
        priority=CounterexamplePriority.MEDIUM,
        priority_reason="Scope boundaries must be validated against excluded actors.",
        assumptions=["Subscription or membership condition is defined."],
    )]


def strategy_condition_flipping(
    repository_id: str,
    contract: SemanticContract,
    behavior: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    For each contract-level precondition, generate a scenario
    where the condition is false/negated.
    """
    if not contract.preconditions:
        return []

    candidates = []
    action = behavior.action or "perform the operation"

    for precond in contract.preconditions[:3]:  # Limit to 3 per obligation
        canonical = f"CONDITION_FLIP:{obligation_id}:{precond}:{action}"
        cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.CONDITION_FLIPPING.value, canonical)

        candidates.append(Counterexample(
            counterexample_id=cid,
            requirement_id=contract.requirement_id,
            contract_id=contract.contract_id,
            obligation_id=obligation_id,
            hypothesis=f"The system may not correctly reject the operation when precondition '{precond}' is not met.",
            preconditions=[f"Precondition '{precond}' is FALSE"],
            actor=CounterexampleActor(role="any_actor", is_authenticated=True),
            action=action,
            resource="target resource",
            expected_behavior=f"The operation is rejected because '{precond}' is not satisfied.",
            violating_behavior=f"The operation succeeds even though '{precond}' is not satisfied.",
            strategy=SkepticStrategy.CONDITION_FLIPPING,
            priority=CounterexamplePriority.MEDIUM,
            priority_reason=f"Precondition '{precond}' has not been independently tested in its negated state.",
            assumptions=[f"'{precond}' can be made false in the test environment."],
        ))

    return candidates


def strategy_negative_obligation_challenge(
    repository_id: str,
    contract: SemanticContract,
    forbidden: BehaviorExpectation,
    obligation_id: str,
) -> list[Counterexample]:
    """
    For every forbidden behavior, construct a scenario that attempts to trigger it.
    """
    action = forbidden.action or "trigger the forbidden operation"
    canonical = f"NEG_OBL:{obligation_id}:{action}"
    cid = generate_counterexample_id(repository_id, contract.contract_id, obligation_id, SkepticStrategy.NEGATIVE_OBLIGATION_CHALLENGE.value, canonical)

    return [Counterexample(
        counterexample_id=cid,
        requirement_id=contract.requirement_id,
        contract_id=contract.contract_id,
        obligation_id=obligation_id,
        hypothesis=f"The system may not enforce the forbidden behavior: '{forbidden.description}'.",
        preconditions=["System is running", "Actor has valid credentials"],
        actor=CounterexampleActor(role="any_actor_attempting_forbidden", is_authenticated=True),
        action=action,
        resource="target resource",
        expected_behavior=f"The forbidden operation is blocked: '{forbidden.description}'.",
        violating_behavior=f"The forbidden operation succeeds: '{forbidden.description}'.",
        strategy=SkepticStrategy.NEGATIVE_OBLIGATION_CHALLENGE,
        priority=CounterexamplePriority.HIGH,
        priority_reason="Forbidden behaviors must have independent evidence confirming enforcement.",
        assumptions=["The system has a mechanism to block this operation."],
    )]
