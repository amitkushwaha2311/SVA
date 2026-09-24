"""
Phase 16 v1 API: Contracts endpoints.
All routes enforce workspace membership. SQLAlchemy models are never exposed directly.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.contract import (
    SemanticContractRow,
    BehaviorExpectationRow,
    InvariantRow,
    ContractAssumptionRow,
    VerificationTargetRow,
)
from app.api.dependencies import get_current_user, require_workspace_member
from app.api.routers.v1.schemas import (
    ContractResponse,
    ContractListResponse,
    BehaviorExpectationResponse,
    InvariantResponse,
    ContractAssumptionResponse,
    VerificationTargetResponse,
)

router = APIRouter(prefix="/v1/contracts", tags=["contracts"])


async def _assert_workspace_analysis(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow,
    db: AsyncSession,
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


async def _build_contract_response(contract: SemanticContractRow, db: AsyncSession) -> ContractResponse:
    behaviors = (
        await db.execute(
            select(BehaviorExpectationRow).where(BehaviorExpectationRow.contract_id == contract.contract_id)
        )
    ).scalars().all()

    invariants = (
        await db.execute(
            select(InvariantRow).where(InvariantRow.contract_id == contract.contract_id)
        )
    ).scalars().all()

    assumptions = (
        await db.execute(
            select(ContractAssumptionRow).where(ContractAssumptionRow.contract_id == contract.contract_id)
        )
    ).scalars().all()

    targets = (
        await db.execute(
            select(VerificationTargetRow).where(VerificationTargetRow.contract_id == contract.contract_id)
        )
    ).scalars().all()

    return ContractResponse(
        contract_id=contract.contract_id,
        contract_version=contract.contract_version,
        parent_contract_id=contract.parent_contract_id,
        requirement_id=contract.requirement_id,
        candidate_id=contract.candidate_id,
        analysis_id=contract.analysis_id,
        statement=contract.statement,
        compilation_status=contract.compilation_status,
        source_refs=contract.source_refs or [],
        behaviors=[BehaviorExpectationResponse.model_validate(b) for b in behaviors],
        invariants=[InvariantResponse.model_validate(i) for i in invariants],
        assumptions=[ContractAssumptionResponse.model_validate(a) for a in assumptions],
        targets=[VerificationTargetResponse.model_validate(t) for t in targets],
    )


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all contracts for an analysis, scoped to the authenticated workspace."""
    await _assert_workspace_analysis(workspace_id, analysis_id, current_user, db)

    contracts = (
        await db.execute(
            select(SemanticContractRow).where(SemanticContractRow.analysis_id == analysis_id)
        )
    ).scalars().all()

    items = [await _build_contract_response(c, db) for c in contracts]
    return ContractListResponse(items=items)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    workspace_id: str,
    analysis_id: str,
    contract_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_workspace_analysis(workspace_id, analysis_id, current_user, db)
    contract = (
        await db.execute(
            select(SemanticContractRow).where(
                SemanticContractRow.contract_id == contract_id,
                SemanticContractRow.analysis_id == analysis_id,
            )
        )
    ).scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return await _build_contract_response(contract, db)
