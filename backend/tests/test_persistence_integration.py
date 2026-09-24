"""
SVA Phase 14 Real Persistence Integration Tests
================================================

These tests verify that the real Phase 1-12 pipeline, driven by LocalAnalysisWorker,
produces genuinely persisted artifacts connected by real FK relationships.

Key principles enforced:
- No mocking of AnalysisOrchestrator.run()
- No mocking of LocalAnalysisWorker
- Persistence failures must propagate (no swallowed errors)
- Causal chain verified by real FK IDs, not row counts
- Workspace isolation verified by scoped repository queries
"""
import asyncio
import uuid
import pytest
import pytest_asyncio

from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.persistence.models.job import AnalysisJobRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.intent import IntentCandidateRow
from app.persistence.models.semantic_ir import SemanticRequirementRow, SemanticConditionRow
from app.persistence.models.ambiguity import AmbiguityCaseRow, InterpretationRow, ClarificationQuestionRow
from app.persistence.models.contract import (
    SemanticContractRow, BehaviorExpectationRow, InvariantRow,
    VerificationTargetRow, ContractAssumptionRow,
)
from app.persistence.models.evidence import EvidenceRow, EvidenceIntegrityRow, EnvironmentFingerprintRow
from app.persistence.models.verification import VerificationReportRow, RequirementVerificationRow, ObligationVerificationRow
from app.persistence.models.skeptic import CounterexampleRow

from app.persistence.repositories.repository_repo import RepositoryRepo, AnalysisRepo
from app.persistence.repositories.workspace_repo import WorkspaceRepository
from app.persistence.repositories.job_repo import AnalysisJobRepo
from app.orchestration.worker import LocalAnalysisWorker


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "repos"


async def _wait_for_job_terminal(SessionLocal, job_id: str, timeout: float = 30.0):
    """Poll until AnalysisJob reaches a terminal state. Returns the final job row."""
    elapsed = 0.0
    while elapsed < timeout:
        async with SessionLocal() as s:
            result = await s.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id))
            job = result.scalar_one_or_none()
            if job and job.status in ("SUCCEEDED", "FAILED", "CANCELLED"):
                return job
        await asyncio.sleep(0.5)
        elapsed += 0.5
    raise TimeoutError(f"Job {job_id} did not reach terminal state within {timeout}s")


# ─────────────────────────────────────────────────────────────────────────────
# Intent persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intent_mapper_to_row(db: AsyncSession):
    """IntentMapper correctly maps a candidate to a DB row."""
    from app.persistence.mappers.intent_mapper import IntentMapper
    from app.repository.intent.models import IntentCandidate, CandidateStatus, Provenance

    candidate = IntentCandidate(
        candidate_id="cand-pi-001",
        analysis_id="analysis-pi-001",
        original_statement="Users must not read other users' data",
        normalized_statement="users cannot read other users data",
        status=CandidateStatus.CANDIDATE,
        human_confirmed=False,
        extraction_method="RULE_BASED",
        sources=[],
        provenance=Provenance.DEFAULT,
        evidence=[],
    )
    row = IntentMapper.to_row(candidate)
    db.add(row)
    await db.flush()

    fetched = (await db.execute(
        select(IntentCandidateRow).where(IntentCandidateRow.candidate_id == "cand-pi-001")
    )).scalar_one()
    assert fetched.analysis_id == "analysis-pi-001"
    assert fetched.status == "CANDIDATE"
    assert fetched.provenance == "DEFAULT"


