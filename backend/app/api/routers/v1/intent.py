"""
Phase 16 v1 API: Intent endpoint (analysis-scoped).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.intent import IntentCandidateRow
from app.api.dependencies import get_current_user, require_workspace_member
from app.api.routers.v1.schemas import IntentListResponse, IntentResponse
from app.persistence.repositories.intent_repo import IntentRepository
from app.semantic_ir.builder import _extract_semantics
from app.repository.intent.models import Provenance

router = APIRouter(prefix="/v1/intent", tags=["intent"])


@router.get("", response_model=IntentListResponse)
async def list_intent(
    workspace_id: str,
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all intent candidates for an analysis, workspace-scoped."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    analysis = (
        await db.execute(
            select(AnalysisRow)
            .join(RepositoryRow, AnalysisRow.repository_id == RepositoryRow.id)
            .where(AnalysisRow.id == analysis_id, RepositoryRow.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    candidates = (
        await db.execute(
            select(IntentCandidateRow).where(IntentCandidateRow.analysis_id == analysis_id)
        )
    ).scalars().all()

    items = []
    for c in candidates:
        # Extract source file and line from sources JSON if available
        source_file = None
        source_line = None
        if c.sources:
            first = c.sources[0] if c.sources else {}
            source_file = first.get("file") or first.get("source_file")
            source_line = first.get("line") or first.get("source_line")

        # Re-extract semantics deterministically for the response
        statement = c.normalized_statement or c.original_statement
        
        # We need a proper Provenance enum if possible, or just pass None/DOCUMENT
        provenance_type = c.provenance.get("type") if isinstance(c.provenance, dict) else str(c.provenance) if c.provenance else None
        prov_enum = Provenance.DOCUMENT
        if provenance_type == "CODE":
            prov_enum = Provenance.CODE
        
        extracted = _extract_semantics(statement, prov_enum)

        items.append(IntentResponse(
            id=c.candidate_id,
            original_statement=c.original_statement,
            source_file=source_file,
            source_line=source_line,
            provenance=provenance_type,
            extraction_method=c.extraction_method,
            status=c.status,
            analysis_id=c.analysis_id,
            human_confirmed=c.human_confirmed,
            actor=extracted.actor.name if extracted.actor else None,
            action=extracted.action.name if extracted.action else None,
            resource=extracted.resource.name if extracted.resource else None,
            assumptions=[a.statement for a in extracted.assumptions] if extracted.assumptions else []
        ))

    return IntentListResponse(items=items)


@router.post("/{candidate_id}/confirm", response_model=IntentResponse)
async def confirm_intent(
    workspace_id: str,
    analysis_id: str,
    candidate_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly confirm an intent candidate."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    # Verify analysis belongs to workspace
    analysis = (
        await db.execute(
            select(AnalysisRow)
            .join(RepositoryRow, AnalysisRow.repository_id == RepositoryRow.id)
            .where(AnalysisRow.id == analysis_id, RepositoryRow.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    repo = IntentRepository(db)
    try:
        candidate = await repo.confirm_candidate(
            candidate_id=candidate_id,
            analysis_id=analysis_id,
            workspace_id=workspace_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    # Reconstruct the response identically to list_intent
    source_file = None
    source_line = None
    if candidate.sources:
        first = candidate.sources[0] if candidate.sources else {}
        source_file = first.get("file") or first.get("source_file")
        source_line = first.get("line") or first.get("source_line")

    statement = candidate.normalized_statement or candidate.original_statement
    provenance_type = candidate.provenance.get("type") if isinstance(candidate.provenance, dict) else str(candidate.provenance) if candidate.provenance else None
    prov_enum = Provenance.CODE if provenance_type == "CODE" else Provenance.DOCUMENT
    extracted = _extract_semantics(statement, prov_enum)

    return IntentResponse(
        id=candidate.candidate_id,
        original_statement=candidate.original_statement,
        source_file=source_file,
        source_line=source_line,
        provenance=provenance_type,
        extraction_method=candidate.extraction_method,
        status=candidate.status,
        analysis_id=candidate.analysis_id,
        human_confirmed=candidate.human_confirmed,
        actor=extracted.actor.name if extracted.actor else None,
        action=extracted.action.name if extracted.action else None,
        resource=extracted.resource.name if extracted.resource else None,
        assumptions=[a.statement for a in extracted.assumptions] if extracted.assumptions else []
    )
