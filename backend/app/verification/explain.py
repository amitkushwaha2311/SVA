"""
SVA Verification Explanations
=============================

Deterministic explanation generation for verification decisions.
"""

from app.evidence.models import Evidence, VerificationState


def generate_obligation_explanation(
    obligation_id: str,
    decision: VerificationState,
    supporting: list[Evidence],
    contradicting: list[Evidence],
    stale: list[Evidence],
    invalid: list[Evidence],
) -> str:
    """Generate deterministic explanation for an obligation verification."""
    
    parts = []
    
    if decision == VerificationState.PROVEN:
        strongest = max(supporting, key=lambda e: e.evidence_type.value)
        parts.append(
            f"Obligation {obligation_id} is PROVEN because valid evidence (e.g., {strongest.evidence_id} - {strongest.evidence_type.value}) "
            f"satisfies the required behavior."
        )
    elif decision == VerificationState.SUPPORTED:
        parts.append(
            f"Obligation {obligation_id} is SUPPORTED by valid evidence, but the evidence strength "
            f"is insufficient to establish PROVEN."
        )
    elif decision == VerificationState.VIOLATED:
        first_violation = contradicting[0]
        parts.append(
            f"Obligation {obligation_id} is VIOLATED because evidence {first_violation.evidence_id} "
            f"observed behavior contradicting the obligation."
        )
    elif decision == VerificationState.INCONCLUSIVE:
        if contradicting and supporting:
            parts.append(
                f"Obligation {obligation_id} is INCONCLUSIVE because valid evidence contradicts itself "
                f"(e.g., {supporting[0].evidence_id} supports, but {contradicting[0].evidence_id} contradicts)."
            )
        else:
            parts.append(
                f"Obligation {obligation_id} is INCONCLUSIVE because available evidence is partial or resulted in error/timeout."
            )
    elif decision == VerificationState.UNKNOWN:
        parts.append(
            f"Obligation {obligation_id} is UNKNOWN because no valid, current evidence could verify the behavior."
        )

    # Note stale/invalid
    if stale:
        stale_e = stale[0]
        parts.append(
            f"Note: Evidence {stale_e.evidence_id} was generated for commit {stale_e.commit_id}, "
            f"but the current verification targets a different commit. The evidence is stale and cannot establish current behavior."
        )
    
    if invalid:
        parts.append(f"Note: {len(invalid)} evidence record(s) were excluded due to invalid integrity or repository mismatch.")

    return " ".join(parts)


def generate_requirement_explanation(
    requirement_id: str,
    decision: VerificationState,
    total_obligations: int,
    proven: int,
    violated: int,
    unresolved: int,
) -> str:
    """Generate deterministic explanation for a requirement verification."""
    
    if decision == VerificationState.PROVEN:
        return f"Requirement {requirement_id} is PROVEN because all {total_obligations} mandatory obligation(s) are PROVEN."
    
    if decision == VerificationState.VIOLATED:
        return f"Requirement {requirement_id} is VIOLATED because {violated} mandatory obligation(s) are VIOLATED."
    
    if decision == VerificationState.INCONCLUSIVE:
        return f"Requirement {requirement_id} is INCONCLUSIVE due to contradictory or inconclusive obligation results."
    
    if decision == VerificationState.SUPPORTED:
        return f"Requirement {requirement_id} is SUPPORTED because obligations have supporting evidence, but not all are PROVEN."
    
    return f"Requirement {requirement_id} is NOT PROVEN ({decision.value}). {unresolved} out of {total_obligations} mandatory obligation(s) remain unverified."
