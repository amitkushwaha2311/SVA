from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.persistence.database import get_db
from app.persistence.models.user import UserRow, WorkspaceMembershipRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.intent import IntentCandidateRow
from app.persistence.models.contract import SemanticContractRow
from app.persistence.models.evidence import EvidenceRow
from app.persistence.models.verification import VerificationReportRow
from app.api.dependencies import get_current_user, require_workspace_member

from app.api.routers.v1.schemas import AnalysisResponse, AnalysisListResponse

router = APIRouter(prefix="/v1/analyses", tags=["analyses"])

async def _verify_analysis_access(workspace_id: str, analysis_id: str, current_user: UserRow, db: AsyncSession) -> AnalysisRow:
    """Helper to verify workspace access and analysis existence."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    # Check if analysis exists and belongs to a repo in this workspace
    stmt = select(AnalysisRow).join(RepositoryRow).where(
        AnalysisRow.id == analysis_id,
        RepositoryRow.workspace_id == workspace_id
    )
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return analysis

@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    workspace_id: str,
    repository_id: str = None,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    stmt = select(AnalysisRow).join(RepositoryRow).where(
        RepositoryRow.workspace_id == workspace_id
    )
    if repository_id:
        stmt = stmt.where(AnalysisRow.repository_id == repository_id)
        
    analyses = (await db.execute(stmt)).scalars().all()
    return AnalysisListResponse(analyses=analyses)

@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await _verify_analysis_access(workspace_id, analysis_id, current_user, db)

@router.get("/{analysis_id}/intent")
async def get_analysis_intent(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await _verify_analysis_access(workspace_id, analysis_id, current_user, db)
    stmt = select(IntentCandidateRow).where(IntentCandidateRow.analysis_id == analysis_id)
    intents = (await db.execute(stmt)).scalars().all()
    
    # We serialize manually for now
    return [{"id": i.id, "statement": i.original_statement, "source": i.source_file, "provenance": i.provenance, "status": i.status} for i in intents]

@router.get("/{analysis_id}/contracts")
async def get_analysis_contracts(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await _verify_analysis_access(workspace_id, analysis_id, current_user, db)
    stmt = select(SemanticContractRow).where(SemanticContractRow.analysis_id == analysis_id)
    contracts = (await db.execute(stmt)).scalars().all()
    return [{"id": c.id, "requirement_id": c.requirement_id, "status": c.status, "version": c.version} for c in contracts]

@router.get("/{analysis_id}/evidence")
async def get_analysis_evidence(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    analysis = await _verify_analysis_access(workspace_id, analysis_id, current_user, db)
    stmt = select(EvidenceRow).where(EvidenceRow.repository_id == analysis.repository_id)
    evidence = (await db.execute(stmt)).scalars().all()
    return [{"id": e.id, "method": e.method, "result": e.result, "status": e.status} for e in evidence]

@router.get("/{analysis_id}/verification")
async def get_analysis_verification(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await _verify_analysis_access(workspace_id, analysis_id, current_user, db)
    stmt = select(VerificationReportRow).where(VerificationReportRow.analysis_id == analysis_id)
    reports = (await db.execute(stmt)).scalars().all()
    return [{"id": r.id, "status": r.overall_status, "created_at": r.created_at} for r in reports]

@router.get("/{analysis_id}/graph")
async def get_analysis_graph(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the real graph of assurance objects.
    """
    await _verify_analysis_access(workspace_id, analysis_id, current_user, db)
    
    # We would build nodes and edges from actual data here.
    # For now, return basic nodes for the intent to start with.
    nodes = []
    edges = []
    
    intent_stmt = select(IntentCandidateRow).where(IntentCandidateRow.analysis_id == analysis_id)
    intents = (await db.execute(intent_stmt)).scalars().all()
    for i in intents:
        nodes.append({
            "id": i.id,
            "type": "intent",
            "data": {"label": i.id, "statement": i.original_statement, "status": i.status}
        })
        
    contract_stmt = select(SemanticContractRow).where(SemanticContractRow.analysis_id == analysis_id)
    contracts = (await db.execute(contract_stmt)).scalars().all()
    for c in contracts:
        nodes.append({
            "id": c.id,
            "type": "contract",
            "data": {"label": c.id, "requirement_id": c.requirement_id, "status": c.status}
        })
        # If we had requirement nodes, we would edge to them. But intent relates to contract via requirement.
        
    return {"nodes": nodes, "edges": edges}
