"""
Tests for Phase 12: Semantic Drift & Semantic CI Engine
"""

import pytest

from app.contracts.models import BehaviorExpectation, SemanticContract, VerificationTarget, VerificationTargetCategory
from app.drift.analyzer import DriftAnalyzer
from app.drift.models import DriftSeverity, DriftType, EntityChangeType, FileChangeType, SemanticCIDecision
from app.evidence.models import Evidence, EvidenceStatus, EvidenceType, VerificationState
from app.repository.intent.models import IntentCandidate, Provenance, SourceLocation
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id
from app.repository.types import FileClassification, FileRecord
from app.semantic_ir.models import SemanticRequirement
from app.verification.models import RequirementVerification


@pytest.fixture
def analyzer():
    return DriftAnalyzer()


@pytest.fixture
def base_files():
    return [
        FileRecord(
            relative_path="src/main.py",
            absolute_path="/src/main.py",
            content_hash="hash_main_v1",
            classification=FileClassification.SOURCE_CODE,
            size_bytes=100,
            is_binary=False,
            encoding="utf-8",
        ),
        FileRecord(
            relative_path="src/auth.py",
            absolute_path="/src/auth.py",
            content_hash="hash_auth_v1",
            classification=FileClassification.SOURCE_CODE,
            size_bytes=200,
            is_binary=False,
            encoding="utf-8",
        ),
        FileRecord(
            relative_path="docs/api.md",
            absolute_path="/docs/api.md",
            content_hash="hash_doc_v1",
            classification=FileClassification.DOCUMENTATION,
            size_bytes=300,
            is_binary=False,
            encoding="utf-8",
        ),
        FileRecord(
            relative_path="config.yaml",
            absolute_path="/config.yaml",
            content_hash="hash_config_v1",
            classification=FileClassification.CONFIGURATION,
            size_bytes=50,
            is_binary=False,
            encoding="utf-8",
        ),
    ]


@pytest.fixture
def base_entities():
    return [
        CodeEntity(
            entity_id=generate_entity_id("repo1", "src/main.py", EntityType.FUNCTION, "main_func", 10),
            repository_id="repo1",
            analysis_id="an1",
            file_path="src/main.py",
            entity_type=EntityType.FUNCTION,
            name="main_func",
            start_line=10,
            end_line=20,
            language="Python",
            extraction_method="TREE_SITTER"
        ),
        CodeEntity(
            entity_id=generate_entity_id("repo1", "src/auth.py", EntityType.FUNCTION, "login", 5),
            repository_id="repo1",
            analysis_id="an1",
            file_path="src/auth.py",
            entity_type=EntityType.FUNCTION,
            name="login",
            start_line=5,
            end_line=15,
            language="Python",
            extraction_method="TREE_SITTER"
        ),
    ]


@pytest.fixture
def requirements():
    return [
        SemanticRequirement(
            requirement_id="REQ-1",
            candidate_id="cand-1",
            analysis_id="an1",
            statement="System must log in",
            original_statement="System must log in",
            provenance=Provenance.DOCUMENT,
            sources=[SourceLocation(path="docs/api.md", start_line=1, end_line=1)]
        )
    ]


@pytest.fixture
def contracts(base_entities):
    return [
        SemanticContract(
            contract_id="CON-1",
            requirement_id="REQ-1",
            repository_id="repo1",
            candidate_id="cand-1",
            analysis_id="an1",
            statement="System must log in",
            verification_targets=[
                VerificationTarget(
                    target_id="TGT-1",
                    category=VerificationTargetCategory.FUNCTION,
                    description="Login function",
                    code_entity_ref=base_entities[1].entity_id,  # auth.py:login
                )
            ],
            allowed_behaviors=[BehaviorExpectation(behavior_id="BEH-1", description="Allows valid users")],
            forbidden_behaviors=[],
            source_refs=[SourceLocation(path="config.yaml", start_line=1, end_line=1)]
        )
    ]


