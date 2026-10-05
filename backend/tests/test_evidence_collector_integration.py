import pytest
import os
from pathlib import Path

from app.evidence.collectors import EvidenceCollector
from app.contracts.models import SemanticContract, VerificationTarget, VerificationTargetCategory
from app.repository.types import ScanResult, FileRecord, FileClassification
from app.repository.scanner.path_guard import PathGuard
from app.repository.scanner.file_discovery import FileDiscovery

def test_evidence_collector_integration(tmp_path: Path):
    # Setup dummy project
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("""
def delete_project():
    pass
""")

    # 1. Real scan
    guard = PathGuard(root=tmp_path)
    discovery = FileDiscovery(guard)
    scan_result = discovery.scan()

    # 2. Dummy contract with a verification target
    target = VerificationTarget(
        target_id="tgt-001",
        category=VerificationTargetCategory.BEHAVIOR,
        description="Verify delete on project",
        identifier="delete_project",
    )
    contract = SemanticContract(
        contract_id="contract-001",
        requirement_id="req-001",
        candidate_id="cand-001",
        analysis_id="analysis-456",
        statement="Only project owners can delete projects",
        verification_targets=[target],
        allowed_behaviors=[],
        forbidden_behaviors=[],
        invariants=[],
        assumptions=[]
    )

    # 3. Collect evidence
    collector = EvidenceCollector()
    evidence = collector.collect(
        repository_id="repo-123",
        analysis_id="analysis-456",
        scan_result=scan_result,
        contracts=[contract],
        commit_id="HEAD",
        snapshot_path=str(tmp_path),
        snapshot_id="snap-789"
    )

    # We expect 1 STATIC mapping evidence because we have 1 target,
    # and main.py defines a function 'delete_project'.
    # Because our ParserManager will extract it!
    assert len(evidence) >= 1
    
    # Check that at least one evidence points to our target
    matched = False
    for ev in evidence:
        if ev.target_refs and "tgt-001" in ev.target_refs:
            matched = True
            assert ev.result.value == "INCONCLUSIVE" # Static matches are INCONCLUSIVE
            assert "delete_project" in ev.observation or "delete_project" in ev.description
    
    assert matched, "EvidenceCollector did not produce a code mapping for the function"