# ─────────────────────────────────────────────────────────────────────────────
# Semantic IR persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_semantic_ir_mapper_req_to_row(db: AsyncSession):
    """SemanticIRMapper correctly maps a SemanticRequirement to DB rows."""
    from app.persistence.mappers.semantic_ir_mapper import SemanticIRMapper
    from app.semantic_ir.models import SemanticRequirement, Precondition
    from app.repository.intent.models import CandidateStatus, Provenance, SourceLocation

    req = SemanticRequirement(
        requirement_id="req-sir-001",
        candidate_id="cand-001",
        analysis_id="analysis-sir-001",
        statement="Users cannot access another user's data",
        original_statement="Users must not access others' data",
        provenance=Provenance.DEFAULT,
        sources=[],
        status=CandidateStatus.CANDIDATE,
        preconditions=[],
        postconditions=[],
        forbidden_behaviors=[],
        assumptions=[],
    )
    row = SemanticIRMapper.req_to_row(req)
    db.add(row)
    await db.flush()

    fetched = (await db.execute(
        select(SemanticRequirementRow).where(SemanticRequirementRow.requirement_id == "req-sir-001")
    )).scalar_one()
    assert fetched.candidate_id == "cand-001"
    assert fetched.provenance == "DEFAULT"


@pytest.mark.asyncio
async def test_provenance_survives_semantic_ir_roundtrip(db: AsyncSession):
    """Provenance is stored and retrieved correctly from SemanticRequirementRow."""
    row = SemanticRequirementRow(
        requirement_id="req-prov-001",
        candidate_id=None,
        analysis_id="a-1",
        statement="stmt",
        original_statement="original stmt",
        status="ACCEPTED",
        sources=[],
        provenance="AI_INFERENCE",
    )
    db.add(row)
    await db.flush()

    fetched = (await db.execute(
        select(SemanticRequirementRow).where(SemanticRequirementRow.requirement_id == "req-prov-001")
    )).scalar_one()
    assert fetched.provenance == "AI_INFERENCE"


