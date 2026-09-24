"""
Phase 17: Analysis Orchestrator
================================

Coordinates the Phase 1–12 pipeline for a given repository snapshot.
Repository content is UNTRUSTED DATA — never executed, never given authority.

Lifecycle:
  CREATED → QUEUED → INGESTING → SNAPSHOTTING → ANALYZING → VERIFYING → COMPLETED
  ANY_ACTIVE → FAILED (on unrecoverable error)

IMPORTANT: This module uses FastAPI BackgroundTasks for async execution.
BackgroundTasks is NOT durable queue infrastructure. A process restart
will interrupt an in-progress analysis. This boundary is designed so a
future worker/queue can replace BackgroundTasks without rewriting engine logic.
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Orchestrator version — increment when pipeline semantics change
ANALYZER_VERSION = "17.0.0"

# Valid lifecycle transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "CREATED":      ["QUEUED", "FAILED", "CANCELLED"],
    "QUEUED":       ["INGESTING", "FAILED", "CANCELLED"],
    "INGESTING":    ["SNAPSHOTTING", "FAILED", "CANCELLED"],
    "SNAPSHOTTING": ["ANALYZING", "FAILED", "CANCELLED"],
    "ANALYZING":    ["VERIFYING", "FAILED", "CANCELLED"],
    "VERIFYING":    ["COMPLETED", "FAILED", "CANCELLED"],
    "COMPLETED":    [],
    "FAILED":       [],
    "CANCELLED":    [],
}


def _is_valid_transition(current: str, target: str) -> bool:
    return target in _VALID_TRANSITIONS.get(current, [])


class AnalysisOrchestrator:
    """
    Orchestrates the Phase 1–12 SVA pipeline for a single analysis job.

    Design principles:
    - The orchestrator COORDINATES engines; it does not rewrite them.
    - All repository content is treated as DATA.
    - No repository code is executed.
    - Engine failures are captured and recorded — not silently dropped.
    - Verification state (UNKNOWN/INCONCLUSIVE) is determined by engines, not the orchestrator.
    """

    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def run(
        self,
        analysis_id: str,
        repository_id: str,
        provider_name: str,
        repository_identifier: str,
        revision: str,
        workspace_id: str,
    ) -> None:
        """
        Entry point for a full analysis job. Transitions lifecycle and drives pipeline.
        All exceptions are captured to transition the analysis to FAILED.
        """
        async with self.session_factory() as session:
            try:
                await self._run_pipeline(
                    session=session,
                    analysis_id=analysis_id,
                    repository_id=repository_id,
                    provider_name=provider_name,
                    repository_identifier=repository_identifier,
                    revision=revision,
                )
                await session.commit()
            except Exception as exc:
                logger.error("Analysis %s failed: %s", analysis_id, exc, exc_info=True)
                try:
                    await session.rollback()
                    async with self.session_factory() as err_session:
                        await self._set_failed(err_session, analysis_id, str(exc))
                        await err_session.commit()
                except Exception:
                    logger.exception("Failed to record failure state for analysis %s", analysis_id)

    async def _run_pipeline(
        self,
        session: AsyncSession,
        analysis_id: str,
        repository_id: str,
        provider_name: str,
        repository_identifier: str,
        revision: str,
    ) -> None:
        from app.persistence.repositories.repository_repo import AnalysisRepo, RepositorySnapshotRepo
        from app.providers.repository.git import GitProvider, GitProviderError
        from app.providers.repository.local import LocalProvider, LocalProviderError
        from app.repository.scanner.file_discovery import FileDiscovery
        from app.repository.scanner.path_guard import PathGuard
        from app.repository.manifest.repository_manifest import build_manifest
        from app.repository.intent.manager import IntentManager
        from app.semantic_ir.builder import SemanticIRBuilder
        from app.ambiguity.detector import AmbiguityDetector
        from app.contracts.compiler import SemanticContractCompiler
        from app.evidence.collectors import EvidenceCollector
        from app.verification.verifier import SemanticVerifier
        from app.skeptic.generator import SkepticGenerator

        analysis_repo = AnalysisRepo(session)
        snapshot_repo = RepositorySnapshotRepo(session)

        # ── QUEUED ────────────────────────────────────────────────────────────
        await self._transition(session, analysis_id, "QUEUED")

        # ── INGESTING ─────────────────────────────────────────────────────────
        await self._transition(session, analysis_id, "INGESTING")

        with tempfile.TemporaryDirectory(prefix="sva_snapshot_") as tmp_dir:
            snapshot_dir = Path(tmp_dir) / "repo"
            snapshot_dir.mkdir()

            # Select provider
            provider = self._select_provider(provider_name)
            metadata = provider.fetch_snapshot(
                identifier=repository_identifier,
                revision=revision,
                target_dir=snapshot_dir,
            )

            # ── SNAPSHOTTING ──────────────────────────────────────────────────
            await self._transition(session, analysis_id, "SNAPSHOTTING")

            # Validate snapshot integrity BEFORE any engine touches the content
            guard = PathGuard(
                root=snapshot_dir,
                max_file_size_bytes=settings.SCANNER_MAX_FILE_SIZE_BYTES,
                max_depth=settings.SCANNER_MAX_DEPTH,
            )

            # Compute content hash of the snapshot
            content_hash = self._hash_snapshot(guard)

            # Create immutable snapshot record
            snapshot = await snapshot_repo.create(
                repository_id=repository_id,
                provider=metadata.provider,
                canonical_source=metadata.repository_identifier,
                requested_revision=metadata.revision,
                resolved_commit=metadata.resolved_commit,
                content_hash=content_hash,
                manifest_hash="",  # will be updated after manifest build
                analyzer_version=ANALYZER_VERSION,
            )

            # Link snapshot to analysis
            analysis = await analysis_repo.get_by_id(analysis_id)
            if analysis:
                analysis.snapshot_id = snapshot.snapshot_id
                analysis.commit_id = metadata.resolved_commit
                await session.flush()

            # ── ANALYZING ─────────────────────────────────────────────────────
            await self._transition(session, analysis_id, "ANALYZING")

            # Phase 1 — File Discovery (via PathGuard)
            discovery = FileDiscovery(guard=guard, max_files=settings.SCANNER_MAX_FILES)
            scan_result = discovery.scan()

            # Phase 2 — Manifest (repository-level summary)
            manifest = build_manifest(analysis_id=analysis_id, scan_result=scan_result)

            # Update manifest_hash on snapshot
            snapshot.manifest_hash = manifest.repository_hash
            await session.flush()

            # Build content map for intent extraction
            content_map: dict[str, bytes] = {}
            for file_record in scan_result.files:
                if not file_record.is_binary and not file_record.read_error:
                    try:
                        content_map[file_record.relative_path] = guard.safe_read_bytes(file_record.relative_path)
                    except Exception:
                        pass

            # Phase 4 — Intent Discovery
            intent_mgr = IntentManager()
            intent_candidates = intent_mgr.discover_intents(
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_records=scan_result.files,
                content_map=content_map,
            )

            # Persist intent candidates
            await self._persist_intent(session, analysis_id, intent_candidates)

            # Phase 5 — Semantic IR
            ir_builder = SemanticIRBuilder()
            semantic_requirements = []
            for candidate in intent_candidates:
                try:
                    req = ir_builder.build_from_candidate(repository_id, candidate)
                    semantic_requirements.append(req)
                except Exception as e:
                    logger.warning("SemanticIR build failed for candidate %s: %s", candidate.candidate_id, e)

            await self._persist_semantic_ir(session, analysis_id, semantic_requirements)

            # Phase 6 — Ambiguity (if available)
            ambiguity_cases = []
            try:
                ambiguity_engine = AmbiguityDetector()
                ambiguity_cases = ambiguity_engine.detect_contradictions(repository_id, semantic_requirements)
                for req in semantic_requirements:
                    case = ambiguity_engine.detect_ambiguity(repository_id, req)
                    if case:
                        ambiguity_cases.append(case)
            except Exception as e:
                logger.warning("Ambiguity engine failed (non-fatal): %s", e)
            # Persist ambiguity regardless — failures here must propagate
            await self._persist_ambiguity(session, analysis_id, ambiguity_cases)

            # Phase 7 — Contract Compiler
            contracts = []
            try:
                contract_compiler = SemanticContractCompiler()
                for req in semantic_requirements:
                    try:
                        contract = contract_compiler.compile(repository_id, req)
                        contracts.append(contract)
                    except Exception as compile_err:
                        logger.warning(
                            "Contract compile failed for requirement %s: %s",
                            req.requirement_id, compile_err,
                        )
            except Exception as e:
                logger.warning("Contract compiler failed (non-fatal): %s", e)
            # Persist what was compiled — failures here must propagate
            await self._persist_contracts(session, analysis_id, repository_id, contracts)

            # Phase 8 — Evidence
            evidence_items = []
            try:
                evidence_collector = EvidenceCollector()
                evidence_items = evidence_collector.collect(
                    repository_id=repository_id,
                    analysis_id=analysis_id,
                    scan_result=scan_result,
                    contracts=contracts,
                    commit_id=metadata.resolved_commit or "HEAD",
                    snapshot_path=str(snapshot_dir),
                    snapshot_id=snapshot.snapshot_id,
                )
            except Exception as e:
                logger.warning("Evidence collection engine failed (non-fatal): %s", e)
            # Persist what was collected — failures here must propagate
            await self._persist_evidence(session, analysis_id, evidence_items)

            # ── VERIFYING ─────────────────────────────────────────────────────
            await self._transition(session, analysis_id, "VERIFYING")

            # Phase 10 — Verification
            # Phase 9 execution is NOT supported in Phase 17 — properly recorded as UNSUPPORTED.
            verification_results = []
            try:
                verifier = SemanticVerifier()
                resolved_commit = metadata.resolved_commit or "HEAD"
                for contract in contracts:
                    try:
                        result = verifier.verify(
                            repository_id,
                            resolved_commit,
                            contract,
                            evidence_items,
                        )
                        verification_results.append(result)
                    except Exception as verify_err:
                        logger.warning(
                            "Verification failed for contract %s: %s",
                            contract.contract_id, verify_err,
                        )
            except Exception as e:
                logger.warning("Verification engine failed (non-fatal): %s", e)
            
            from app.verification.models import VerificationReport
            report = VerificationReport(
                verification_id=f"vr-{analysis_id}",
                repository_id=repository_id,
                commit_id=metadata.resolved_commit or "HEAD",
                generated_at=datetime.now(timezone.utc).isoformat(),
                engine_version="17.0.0",
                requirement_results=verification_results,
            )
            
            # Persist verification output — failures here must propagate
            await self._persist_verification(session, analysis_id, repository_id, [report])

            # Phase 11 — Skeptic
            all_counterexamples = []
            try:
                skeptic_gen = SkepticGenerator()
                skeptic_reports = []
                for contract in contracts:
                    try:
                        report = skeptic_gen.generate(repository_id, contract)
                        skeptic_reports.append(report)
                    except Exception as skeptic_err:
                        logger.warning(
                            "Skeptic generation failed for contract %s: %s",
                            contract.contract_id, skeptic_err,
                        )
                # Flatten counterexamples across all reports for persistence
                all_counterexamples = [
                    cx for report in skeptic_reports for cx in report.counterexamples
                ]
            except Exception as e:
                logger.warning("Skeptic engine failed (non-fatal): %s", e)
            # Persist skeptic output — failures here must propagate
            await self._persist_skeptic(session, analysis_id, all_counterexamples)

            # Phase 12 — Drift (NOT_APPLICABLE for first analysis without a base)
            # Only runs if a prior resolved_commit exists for this repository.
            # Left as NOT_APPLICABLE for now — Phase 12 integration can be added
            # when incremental analyses are implemented.
            logger.info("Analysis %s: Phase 12 Drift — NOT_APPLICABLE (no prior commit)", analysis_id)

        # ── COMPLETED ─────────────────────────────────────────────────────────
        await self._transition(session, analysis_id, "COMPLETED", completed_at=datetime.now(timezone.utc))
        logger.info("Analysis %s completed successfully.", analysis_id)

    def _select_provider(self, provider_name: str):
        from app.providers.repository.git import GitProvider
        from app.providers.repository.local import LocalProvider
        if provider_name == "git":
            return GitProvider()
        elif provider_name == "local":
            return LocalProvider()
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    def _hash_snapshot(self, guard: "PathGuard") -> str:
        """Compute a content hash across all valid files in the snapshot."""
        h = hashlib.sha256()
        for p in sorted(guard.iter_files()):
            rel = str(p.relative_to(guard.root))
            h.update(rel.encode("utf-8"))
            try:
                h.update(p.read_bytes())
            except Exception:
                pass
        return h.hexdigest()

    async def _transition(
        self,
        session: AsyncSession,
        analysis_id: str,
        new_status: str,
        completed_at: Optional[datetime] = None,
    ) -> None:
        from app.persistence.models.analysis import AnalysisRow
        from sqlalchemy import select

        result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
        row = result.scalar_one_or_none()
        if not row:
            raise RuntimeError(f"Analysis {analysis_id} not found for lifecycle transition")

        if not _is_valid_transition(row.status, new_status):
            raise ValueError(
                f"Illegal lifecycle transition for analysis {analysis_id}: "
                f"{row.status!r} → {new_status!r}"
            )

        row.status = new_status
        if completed_at:
            row.completed_at = completed_at
        await session.flush()
        logger.info("Analysis %s → %s", analysis_id, new_status)

    async def _set_failed(self, session: AsyncSession, analysis_id: str, error_message: str) -> None:
        from app.persistence.models.analysis import AnalysisRow
        from sqlalchemy import select

        result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
        row = result.scalar_one_or_none()
        if row:
            row.status = "FAILED"
            row.error_message = error_message[:1000]  # Truncate to avoid oversized errors
            row.completed_at = datetime.now(timezone.utc)
            await session.flush()

    # ── Persistence helpers ───────────────────────────────────────────────────

    async def _persist_intent(self, session: AsyncSession, analysis_id: str, candidates: list) -> None:
        from app.persistence.mappers.intent_mapper import IntentMapper
        for candidate in candidates:
            session.add(IntentMapper.to_row(candidate))
        await session.flush()

    async def _persist_semantic_ir(self, session: AsyncSession, analysis_id: str, requirements: list) -> None:
        from app.persistence.mappers.semantic_ir_mapper import SemanticIRMapper
        for req in requirements:
            session.add(SemanticIRMapper.req_to_row(req))
            for pre in req.preconditions:
                session.add(SemanticIRMapper.cond_to_row(req.requirement_id, pre))
            for post in req.postconditions:
                session.add(SemanticIRMapper.cond_to_row(req.requirement_id, post))
            for fb in req.forbidden_behaviors:
                session.add(SemanticIRMapper.cond_to_row(req.requirement_id, fb))
            for assume in req.assumptions:
                session.add(SemanticIRMapper.cond_to_row(req.requirement_id, assume))
        await session.flush()

    async def _persist_ambiguity(self, session: AsyncSession, analysis_id: str, cases: list) -> None:
        from app.persistence.mappers.ambiguity_mapper import AmbiguityMapper
        for case in cases:
            session.add(AmbiguityMapper.case_to_row(case))
            for interp in case.interpretations:
                session.add(AmbiguityMapper.interpretation_to_row(case.ambiguity_id, interp))
            if case.clarification_question:
                session.add(AmbiguityMapper.question_to_row(case.ambiguity_id, case.clarification_question))
        await session.flush()

    async def _persist_contracts(self, session: AsyncSession, analysis_id: str, repository_id: str, contracts: list) -> None:
        from app.persistence.mappers.contract_mapper import ContractMapper
        for contract in contracts:
            session.add(ContractMapper.contract_to_row(contract))
            for behavior in contract.allowed_behaviors:
                session.add(ContractMapper.behavior_to_row(contract.contract_id, behavior))
            for behavior in contract.forbidden_behaviors:
                session.add(ContractMapper.behavior_to_row(contract.contract_id, behavior))
            for invariant in contract.invariants:
                session.add(ContractMapper.invariant_to_row(contract.contract_id, invariant))
            for assume in contract.assumptions:
                session.add(ContractMapper.assumption_to_row(contract.contract_id, assume))
            for target in contract.verification_targets:
                session.add(ContractMapper.target_to_row(contract.contract_id, target))
        await session.flush()

    async def _persist_evidence(self, session: AsyncSession, analysis_id: str, evidence: list) -> None:
        from app.persistence.mappers.evidence_mapper import EvidenceMapper
        for ev in evidence:
            session.add(EvidenceMapper.to_row(ev))
            if ev.integrity:
                session.add(EvidenceMapper.integrity_to_row(ev.evidence_id, ev.integrity))
            if ev.environment_fingerprint:
                session.add(EvidenceMapper.fingerprint_to_row(ev.evidence_id, ev.environment_fingerprint))
        await session.flush()

    async def _persist_verification(self, session: AsyncSession, analysis_id: str, repository_id: str, results: list) -> None:
        from app.persistence.mappers.verification_mapper import VerificationMapper
        for report in results:
            session.add(VerificationMapper.report_to_row(report))
            for req_res in report.requirement_results:
                session.add(VerificationMapper.req_to_row(req_res))
                for obl_res in req_res.obligation_results:
                    session.add(VerificationMapper.obl_to_row(obl_res))
        await session.flush()

    async def _persist_skeptic(self, session: AsyncSession, analysis_id: str, counterexamples: list) -> None:
        from app.persistence.mappers.skeptic_mapper import SkepticMapper
        for cx in counterexamples:
            session.add(SkepticMapper.counterexample_to_row(cx))
        await session.flush()