@pytest.fixture
def evidence(base_entities):
    return [
        Evidence(
            evidence_id="EV-1",
            contract_id="CON-1",
            requirement_id="REQ-1",
            repository_id="repo1",
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Login check",
            observation="Observed login",
            commit_id="commit-v1",
            target_refs=["TGT-1"]
        )
    ]


@pytest.fixture
def verifications():
    return [
        RequirementVerification(
            requirement_id="REQ-1",
            contract_id="CON-1",
            decision=VerificationState.PROVEN,
            explanation="Passed static analysis",
            evidence_ids=["EV-1"],
            obligation_verifications=[],
        )
    ]


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_no_changes(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, base_files,  # Target files = Base files
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    assert len(report.changes) == 0
    assert report.semantic_ci_result.decision == SemanticCIDecision.PASS


def test_file_added(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_files = base_files.copy()
    target_files.append(FileRecord(
        relative_path="src/new.py",
        absolute_path="/src/new.py",
        content_hash="hash_new_v1",
        classification=FileClassification.SOURCE_CODE,
        size_bytes=50,
        is_binary=False,
        encoding="utf-8",
    ))
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert len(report.changes) == 1
    assert report.changes[0].file_path == "src/new.py"
    assert report.changes[0].file_change_type == FileChangeType.ADDED
    assert report.semantic_ci_result.decision == SemanticCIDecision.REVIEW


def test_file_removed(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_files = [f for f in base_files if f.relative_path != "src/main.py"]
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    changes = [c for c in report.changes if c.file_change_type == FileChangeType.REMOVED]
    assert len(changes) == 1
    assert changes[0].file_path == "src/main.py"
    

def test_file_modified(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_files = [
        FileRecord(
            relative_path=f.relative_path,
            absolute_path=f.absolute_path,
            content_hash="hash_mod" if f.relative_path == "src/main.py" else f.content_hash,
            classification=f.classification,
            size_bytes=f.size_bytes,
            is_binary=f.is_binary,
            encoding=f.encoding,
        ) for f in base_files
    ]
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    # One change for file modified, one for entity unknown impact
    assert len(report.changes) == 2
    f_change = next(c for c in report.changes if c.file_change_type == FileChangeType.MODIFIED)
    assert f_change.file_path == "src/main.py"
    e_change = next(c for c in report.changes if c.entity_id is not None)
    assert e_change.entity_change_type == EntityChangeType.UNKNOWN
    

def test_entity_added(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_entities = base_entities.copy()
    new_entity = CodeEntity(
        entity_id=generate_entity_id("repo1", "src/main.py", EntityType.FUNCTION, "new_func", 30),
        repository_id="repo1",
        analysis_id="an1",
        file_path="src/main.py",
        entity_type=EntityType.FUNCTION,
        name="new_func",
        start_line=30,
        end_line=40,
        language="Python",
        extraction_method="TREE_SITTER"
    )
    target_entities.append(new_entity)
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, base_files,
        base_entities, target_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert len(report.changes) == 1
    assert report.changes[0].entity_change_type == EntityChangeType.ADDED
    assert report.changes[0].drift_type == DriftType.STRUCTURAL
    # No targets link to this new entity, so UNKNOWN_RELATIONSHIP -> REVIEW
    assert report.semantic_ci_result.decision == SemanticCIDecision.REVIEW


def test_entity_reidentified(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_entities = base_entities.copy()
    # Modify start_line of first entity
    target_entities[0] = CodeEntity(
        entity_id=generate_entity_id("repo1", "src/main.py", EntityType.FUNCTION, "main_func", 15),
        repository_id="repo1",
        analysis_id="an1",
        file_path="src/main.py",
        entity_type=EntityType.FUNCTION,
        name="main_func",
        start_line=15, # Changed
        end_line=25,
        language="Python",
        extraction_method="TREE_SITTER"
    )
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, base_files,
        base_entities, target_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert len(report.changes) == 1
    assert report.changes[0].entity_change_type == EntityChangeType.REIDENTIFIED
    assert report.changes[0].drift_type == DriftType.BEHAVIORAL


def test_intent_drift(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_files = [
        FileRecord(
            relative_path=f.relative_path,
            absolute_path=f.absolute_path,
            content_hash="hash_doc_mod" if f.relative_path == "docs/api.md" else f.content_hash,
            classification=f.classification,
            size_bytes=f.size_bytes,
            is_binary=f.is_binary,
            encoding=f.encoding,
        ) for f in base_files
    ]
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    # Doc changed -> INTENT drift type because docs/api.md is a requirement source
    f_change = report.changes[0]
    assert f_change.file_path == "docs/api.md"
    assert f_change.drift_type == DriftType.INTENT
    assert report.semantic_ci_result.decision == SemanticCIDecision.REVIEW
    assert len(report.impacts) == 1
    assert report.impacts[0].affected_requirements == ["REQ-1"]


def test_config_drift_pass(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    # Add a config file with no links
    base_files.append(FileRecord(
        relative_path="unrelated_config.yaml",
        absolute_path="/unrelated_config.yaml",
        content_hash="h1",
        classification=FileClassification.CONFIGURATION,
        size_bytes=10,
        is_binary=False,
        encoding="utf-8",
    ))
    target_files = base_files.copy()
    target_files[-1] = FileRecord(
        relative_path="unrelated_config.yaml",
        absolute_path="/unrelated_config.yaml",
        content_hash="h2",
        classification=FileClassification.CONFIGURATION,
        size_bytes=10,
        is_binary=False,
        encoding="utf-8",
    )
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert len(report.changes) == 1
    assert report.changes[0].drift_type == DriftType.CONFIGURATION
    assert report.semantic_ci_result.decision == SemanticCIDecision.PASS


def test_config_drift_review(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    # Modify the config.yaml which is explicitly linked to CON-1
    target_files = [
        FileRecord(
            relative_path=f.relative_path,
            absolute_path=f.absolute_path,
            content_hash="hash_cfg_mod" if f.relative_path == "config.yaml" else f.content_hash,
            classification=f.classification,
            size_bytes=f.size_bytes,
            is_binary=f.is_binary,
            encoding=f.encoding,
        ) for f in base_files
    ]
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert report.semantic_ci_result.decision == SemanticCIDecision.REVIEW
    assert any("config.yaml" in r for r in report.semantic_ci_result.reason.split(" | "))
    assert len(report.impacts) == 1
    assert report.impacts[0].affected_contracts == ["CON-1"]


def test_violated_block(analyzer, base_files, base_entities, requirements, contracts, evidence, verifications):
    target_files = [
        FileRecord(
            relative_path=f.relative_path,
            absolute_path=f.absolute_path,
            content_hash="hash_mod" if f.relative_path == "src/main.py" else f.content_hash,
            classification=f.classification,
            size_bytes=f.size_bytes,
            is_binary=f.is_binary,
            encoding=f.encoding,
        ) for f in base_files
    ]
    # Set verification to violated
    verifications[0].decision = VerificationState.VIOLATED
    
    # We also need an impact to trigger the block check, so modify the target entity
    # Actually, modify src/auth.py so target is hit
    target_files[1] = FileRecord(
        relative_path="src/auth.py",
        absolute_path="/src/auth.py",
        content_hash="hash_auth_mod",
        classification=FileClassification.SOURCE_CODE,
        size_bytes=200,
        is_binary=False,
        encoding="utf-8",
    )
    
    report = analyzer.analyze(
        "repo1", "commit-v1", "commit-v2",
        base_files, target_files,
        base_entities, base_entities,
        contracts, requirements, [], evidence, verifications
    )
    
    assert report.semantic_ci_result.decision == SemanticCIDecision.BLOCK