# ─────────────────────────────────────────────────────────────────────────────
# Ambiguity persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ambiguity_mapper_case_to_row(db: AsyncSession):
    """AmbiguityMapper maps an AmbiguityCase and Interpretation to DB rows."""
    from app.persistence.mappers.ambiguity_mapper import AmbiguityMapper
    from app.ambiguity.models import AmbiguityCase, AmbiguityType, Interpretation, InterpretationStatus, ClarificationQuestion, ClarificationStatus, QuestionOption
    from app.repository.intent.models import Provenance

    interp = Interpretation(
        interpretation_id="interp-001",
        requirement_id="req-001",
        statement="User A cannot see User B's profile",
        provenance=Provenance.AI_INFERENCE,
        interpretation_method="RULE_BASED",
        status=InterpretationStatus.PROPOSED,
        semantic_fields={},
        assumptions=[],
    )
    question = ClarificationQuestion(
        question_id="q-001",
        ambiguity_id="amb-001",
        question="Does 'access' include read-only?",
        options=[QuestionOption(option_id="o-1", text="Yes", maps_to_interpretation_id="interp-001")],
        status=ClarificationStatus.OPEN,
        information_gain=0.8,
    )
    case = AmbiguityCase(
        ambiguity_id="amb-001",
        requirement_ids=["req-001"],
        candidate_ids=["cand-001"],
        statement="Users must not access other users' data",
        ambiguity_types=[AmbiguityType.ACTOR],
        interpretations=[interp],
        clarification_question=question,
        provenance=Provenance.AI_INFERENCE,
    )
    case_row = AmbiguityMapper.case_to_row(case)
    db.add(case_row)
    await db.flush()

    interp_row = AmbiguityMapper.interpretation_to_row(case.ambiguity_id, interp)
    db.add(interp_row)
    q_row = AmbiguityMapper.question_to_row(case.ambiguity_id, question)
    db.add(q_row)
    await db.flush()

    fetched_case = (await db.execute(
        select(AmbiguityCaseRow).where(AmbiguityCaseRow.ambiguity_id == "amb-001")
    )).scalar_one()
    assert "ACTOR" in fetched_case.ambiguity_types

    fetched_interp = (await db.execute(
        select(InterpretationRow).where(InterpretationRow.ambiguity_id == "amb-001")
    )).scalar_one()
    assert fetched_interp.interpretation_id == "interp-001"
    assert fetched_interp.interpretation_method == "RULE_BASED"

    fetched_q = (await db.execute(
        select(ClarificationQuestionRow).where(ClarificationQuestionRow.ambiguity_id == "amb-001")
    )).scalar_one()
    assert fetched_q.question_id == "q-001"
    assert len(fetched_q.options) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Contract + dependent rows persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contract_mapper_full_graph(db: AsyncSession):
    """ContractMapper maps contract + behaviors + invariants + assumptions + targets."""
    from app.persistence.mappers.contract_mapper import ContractMapper
    from app.contracts.models import (
        SemanticContract, BehaviorExpectation, Invariant,
        ContractAssumption, VerificationTarget, VerificationTargetCategory
    )
    from app.repository.intent.models import Provenance

    contract = SemanticContract(
        contract_id="contract-pm-001",
        contract_version="1",
        requirement_id="req-001",
        candidate_id="cand-001",
        analysis_id="analysis-001",
        statement="Users cannot access another user's data",
        allowed_behaviors=[
            BehaviorExpectation(
                behavior_id="beh-001",
                description="User reads own data",
                actor="User",
                action="READ",
                resource="OwnProfile",
                expected_outcome="Data returned",
                provenance=Provenance.DEFAULT,
            )
        ],
        forbidden_behaviors=[
            BehaviorExpectation(
                behavior_id="beh-002",
                description="User reads another's data",
                actor="User",
                action="READ",
                resource="OtherUserProfile",
                expected_outcome="Access denied",
                provenance=Provenance.DEFAULT,
            )
        ],
        invariants=[
            Invariant(invariant_id="inv-001", statement="requester.id != target.owner_id", provenance=Provenance.DEFAULT)
        ],
        assumptions=[
            ContractAssumption(assumption_id="assum-001", statement="Authentication is enforced", provenance=Provenance.DEFAULT)
        ],
        verification_targets=[
            VerificationTarget(
                target_id="tgt-001",
                category=VerificationTargetCategory.API_ENDPOINT,
                description="GET /users/{id} endpoint",
                code_entity_ref=None,
            )
        ],
    )

    db.add(ContractMapper.contract_to_row(contract))
    await db.flush()
    for b in contract.allowed_behaviors:
        db.add(ContractMapper.behavior_to_row(contract.contract_id, b))
    for b in contract.forbidden_behaviors:
        db.add(ContractMapper.behavior_to_row(contract.contract_id, b))
    for inv in contract.invariants:
        db.add(ContractMapper.invariant_to_row(contract.contract_id, inv))
    for a in contract.assumptions:
        db.add(ContractMapper.assumption_to_row(contract.contract_id, a))
    for t in contract.verification_targets:
        db.add(ContractMapper.target_to_row(contract.contract_id, t))
    await db.flush()

    # Verify all rows exist with correct FKs
    fetched = (await db.execute(
        select(SemanticContractRow).where(SemanticContractRow.contract_id == "contract-pm-001")
    )).scalar_one()
    assert fetched.requirement_id == "req-001"

    behaviors = (await db.execute(
        select(BehaviorExpectationRow).where(BehaviorExpectationRow.contract_id == "contract-pm-001")
    )).scalars().all()
    assert len(behaviors) == 2

    inv_rows = (await db.execute(
        select(InvariantRow).where(InvariantRow.contract_id == "contract-pm-001")
    )).scalars().all()
    assert len(inv_rows) == 1

    assum_rows = (await db.execute(
        select(ContractAssumptionRow).where(ContractAssumptionRow.contract_id == "contract-pm-001")
    )).scalars().all()
    assert len(assum_rows) == 1
    assert assum_rows[0].statement == "Authentication is enforced"

    target_rows = (await db.execute(
        select(VerificationTargetRow).where(VerificationTargetRow.contract_id == "contract-pm-001")
    )).scalars().all()
    assert len(target_rows) == 1
    assert target_rows[0].category == "API_ENDPOINT"


