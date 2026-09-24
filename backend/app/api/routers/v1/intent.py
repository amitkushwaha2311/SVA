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

router = APIRouter(prefix="/v1/intent", tags=["intent"])


@router.get("/", response_model=IntentListResponse)
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

        items.append(IntentResponse(
            id=c.candidate_id,
            original_statement=c.original_statement,
            source_file=source_file,
            source_line=source_line,
            provenance=c.provenance.get("type") if isinstance(c.provenance, dict) else str(c.provenance) if c.provenance else None,
            extraction_method=c.extraction_method,
            status=c.status,
            analysis_id=c.analysis_id,
        ))

    return IntentListResponse(items=items)
