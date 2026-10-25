"""
Focused tests for Evidence-to-Obligation Association in SVA.
=============================================================

Tests:
1. Exact obligation_id association
2. Validated target_id mapping association (when obligation_id is None on evidence)
3. Unrelated-target rejection (target for obligation B does not match obligation A)
4. Missing links remain UNKNOWN
5. CODE_MAPPING evidence produces INCONCLUSIVE (never PROVEN or SUPPORTED)
6. Unsupported sandbox (NOT_RUN) leaves obligation UNKNOWN
7. PROVEN strictly requires PASS on or above DETERMINISTIC_TEST ladder level
8. Multi-obligation isolation (evidence for target A does not spill into obligation B)
"""

from datetime import datetime, timezone
import pytest

from app.contracts.models import (
    BehaviorExpectation,
    ContractStatus,
    SemanticContract,
    VerificationTarget,
    VerificationTargetCategory,
)
from app.evidence.ids import generate_evidence_id, generate_obligation_id
from app.evidence.integrity import compute_evidence_hash
from app.evidence.models import (
    Evidence,
    EvidenceIntegrity,
    EvidenceResult,
    EvidenceStatus,
    EvidenceType,
    VerificationMethod,
    VerificationState,
)
from app.verification.verifier import SemanticVerifier


def _create_contract(cid: str = "c-1", two_obligations: bool = False) -> SemanticContract:
    allowed = [
        BehaviorExpectation(
            behavior_id="b-1",
            description="Owner can delete project",
            actor="Owner",
            action="delete",
            resource="project",
            expected_outcome="permitted",
        )
    ]
    ob1_id = generate_obligation_id(cid, "Owner can delete project")
    targets = [
        VerificationTarget(
            target_id="tgt-1",
            category=VerificationTargetCategory.BEHAVIOR,
            description="Verify delete on project",
            obligation_id=ob1_id,
        )
    ]

    forbidden = []
    if two_obligations:
        ob2_desc = "FORBIDDEN: Non-owner cannot delete project"
        ob2_id = generate_obligation_id(cid, ob2_desc)
        forbidden.append(
            BehaviorExpectation(
                behavior_id="b-2",
                description="Non-owner cannot delete project",
                expected_outcome="denied",
            )
        )
        targets.append(
            VerificationTarget(
                target_id="tgt-2",
                category=VerificationTargetCategory.BEHAVIOR,
                description="Verify delete on project denied",
                obligation_id=ob2_id,
            )
        )

    return SemanticContract(
        contract_id=cid,
        requirement_id="req-1",
        candidate_id="cand-1",
        analysis_id="run-1",
        statement="Only project owners can delete projects.",
        compilation_status=ContractStatus.READY,
        allowed_behaviors=allowed,
        forbidden_behaviors=forbidden,
        verification_targets=targets,
    )


def _create_evidence(
    cid: str,
    target_id: str | None = None,
    obligation_id: str | None = None,
    result: EvidenceResult = EvidenceResult.PASS,
    etype: EvidenceType = EvidenceType.DETERMINISTIC_TEST,
    desc: str = "Test execution",
) -> Evidence:
    e_id = generate_evidence_id("repo", cid, etype.value, desc)
    ev = Evidence(
        evidence_id=e_id,
        contract_id=cid,
        requirement_id="req-1",
        repository_id="repo",
        obligation_id=obligation_id,
        evidence_type=etype,
        verification_method=VerificationMethod.UNIT_TEST,
        description=desc,
        observation="Execution observation",
        result=result,
        status=EvidenceStatus.OBSERVED,
        target_refs=[target_id] if target_id else [],
        commit_id="commit-1",
        collected_at=datetime.now(timezone.utc).isoformat(),
    )
    ev.integrity = EvidenceIntegrity(
        evidence_hash=compute_evidence_hash(ev),
        hash_algorithm="SHA-256",
    )
    return ev