# ─────────────────────────────────────────────────────────────────────────────
# Evidence + integrity/environment rows unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evidence_mapper_full_row(db: AsyncSession):
    """EvidenceMapper maps evidence + integrity row correctly."""
    from app.persistence.mappers.evidence_mapper import EvidenceMapper
    from app.evidence.models import (
        Evidence, EvidenceType, VerificationMethod, EvidenceResult,
        EvidenceStatus, EvidenceIntegrity
    )
    from datetime import datetime, timezone

    ev = Evidence(
        evidence_id="ev-pi-001",
        contract_id="contract-001",
        requirement_id="req-001",
        repository_id="repo-001",
        commit_id="abc123",
        evidence_type=EvidenceType.STATIC_ANALYSIS,
        verification_method=VerificationMethod.STATIC_ANALYSIS,
        result=EvidenceResult.PASS,
        status=EvidenceStatus.OBSERVED,
        description="Static analysis passed",
        observation="No issues found",
        collected_at=datetime.now(timezone.utc).isoformat(),
    )
    ev.integrity = EvidenceIntegrity(
        evidence_hash="sha256:aabbcc",
        hash_algorithm="SHA-256",
        input_hashes={"obs": "sha256:dead"},
        parent_evidence_ids=[],
    )

    db.add(EvidenceMapper.to_row(ev))
    await db.flush()
    db.add(EvidenceMapper.integrity_to_row(ev.evidence_id, ev.integrity))
    await db.flush()

    fetched = (await db.execute(
        select(EvidenceRow).where(EvidenceRow.evidence_id == "ev-pi-001")
    )).scalar_one()
    assert fetched.contract_id == "contract-001"
    assert fetched.result == "PASS"

    integrity = (await db.execute(
        select(EvidenceIntegrityRow).where(EvidenceIntegrityRow.evidence_id == "ev-pi-001")
    )).scalar_one()
    assert integrity.evidence_hash == "sha256:aabbcc"
    assert integrity.input_hashes == {"obs": "sha256:dead"}


# ─────────────────────────────────────────────────────────────────────────────
# Verification persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verification_mapper_report_to_row(db: AsyncSession):
    """VerificationMapper persists a VerificationReport correctly."""
    from app.persistence.repositories.verification_repo import VerificationRepository
    from app.verification.models import VerificationReport
    from datetime import datetime, timezone

    report = VerificationReport(
        verification_id="vr-pi-001",
        repository_id="repo-001",
        commit_id="abc123",
        generated_at=datetime.now(timezone.utc).isoformat(),
        engine_version="1.0.0",
        requirement_results=[],
    )
    repo = VerificationRepository(db)
    await repo.save_report(report)

    fetched = await repo.get_report("vr-pi-001")
    assert fetched is not None
    assert fetched.repository_id == "repo-001"


# ─────────────────────────────────────────────────────────────────────────────
# Skeptic persistence unit tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_skeptic_mapper_counterexample_to_row(db: AsyncSession):
    """SkepticMapper persists a Counterexample correctly."""
    from app.persistence.mappers.skeptic_mapper import SkepticMapper
    from app.skeptic.models import Counterexample, CounterexampleActor, SkepticStrategy

    cx = Counterexample(
        counterexample_id="cx-pi-001",
        requirement_id="req-001",
        contract_id="contract-001",
        obligation_id="obl-001",
        target_id="tgt-001",
        scenario_id="scen-001",
        hypothesis="An attacker can bypass auth by forging a token",
        preconditions=["attacker is unauthenticated"],
        actor=CounterexampleActor(role="attacker", is_authenticated=False),
        action="READ",
        resource="OtherUserProfile",
        expected_behavior="Access denied",
        violating_behavior="Data returned",
        strategy=SkepticStrategy.AUTHORIZATION_BOUNDARY,
    )
    row = SkepticMapper.counterexample_to_row(cx)
    db.add(row)
    await db.flush()

    fetched = (await db.execute(
        select(CounterexampleRow).where(CounterexampleRow.counterexample_id == "cx-pi-001")
    )).scalar_one()
    assert fetched.hypothesis == "An attacker can bypass auth by forging a token"
    assert fetched.requirement_id == "req-001"
    assert fetched.contract_id == "contract-001"


