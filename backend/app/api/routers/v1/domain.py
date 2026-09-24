"""
Phase 16 v1 API: Ambiguity, Drift, Verification, and Activity endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone

from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.ambiguity import AmbiguityCaseRow, InterpretationRow, ClarificationQuestionRow
from app.persistence.models.drift import DriftReportRow
from app.persistence.models.verification import ObligationVerificationRow, RequirementVerificationRow
from app.api.dependencies import get_current_user, require_workspace_member
from app.api.routers.v1.schemas import (
    AmbiguityCaseResponse,
    AmbiguityListResponse,
    InterpretationResponse,
    ClarificationQuestionResponse,
    DriftReportResponse,
    DriftListResponse,
    ObligationVerificationResponse,
    RequirementVerificationResponse,
    VerificationListResponse,
)

# ─── Ambiguity ────────────────────────────────────────────────────────────────
ambiguity_router = APIRouter(prefix="/v1/ambiguity", tags=["ambiguity"])


async def _assert_analysis_in_workspace(
    workspace_id: str, analysis_id: str, current_user: UserRow, db: AsyncSession
) -> AnalysisRow:
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    stmt = (
        select(AnalysisRow)
        .join(RepositoryRow, AnalysisRow.repository_id == RepositoryRow.id)
        .where(AnalysisRow.id == analysis_id, RepositoryRow.workspace_id == workspace_id)
    )
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@ambiguity_router.get("/", response_model=AmbiguityListResponse)
async def list_ambiguity(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_analysis_in_workspace(workspace_id, analysis_id, current_user, db)

    # Ambiguity cases are linked via candidate_ids stored in analysis.
    # We query by analysis_id through intent candidates.
    from app.persistence.models.intent import IntentCandidateRow
    candidate_ids = (
        await db.execute(
            select(IntentCandidateRow.id).where(IntentCandidateRow.analysis_id == analysis_id)
        )
    ).scalars().all()

    if not candidate_ids:
        return AmbiguityListResponse(items=[])

    cases = (
        await db.execute(
            select(AmbiguityCaseRow)
        )
    ).scalars().all()

    # Filter to cases that reference any candidate from this analysis
    filtered = [c for c in cases if any(cid in (c.candidate_ids or []) for cid in candidate_ids)]

    items = []
    for case in filtered:
        interps = (
            await db.execute(
                select(InterpretationRow).where(InterpretationRow.ambiguity_id == case.ambiguity_id)
            )
        ).scalars().all()
        questions = (
            await db.execute(
                select(ClarificationQuestionRow).where(ClarificationQuestionRow.ambiguity_id == case.ambiguity_id)
            )
        ).scalars().all()

        items.append(AmbiguityCaseResponse(
            ambiguity_id=case.ambiguity_id,
            statement=case.statement,
            requirement_ids=case.requirement_ids or [],
            candidate_ids=case.candidate_ids or [],
            ambiguity_types=case.ambiguity_types or [],
            interpretations=[InterpretationResponse.model_validate(i) for i in interps],
            questions=[ClarificationQuestionResponse.model_validate(q) for q in questions],
        ))

    return AmbiguityListResponse(items=items)


# ─── Verification ─────────────────────────────────────────────────────────────
verification_router = APIRouter(prefix="/v1/verification", tags=["verification"])


@verification_router.get("/", response_model=VerificationListResponse)
async def list_verification(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    analysis = await _assert_analysis_in_workspace(workspace_id, analysis_id, current_user, db)

    req_verifications = (
        await db.execute(
            select(RequirementVerificationRow).where(
                RequirementVerificationRow.contract_id.in_(
                    select(AnalysisRow.id).where(AnalysisRow.id == analysis_id)
                )
            )
        )
    ).scalars().all()
    # Simpler: fetch requirement verifications where contract belongs to analysis
    from app.persistence.models.contract import SemanticContractRow
    contract_ids = (
        await db.execute(
            select(SemanticContractRow.contract_id).where(SemanticContractRow.analysis_id == analysis_id)
        )
    ).scalars().all()

    req_v = (
        await db.execute(
            select(RequirementVerificationRow).where(
                RequirementVerificationRow.contract_id.in_(contract_ids)
            )
        )
    ).scalars().all()

    obl_v = (
        await db.execute(
            select(ObligationVerificationRow).where(
                ObligationVerificationRow.contract_id.in_(contract_ids)
            )
        )
    ).scalars().all()

    return VerificationListResponse(
        requirement_verifications=[RequirementVerificationResponse.model_validate(r) for r in req_v],
        obligation_verifications=[ObligationVerificationResponse.model_validate(o) for o in obl_v],
    )


# ─── Drift ────────────────────────────────────────────────────────────────────
drift_router = APIRouter(prefix="/v1/drift", tags=["drift"])


@drift_router.get("/", response_model=DriftListResponse)
async def list_drift(
    workspace_id: str,
    repository_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    repo = (
        await db.execute(
            select(RepositoryRow).where(
                RepositoryRow.id == repository_id,
                RepositoryRow.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    reports = (
        await db.execute(
            select(DriftReportRow)
            .where(DriftReportRow.repository_id == repository_id)
            .order_by(desc(DriftReportRow.drift_id))
            .limit(50)
        )
    ).scalars().all()

    return DriftListResponse(items=[DriftReportResponse.model_validate(r) for r in reports])


@drift_router.get("/{drift_id}", response_model=DriftReportResponse)
async def get_drift_report(
    workspace_id: str,
    drift_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    repos = (
        await db.execute(
            select(RepositoryRow.id).where(RepositoryRow.workspace_id == workspace_id)
        )
    ).scalars().all()

    report = (
        await db.execute(
            select(DriftReportRow).where(
                DriftReportRow.drift_id == drift_id,
                DriftReportRow.repository_id.in_(repos),
            )
        )
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Drift report not found")

    return DriftReportResponse.model_validate(report)