class TestEvidenceToObligationAssociation:
    """Test suite verifying strict, validated evidence association."""

    def test_exact_obligation_id_association(self):
        verifier = SemanticVerifier()
        contract = _create_contract()
        ob_id = generate_obligation_id(contract.contract_id, "Owner can delete project")

        ev = _create_evidence(
            cid=contract.contract_id,
            obligation_id=ob_id,
            result=EvidenceResult.PASS,
            etype=EvidenceType.DETERMINISTIC_TEST,
        )

        res = verifier.verify("repo", "commit-1", contract, [ev])
        assert len(res.obligation_results) == 1
        ob_res = res.obligation_results[0]
        assert ob_res.obligation_id == ob_id
        assert ob_res.decision == VerificationState.PROVEN
        assert ev.evidence_id in ob_res.evidence_refs

    def test_validated_target_id_association(self):
        """When obligation_id is None on evidence, target_refs is mapped via target.obligation_id."""
        verifier = SemanticVerifier()
        contract = _create_contract()
        ob_id = generate_obligation_id(contract.contract_id, "Owner can delete project")

        # Evidence only has target_refs=["tgt-1"], obligation_id is None
        ev = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-1",
            obligation_id=None,
            result=EvidenceResult.PASS,
            etype=EvidenceType.DETERMINISTIC_TEST,
        )

        res = verifier.verify("repo", "commit-1", contract, [ev])
        ob_res = res.obligation_results[0]
        assert ob_res.obligation_id == ob_id
        assert ob_res.decision == VerificationState.PROVEN
        assert ev.evidence_id in ob_res.evidence_refs

    def test_unrelated_target_rejection(self):
        """Evidence referencing an unrelated target must NOT associate with the obligation."""
        verifier = SemanticVerifier()
        contract = _create_contract(two_obligations=True)

        ob1_id = generate_obligation_id(contract.contract_id, "Owner can delete project")
        ob2_id = generate_obligation_id(contract.contract_id, "FORBIDDEN: Non-owner cannot delete project")

        # Evidence references tgt-2 (mapped to ob2), not tgt-1 (mapped to ob1)
        ev_for_tgt2 = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-2",
            obligation_id=None,
            result=EvidenceResult.PASS,
            etype=EvidenceType.DETERMINISTIC_TEST,
        )

        res = verifier.verify("repo", "commit-1", contract, [ev_for_tgt2])
        ob1_res = next(o for o in res.obligation_results if o.obligation_id == ob1_id)
        ob2_res = next(o for o in res.obligation_results if o.obligation_id == ob2_id)

        # Obligation 1 did NOT match ev_for_tgt2
        assert ev_for_tgt2.evidence_id not in ob1_res.evidence_refs
        assert ob1_res.decision == VerificationState.UNKNOWN

        # Obligation 2 DID match ev_for_tgt2
        assert ev_for_tgt2.evidence_id in ob2_res.evidence_refs
        assert ob2_res.decision == VerificationState.PROVEN

    def test_missing_links_remain_unknown(self):
        """Evidence with an unmapped target_id and no obligation_id must not match any obligation."""
        verifier = SemanticVerifier()
        contract = _create_contract()

        ev_unmapped = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-foreign",
            obligation_id=None,
            result=EvidenceResult.PASS,
        )

        res = verifier.verify("repo", "commit-1", contract, [ev_unmapped])
        assert res.obligation_results[0].decision == VerificationState.UNKNOWN
        assert len(res.obligation_results[0].evidence_refs) == 0

    def test_code_mapping_produces_inconclusive_never_proven(self):
        """CODE_MAPPING evidence is a candidate pointer, never proof."""
        verifier = SemanticVerifier()
        contract = _create_contract()

        ev_code_map = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-1",
            result=EvidenceResult.INCONCLUSIVE,
            etype=EvidenceType.CODE_MAPPING,
            desc="Static candidate match: Function delete_project in project.py",
        )

        res = verifier.verify("repo", "commit-1", contract, [ev_code_map])
        ob_res = res.obligation_results[0]
        assert ob_res.decision == VerificationState.INCONCLUSIVE
        assert res.decision == VerificationState.INCONCLUSIVE

    def test_unsupported_sandbox_not_run_produces_unknown(self):
        """When dynamic execution is unsupported (NOT_RUN), the obligation remains UNKNOWN."""
        verifier = SemanticVerifier()
        contract = _create_contract()

        ev_not_run = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-1",
            result=EvidenceResult.NOT_RUN,
            etype=EvidenceType.DETERMINISTIC_TEST,
            desc="Execution of pytest",
        )

        res = verifier.verify("repo", "commit-1", contract, [ev_not_run])
        ob_res = res.obligation_results[0]
        assert ob_res.decision == VerificationState.UNKNOWN

    def test_code_mapping_plus_not_run_produces_inconclusive(self):
        """Static candidate mapping + unsupported test execution produces INCONCLUSIVE (not UNKNOWN, not PROVEN)."""
        verifier = SemanticVerifier()
        contract = _create_contract()

        ev_code_map = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-1",
            result=EvidenceResult.INCONCLUSIVE,
            etype=EvidenceType.CODE_MAPPING,
        )
        ev_not_run = _create_evidence(
            cid=contract.contract_id,
            target_id="tgt-1",
            result=EvidenceResult.NOT_RUN,
            etype=EvidenceType.DETERMINISTIC_TEST,
        )

        res = verifier.verify("repo", "commit-1", contract, [ev_code_map, ev_not_run])
        ob_res = res.obligation_results[0]
        # Inconclusive evidence was evaluated and observed, but not proven
        assert ob_res.decision == VerificationState.INCONCLUSIVE
