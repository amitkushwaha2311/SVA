"""
SVA Semantic Drift Impact
=========================

Analyzes the impact of changes on the semantic assurance graph.
Traces relationships explicitly and marks missing links as UNKNOWN_RELATIONSHIP.
"""

from __future__ import annotations

from app.contracts.models import SemanticContract
from app.drift.models import (
    ChangeRecord,
    DriftType,
    SemanticImpact,
    generate_impact_id,
)
from app.evidence.graph import EvidenceGraph
from app.evidence.ids import generate_obligation_id
from app.repository.intent.models import IntentCandidate
from app.semantic_ir.models import SemanticRequirement


class ImpactAnalyzer:
    """Propagates changes through explicit semantic relationships."""

    def __init__(self, graph: EvidenceGraph | None = None) -> None:
        self.graph = graph or EvidenceGraph()

    def analyze(
        self,
        change: ChangeRecord,
        contracts: list[SemanticContract],
        requirements: list[SemanticRequirement],
        intent_candidates: list[IntentCandidate],
    ) -> list[SemanticImpact]:
        """
        Determine the semantic impact of a specific change.
        """
        impacts: list[SemanticImpact] = []
        
        # 1. Intent Source Impact
        # Check if the changed file is an intent source
        for req in requirements:
            for src in req.sources:
                if src.path == change.file_path:
                    # The source file for this requirement changed.
                    # We can't say the intent definitely changed without LLM/Human,
                    # so we record the structural impact.
                    impacts.append(self._create_impact(
                        change.change_id, "REQUIREMENT", req.requirement_id,
                        f"Intent source file {change.file_path} changed.",
                        affected_requirements=[req.requirement_id],
                        impact_type="DIRECT"
                    ))
                    
                    # Also flag this on the change record
                    change.drift_type = DriftType.INTENT
                    break
        
        # 2. Configuration Impact (Correction 1)
        if change.drift_type == DriftType.CONFIGURATION:
            has_explicit_relationship = False
            
            # Check requirements sources (done above implicitly, but we must check contracts/targets too)
            for req in requirements:
                if any(src.path == change.file_path for src in req.sources):
                    has_explicit_relationship = True
                    break
            
            for contract in contracts:
                if any(src.path == change.file_path for src in contract.source_refs):
                    has_explicit_relationship = True
                    impacts.append(self._create_impact(
                        change.change_id, "CONTRACT", contract.contract_id,
                        f"Configuration file {change.file_path} explicitly linked to contract changed.",
                        affected_contracts=[contract.contract_id],
                        impact_type="DIRECT"
                    ))
                    
                # Note: VerificationTarget might link to this config file if it has code_entity_ref
                # Since we don't have the full entity graph here directly without querying,
                # we assume if it's an entity change in a config, it might hit step 3.
            
            if not has_explicit_relationship:
                # We do NOT create an UNKNOWN_RELATIONSHIP here for every config file,
                # because the rule says "if no relationship found -> PASS".
                # But if we genuinely can't determine it due to missing indexes, we would.
                # For this implementation, we assume our sweep above is exhaustive for direct links.
                pass

        # 3. Code Entity / Verification Target Impact
        if change.entity_id:
            target_impacts = self._trace_entity_impact(change.entity_id, change.change_id, contracts)
            impacts.extend(target_impacts)
            
            # 4. Unknown relationships
            # If the change has an entity, but we found NO explicit target links,
            # and it's a structural/behavioral change, surface UNKNOWN_RELATIONSHIP.
            if not target_impacts and change.drift_type in (DriftType.BEHAVIORAL, DriftType.STRUCTURAL, DriftType.AUTHORIZATION, DriftType.DATA):
                impacts.append(self._create_impact(
                    change.change_id, "ENTITY", change.entity_id,
                    "Code entity changed but no verification-target relationship exists.",
                    impact_type="UNKNOWN_RELATIONSHIP"
                ))

        return impacts

    def _trace_entity_impact(
        self,
        entity_id: str,
        change_id: str,
        contracts: list[SemanticContract],
    ) -> list[SemanticImpact]:
        """
        Trace entity -> target -> contract -> obligations.
        Positive and negative obligations are evaluated independently.
        """
        impacts: list[SemanticImpact] = []
        
        for contract in contracts:
            affected_targets = []
            for target in contract.verification_targets:
                if target.code_entity_ref == entity_id:
                    affected_targets.append(target.target_id)
            
            if affected_targets:
                # This contract is affected.
                # Now identify affected obligations. In a robust system, the target would
                # explicitly link to specific obligations. Since we don't have that index in
                # SemanticContract (targets are flat on the contract), we must mark ALL
                # obligations on this contract as potentially affected.
                # We still respect independence by creating separate lists.
                
                affected_obs = []
                for allowed in contract.allowed_behaviors:
                    affected_obs.append(generate_obligation_id(contract.contract_id, allowed.description))
                for forbidden in contract.forbidden_behaviors:
                    affected_obs.append(generate_obligation_id(contract.contract_id, f"FORBIDDEN: {forbidden.description}"))
                    
                impacts.append(self._create_impact(
                    change_id, "TARGET", affected_targets[0],
                    f"Entity {entity_id} affects verification target(s).",
                    affected_targets=affected_targets,
                    affected_contracts=[contract.contract_id],
                    affected_requirements=[contract.requirement_id],
                    affected_obligations=affected_obs,
                    impact_type="TRANSITIVE"
                ))
                
        return impacts

    def _create_impact(
        self,
        change_id: str,
        artifact_type: str,
        artifact_id: str,
        reason: str,
        affected_requirements: list[str] | None = None,
        affected_contracts: list[str] | None = None,
        affected_obligations: list[str] | None = None,
        affected_targets: list[str] | None = None,
        impact_type: str = "DIRECT"
    ) -> SemanticImpact:
        
        iid = generate_impact_id(change_id, artifact_type, artifact_id, reason)
        return SemanticImpact(
            impact_id=iid,
            change_id=change_id,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            affected_requirements=affected_requirements or [],
            affected_contracts=affected_contracts or [],
            affected_obligations=affected_obligations or [],
            affected_targets=affected_targets or [],
            reason=reason,
            impact_type=impact_type,
        )
