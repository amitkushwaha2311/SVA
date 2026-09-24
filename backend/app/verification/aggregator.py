"""
SVA Verification Aggregator
===========================

Aggregates obligation results into a requirement result.
"""

from app.evidence.models import VerificationState
from app.verification.models import ObligationVerification


class RequirementAggregator:
    """
    Aggregates ObligationVerification results deterministically.
    
    Does NOT use simple enum precedence. Reasons about the complete set
    of mandatory obligations.
    """

    def aggregate(
        self,
        obligation_results: list[ObligationVerification]
    ) -> VerificationState:
        """
        Aggregate obligations into a single VerificationState.
        """
        if not obligation_results:
            return VerificationState.UNKNOWN
            
        states = [o.decision for o in obligation_results]
        
        # Any VIOLATED obligation means the requirement is VIOLATED.
        if VerificationState.VIOLATED in states:
            return VerificationState.VIOLATED
            
        # Contradictions / Inconclusive surface as INCONCLUSIVE
        if VerificationState.INCONCLUSIVE in states:
            return VerificationState.INCONCLUSIVE
            
        # If all obligations are PROVEN, requirement is PROVEN.
        if all(s == VerificationState.PROVEN for s in states):
            return VerificationState.PROVEN
            
        # If any obligation is UNKNOWN, and we aren't VIOLATED/INCONCLUSIVE,
        # then the requirement is not fully verified. It remains UNKNOWN.
        # This prevents partial success (1 PROVEN, 1 UNKNOWN) from becoming PROVEN.
        if VerificationState.UNKNOWN in states:
            return VerificationState.UNKNOWN
            
        # If we have a mix of SUPPORTED and PROVEN (but no UNKNOWN/VIOLATED/INCONCLUSIVE),
        # the requirement is SUPPORTED.
        if VerificationState.SUPPORTED in states:
            return VerificationState.SUPPORTED
            
        return VerificationState.UNKNOWN
