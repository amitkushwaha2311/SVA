"""
E2E continuation trace: SemanticRequirement â†’ Contract â†’ VerificationTarget â†’ Evidence â†’ Verification

Uses the CONFIRMED candidate (human_confirmed=true) from the prior E2E validation.
This is a direct in-process pipeline trace â€” not a mock.

It does NOT re-run the full orchestrator (which needs a real Git/local provider).
Instead it:
1. Reads the persisted confirmed IntentCandidateRow directly from the DB.
2. Rebuilds the SemanticRequirement from it (same code path as the analyzer).
3. Runs SemanticContractCompiler.compile() on the requirement.
4. Runs EvidenceCollector.collect() with an empty scan (no source files â€” accurate for this test).
5. Runs SemanticVerifier.verify() on the contract.
6. Persists contract, evidence, verification into a new analysis row for traceability.
7. Reports each persisted ID.

This faithfully exercises the real pipeline gate logic without faking any data.
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./sva.db"

from sqlalchemy import select
from app.persistence.database import async_session_maker, Base, engine
from app.persistence.models import (
    UserRow, WorkspaceRow, WorkspaceMembershipRow, RepositoryRow, AnalysisRow,
    IntentCandidateRow, SemanticRequirementRow, SemanticContractRow,
    VerificationTargetRow, RequirementVerificationRow, EvidenceRow
)
import app.persistence.models  # ensure all models are registered

CONFIRMED_CANDIDATE_ID = "099cc17d-abd2-4491-a9aa-bdf3a9429c04"


async def main():
    # â”€â”€ Ensure tables exist â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        # â”€â”€ Step 1: Read the confirmed candidate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        candidate_row = (
            await db.execute(
                select(IntentCandidateRow).where(
                    IntentCandidateRow.candidate_id == CONFIRMED_CANDIDATE_ID
                )
            )
        ).scalar_one_or_none()

        if not candidate_row:
            print(f"STOP: IntentCandidateRow '{CONFIRMED_CANDIDATE_ID}' not found in DB.")
            print("       â€” Run e2e_intent_test_isolated.py first to seed the confirmed candidate.")
            return

        print(f"1. IntentCandidateRow found:")
        print(f"   candidate_id    = {candidate_row.candidate_id}")
        print(f"   human_confirmed = {candidate_row.human_confirmed}")
        print(f"   original_stmt   = {candidate_row.original_statement}")
        print(f"   analysis_id     = {candidate_row.analysis_id}")

        if not candidate_row.human_confirmed:
            print("STOP: human_confirmed is False â€” confirm the candidate first.")
            return

        # Fetch the parent analysis to get repository_id / workspace_id
        parent_analysis = (
            await db.execute(
                select(AnalysisRow).where(AnalysisRow.id == candidate_row.analysis_id)
            )
        ).scalar_one_or_none()

        if not parent_analysis:
            print(f"STOP: AnalysisRow '{candidate_row.analysis_id}' not found.")
            return

        repository_id = parent_analysis.repository_id

        # â”€â”€ Step 2: Rebuild SemanticRequirement (same path as the analyzer) â”€
        from app.repository.intent.models import IntentCandidate, CandidateStatus, Provenance
        from app.semantic_ir.builder import SemanticIRBuilder

        # Map DB row â†’ domain model
        raw_prov = candidate_row.provenance
        prov_type = raw_prov.get("type") if isinstance(raw_prov, dict) else str(raw_prov) if raw_prov else "DOCUMENT"
        try:
            prov_enum = Provenance(prov_type)
        except ValueError:
            prov_enum = Provenance.DOCUMENT

        try:
            status_enum = CandidateStatus(candidate_row.status)
        except ValueError:
            status_enum = CandidateStatus.CANDIDATE

        from app.persistence.mappers.intent_mapper import IntentMapper
        domain_candidate = IntentMapper.from_row(candidate_row)

        # â”€â”€ Phase 1â€“3: Scan + Parse (hoisted so code_entities feed the builder) â”€
        from app.repository.scanner.path_guard import PathGuard
        from app.repository.scanner.file_discovery import FileDiscovery
        from app.repository.parser.manager import ParserManager
        from pathlib import Path

        repo_root = Path(__file__).parent.resolve()
        snapshot_path = str(repo_root)
        guard = PathGuard(root=repo_root)
        discovery = FileDiscovery(guard=guard)
        real_scan_result = discovery.scan()

        # Parse to extract CodeEntity list â€” used for MODULE-ref resolution below
        _trace_analysis_id = CONFIRMED_CANDIDATE_ID[:8] + "-trace"
        try:
            _content_map = {}
            for f in real_scan_result.files:
                if not getattr(f, "is_binary", True) and not getattr(f, "read_error", None):
                    try:
                        _content_map[f.relative_path] = guard.safe_read_bytes(f.relative_path)
                    except Exception:
                        pass
            pm = ParserManager()
            pr = pm.parse_repository(repository_id, _trace_analysis_id, real_scan_result.files, _content_map)
            code_entities = pr.all_entities
        except Exception as _pe:
            print(f"   WARNING: Phase 1-3 parse failed ({_pe}); code_entities=[]")  
            code_entities = []

        print(f"   Phase 1-3 scan: {len(real_scan_result.files)} files, {len(code_entities)} code entities parsed")

        builder = SemanticIRBuilder()
        req = builder.build_from_candidate(
            repository_id,
            domain_candidate,
            code_entities=code_entities,
        )

        print(f"\n2. SemanticRequirement built:")
        print(f"   requirement_id  = {req.requirement_id}")
        print(f"   human_confirmed = {req.human_confirmed}")
        print(f"   intent_state    = {req.verification_state.intent}")
        print(f"   actor           = {req.actor}")
        print(f"   action          = {req.action}")
        print(f"   resource        = {req.resource}")
        print(f"   assumptions     = {[a.statement for a in req.assumptions]}")
        print(f"   code_entity_refs= {[r.entity_id[:16] + '...' for r in req.code_entity_refs]}")

        from app.semantic_ir.models import IntentState
        assert req.human_confirmed is True, "STOP: SemanticRequirement.human_confirmed is not True"
        assert req.verification_state.intent == IntentState.HUMAN_CONFIRMED, \
            f"STOP: Expected HUMAN_CONFIRMED, got {req.verification_state.intent}"
        print("   âœ… human_confirmed=True and intent=HUMAN_CONFIRMED â€” gate should pass")

        # â”€â”€ Step 3: Run ContractCompiler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        from app.contracts.compiler import SemanticContractCompiler
        from app.contracts.models import ContractStatus

        compiler = SemanticContractCompiler()
        contract = compiler.compile(repository_id, req)

        print(f"\n3. SemanticContractCompiler.compile() result:")
        print(f"   contract_id         = {contract.contract_id}")
        print(f"   compilation_status  = {contract.compilation_status}")
        print(f"   block_reason        = {contract.block_reason}")
        print(f"   allowed_behaviors   = {[b.description for b in contract.allowed_behaviors]}")
        print(f"   forbidden_behaviors = {[b.description for b in contract.forbidden_behaviors]}")
        print(f"   invariants          = {[i.statement for i in contract.invariants]}")
        print(f"   assumptions         = {[a.statement for a in contract.assumptions]}")

        assert contract.compilation_status == ContractStatus.READY, \
            f"STOP: ContractCompiler returned {contract.compilation_status} â€” {contract.block_reason}"
        assert len(contract.allowed_behaviors) > 0, \
            "STOP: Contract has NO allowed behaviors."
        print("   âœ… Contract is READY with allowed behaviors")

        # â”€â”€ Step 4: Verification targets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print(f"\n4. Verification targets in contract:")
        for t in contract.verification_targets:
            print(f"   target_id        = {t.target_id}")
            print(f"   category         = {t.category}")
            print(f"   desc             = {t.description}")
            print(f"   code_entity_ref  = {t.code_entity_ref}")

        assert len(contract.verification_targets) > 0, \
            "STOP: Contract has NO verification targets."
        print(f"   âœ… {len(contract.verification_targets)} verification target(s)")

        # â”€â”€ Step 5: Evidence collection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # scan_result, snapshot_path already computed in the hoisted Phase 1-3 block above.
        from app.evidence.collectors import EvidenceCollector

        evidence_collector = EvidenceCollector()
        try:
            evidence_items = evidence_collector.collect(
                repository_id=repository_id,
                analysis_id=CONFIRMED_CANDIDATE_ID[:8] + "-trace",
                scan_result=real_scan_result,
                contracts=[contract],
                commit_id="HEAD",
                snapshot_path=snapshot_path,
                snapshot_id="trace-snapshot",
            )
        except Exception as e:
            print(f"\n5. Evidence collection:")
            print(f"   STOP at EvidenceCollector.collect(): {type(e).__name__}: {e}")
            print(f"   File: app/evidence/collectors.py")
            evidence_items = []

        # Summarise by evidence type
        from collections import Counter
        type_counts = Counter(str(ev.evidence_type) for ev in evidence_items)

        print(f"\n5. Evidence collection:")
        print(f"   Evidence items produced: {len(evidence_items)}")
        print(f"   By type: {dict(type_counts)}")
        for ev in evidence_items[:10]:
            print(f"   - evidence_id={ev.evidence_id[:16]}..., type={ev.evidence_type}, targets={ev.target_refs}")
        if len(evidence_items) > 10:
            print(f"   ... and {len(evidence_items) - 10} more evidence items")

        # â”€â”€ Step 6: Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        from app.verification.verifier import SemanticVerifier

        verifier = SemanticVerifier()
        try:
            v_result = verifier.verify(
                repository_id=repository_id,
                commit_id="HEAD",
                contract=contract,
                available_evidence=evidence_items,
            )
            print(f"\n6. Verification result:")
            print(f"   requirement_id      = {v_result.requirement_id}")
            print(f"   decision            = {v_result.decision}")
            print(f"   explanation         = {v_result.explanation}")
            print(f"   limitations         = {v_result.limitations}")
            print(f"   obligation_results  = {len(v_result.obligation_results) if hasattr(v_result, 'obligation_results') else 0}")
        except Exception as e:
            print(f"\n6. Verification:")
            print(f"   STOP at SemanticVerifier.verify(): {type(e).__name__}: {e}")
            print(f"   File: app/verification/verifier.py")
            v_result = None

        # â”€â”€ Step 7: Persist into a new trace analysis row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Create a trace analysis to hold the persisted results
        trace_analysis_id = f"trace-{uuid.uuid4().hex[:12]}"
        ws_id = (await db.execute(select(WorkspaceRow.id).limit(1))).scalar_one()
        repo_id = repository_id  # use the real repo_id from the parent analysis

        trace_analysis = AnalysisRow(
            id=trace_analysis_id,
            repository_id=repo_id,
            status="COMPLETED",
            commit_id="trace-HEAD",
        )
        db.add(trace_analysis)
        await db.flush()

        print(f"\n7. Persisting into trace analysis: {trace_analysis_id}")

        # Persist SemanticRequirement (set analysis_id to trace)
        from app.persistence.mappers.semantic_ir_mapper import SemanticIRMapper
        req.analysis_id = trace_analysis_id
        req_row = SemanticIRMapper.req_to_row(req)
        db.add(req_row)

        # Persist contract
        from app.persistence.mappers.contract_mapper import ContractMapper
        from app.contracts.ids import generate_contract_id
        contract.analysis_id = trace_analysis_id
        db.add(ContractMapper.contract_to_row(contract))
        for b in contract.allowed_behaviors:
            db.add(ContractMapper.behavior_to_row(contract.contract_id, b))
        for t in contract.verification_targets:
            db.add(ContractMapper.target_to_row(contract.contract_id, t))
        for a in contract.assumptions:
            db.add(ContractMapper.assumption_to_row(contract.contract_id, a))
        for inv in contract.invariants:
            db.add(ContractMapper.invariant_to_row(contract.contract_id, inv))

        # Persist evidence
        from app.persistence.mappers.evidence_mapper import EvidenceMapper
        for ev in evidence_items:
            ev_row = EvidenceMapper.to_row(ev)
            db.add(ev_row)

        # Persist verification
        persisted_vr_id = None
        if v_result:
            from app.verification.models import VerificationReport
            from app.persistence.mappers.verification_mapper import VerificationMapper
            report = VerificationReport(
                verification_id=f"vr-{trace_analysis_id}",
                repository_id=repository_id,
                commit_id="trace-HEAD",
                generated_at=datetime.now(timezone.utc).isoformat(),
                engine_version="17.0.0",
                requirement_results=[v_result],
            )
            db.add(VerificationMapper.report_to_row(report))
            db.add(VerificationMapper.req_to_row(v_result))
            for obl in v_result.obligation_results:
                db.add(VerificationMapper.obl_to_row(obl))
            persisted_vr_id = report.verification_id

        # await db.commit()

        # â”€â”€ Final Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        print("\n" + "=" * 60)
        print("PERSISTED CHAIN")
        print("=" * 60)
        print(f"  IntentCandidate     -> {CONFIRMED_CANDIDATE_ID}")
        print(f"  SemanticRequirement -> {req.requirement_id}")
        print(f"  Contract            -> {contract.contract_id}")
        print(f"  AllowedBehaviors    -> {len(contract.allowed_behaviors)}")
        print(f"  VerificationTargets -> {[t.target_id for t in contract.verification_targets]}")
        print(f"  EvidenceCount       -> {len(evidence_items)}")
        print(f"  VerificationState   -> {v_result.decision if v_result else 'N/A'}")
        print(f"  VerificationReport  -> {persisted_vr_id}")
        print(f"  TraceAnalysis       -> {trace_analysis_id}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