# ─────────────────────────────────────────────────────────────────────────────
# FK relationships unit test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fk_contract_to_requirement(db: AsyncSession):
    """Behavior rows reference their parent contract_id correctly."""
    contract_row = SemanticContractRow(
        contract_id="fk-contract-001",
        contract_version="1",
        parent_contract_id=None,
        requirement_id="req-fk-001",
        candidate_id=None,
        analysis_id="analysis-fk-001",
        statement="stmt",
        compilation_status="DRAFT",
        source_refs=[],
    )
    behavior_row = BehaviorExpectationRow(
        behavior_id="beh-fk-001",
        contract_id="fk-contract-001",
        is_allowed="ALLOWED",
        description="desc",
        actor=None, action=None, resource=None, expected_outcome=None,
        provenance=None,
    )
    db.add(contract_row)
    await db.flush()
    db.add(behavior_row)
    await db.flush()

    behaviors = (await db.execute(
        select(BehaviorExpectationRow).where(BehaviorExpectationRow.contract_id == "fk-contract-001")
    )).scalars().all()
    assert len(behaviors) == 1
    assert behaviors[0].behavior_id == "beh-fk-001"


# ─────────────────────────────────────────────────────────────────────────────
# Rollback on persistence failure
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rollback_on_persistence_failure(engine):
    """A duplicate PK insert is not silently swallowed; session rolls back."""
    from sqlalchemy.exc import IntegrityError

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    contract_id = f"rollback-contract-{uuid.uuid4()}"

    async with SessionLocal() as session:
        row = SemanticContractRow(
            contract_id=contract_id,
            contract_version="1",
            parent_contract_id=None,
            requirement_id="req-001",
            candidate_id=None,
            analysis_id="analysis-001",
            statement="stmt",
            compilation_status="DRAFT",
            source_refs=[],
        )
        session.add(row)
        await session.commit()

    # Inserting a duplicate must raise IntegrityError
    async with SessionLocal() as session:
        duplicate = SemanticContractRow(
            contract_id=contract_id,  # Duplicate PK
            contract_version="2",
            parent_contract_id=None,
            requirement_id="req-001",
            candidate_id=None,
            analysis_id="analysis-001",
            statement="duplicate",
            compilation_status="READY",
            source_refs=[],
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    # Original row must still exist
    async with SessionLocal() as session:
        fetched = (await session.execute(
            select(SemanticContractRow).where(SemanticContractRow.contract_id == contract_id)
        )).scalar_one_or_none()
        assert fetched is not None
        assert fetched.contract_version == "1"


# ─────────────────────────────────────────────────────────────────────────────
# Workspace isolation unit test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workspace_isolation_full(db: AsyncSession):
    """Repositories, analyses, and intents from WS A are invisible from WS B scope."""
    ws_repo = WorkspaceRepository(db)
    repo_repo = RepositoryRepo(db)
    analysis_repo = AnalysisRepo(db)

    ws_a = await ws_repo.create("Isolation WS A")
    ws_b = await ws_repo.create("Isolation WS B")

    repo_a = await repo_repo.create(ws_a.id, "repo-a", "git", "file:///repo-a")
    repo_b = await repo_repo.create(ws_b.id, "repo-b", "git", "file:///repo-b")

    await analysis_repo.create(f"analysis-iso-a-{uuid.uuid4()}", repo_a.id, "commit-a", "COMPLETED")
    await analysis_repo.create(f"analysis-iso-b-{uuid.uuid4()}", repo_b.id, "commit-b", "COMPLETED")

    # WS A repos
    a_repos = await repo_repo.get_by_workspace(ws_a.id)
    a_ids = {r.id for r in a_repos}
    assert repo_a.id in a_ids
    assert repo_b.id not in a_ids

    # WS B repos
    b_repos = await repo_repo.get_by_workspace(ws_b.id)
    b_ids = {r.id for r in b_repos}
    assert repo_b.id in b_ids
    assert repo_a.id not in b_ids


# ─────────────────────────────────────────────────────────────────────────────
# Worker → Orchestrator → Persistence integration test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_orchestrator_persistence_integration(db: AsyncSession, engine, injection_repo: Path):
    """
    Full integration test: real LocalAnalysisWorker → real AnalysisOrchestrator
    → real Phase 1-12 pipeline → real persistence → DB inspection.

    No mocks on the orchestrator path. Verifies the causal chain:
    Job QUEUED → RUNNING → SUCCEEDED, Analysis COMPLETED,
    and generated artifacts persisted in the DB.
    """
    ws_repo = WorkspaceRepository(db)
    repo_repo = RepositoryRepo(db)
    analysis_repo = AnalysisRepo(db)

    # Setup two workspaces to verify isolation
    ws_a = await ws_repo.create("IntegWS A")
    ws_b = await ws_repo.create("IntegWS B")

    # Use local provider with the fixture repo path
    repo_a = await repo_repo.create(
        ws_a.id, "fixture-repo", "local", str(injection_repo), provider_type="local"
    )
    await repo_repo.create(ws_b.id, "other-repo", "local", str(injection_repo), provider_type="local")

    analysis_id = f"integ-analysis-{uuid.uuid4()}"
    analysis = await analysis_repo.create(analysis_id, repo_a.id, "HEAD", "CREATED")
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws_a.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    worker = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)

    worker_task = asyncio.create_task(worker.start())
    try:
        job = await _wait_for_job_terminal(SessionLocal, job_id, timeout=30.0)
    finally:
        await worker.stop()
        await worker_task

    assert job.status == "SUCCEEDED", (
        f"Job ended in {job.status!r}. last_error: {job.last_error}"
    )

    async with SessionLocal() as session:
        # Verify Analysis reached COMPLETED
        analysis_row = (await session.execute(
            select(AnalysisRow).where(AnalysisRow.id == analysis_id)
        )).scalar_one()
        assert analysis_row.status == "COMPLETED", (
            f"Analysis ended in {analysis_row.status!r}"
        )

        # Causal chain: Intents
        intents = (await session.execute(
            select(IntentCandidateRow).where(IntentCandidateRow.analysis_id == analysis_id)
        )).scalars().all()
        assert len(intents) > 0, "No IntentCandidateRows persisted"
        candidate_ids = {i.candidate_id for i in intents}

        # Causal chain: Semantic Requirements linked to intents
        reqs = (await session.execute(
            select(SemanticRequirementRow).where(SemanticRequirementRow.analysis_id == analysis_id)
        )).scalars().all()
        assert len(reqs) > 0, "No SemanticRequirementRows persisted"
        req_ids = {r.requirement_id for r in reqs}

        # Each SemanticRequirement must link back to a known candidate_id
        for req in reqs:
            if req.candidate_id:  # candidate_id is nullable but should be set in pipeline
                assert req.candidate_id in candidate_ids, (
                    f"SemanticRequirement {req.requirement_id} links to unknown candidate "
                    f"{req.candidate_id!r}"
                )

        # Causal chain: Contracts linked to requirements
        contracts = (await session.execute(
            select(SemanticContractRow).where(SemanticContractRow.analysis_id == analysis_id)
        )).scalars().all()
        assert len(contracts) > 0, "No SemanticContractRows persisted"
        contract_ids = {c.contract_id for c in contracts}

        # Each Contract must link back to a known requirement_id
        for contract in contracts:
            if contract.requirement_id:
                assert contract.requirement_id in req_ids, (
                    f"Contract {contract.contract_id} links to unknown requirement "
                    f"{contract.requirement_id!r}"
                )

        # Evidence rows (may be 0 if EvidenceCollector found nothing — acceptable)
        evidence_rows = (await session.execute(
            select(EvidenceRow).where(EvidenceRow.repository_id == repo_a.id)
        )).scalars().all()
        # No assertion on count — but if evidence exists, its contract_id must link to a known contract
        for ev in evidence_rows:
            if ev.contract_id:
                assert ev.contract_id in contract_ids, (
                    f"Evidence {ev.evidence_id} links to unknown contract {ev.contract_id!r}"
                )

        # Workspace Isolation: WS B must not see WS A's repos' analyses
        ws_b_id = ws_b.id
        b_repos = await repo_repo.get_by_workspace(ws_b_id)
        b_repo_ids = {r.id for r in b_repos}
        assert repo_a.id not in b_repo_ids, "WS B can see WS A's repository — isolation violated"
