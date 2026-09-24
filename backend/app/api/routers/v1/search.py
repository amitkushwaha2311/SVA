from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast
from typing import List

from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.intent import IntentCandidateRow
from app.persistence.models.contract import SemanticContractRow
from app.persistence.models.evidence import EvidenceRow
from app.api.dependencies import get_current_user, require_workspace_member

from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    type: str
    label: str
    href: str
    repository_id: str = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

router = APIRouter(prefix="/v1/search", tags=["search"])

@router.get("/", response_model=SearchResponse)
async def search_all(
    workspace_id: str,
    q: str = Query(..., min_length=1),
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Global search across workspace resources."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    results = []
    q_pattern = f"%{q}%"
    q_lower = f"%{q.lower()}%"
    
    # 1. Repositories
    repo_stmt = select(RepositoryRow).where(
        RepositoryRow.workspace_id == workspace_id,
        RepositoryRow.name.ilike(q_pattern)
    ).limit(5)
    repos = (await db.execute(repo_stmt)).scalars().all()
    
    repo_ids = []
    for r in repos:
        repo_ids.append(r.id)
        results.append(SearchResult(
            id=r.id, type="repository", label=r.name, href=f"/repositories/{r.id}", repository_id=r.id
        ))
        
    # Get all repo IDs for this workspace to scope other searches securely
    all_workspace_repo_stmt = select(RepositoryRow.id).where(RepositoryRow.workspace_id == workspace_id)
    all_repo_ids = (await db.execute(all_workspace_repo_stmt)).scalars().all()
    
    if not all_repo_ids:
        return SearchResponse(results=results)
        
    # 2. Analyses
    analysis_stmt = select(AnalysisRow).where(
        AnalysisRow.repository_id.in_(all_repo_ids),
        or_(
            cast(AnalysisRow.id, String).ilike(q_pattern),
            AnalysisRow.commit_id.ilike(q_pattern)
        )
    ).limit(5)
    analyses = (await db.execute(analysis_stmt)).scalars().all()
    for a in analyses:
        results.append(SearchResult(
            id=a.id, type="analysis", label=f"Analysis {a.commit_id[:7] if a.commit_id else a.id[:7]}", 
            href=f"/repositories/{a.repository_id}", repository_id=a.repository_id
        ))
        
    # 3. Intents (Requirements)
    intent_stmt = select(IntentCandidateRow, AnalysisRow.repository_id).join(
        AnalysisRow, IntentCandidateRow.analysis_id == AnalysisRow.id
    ).where(
        AnalysisRow.repository_id.in_(all_repo_ids),
        IntentCandidateRow.original_statement.ilike(q_pattern)
    ).limit(5)
    intents = (await db.execute(intent_stmt)).all()
    for row in intents:
        i = row[0]
        rep_id = row[1]
        results.append(SearchResult(
            id=i.id, type="intent", label=i.original_statement[:100], href="/intent", repository_id=rep_id
        ))

    # 4. Contracts
    contract_stmt = select(SemanticContractRow, AnalysisRow.repository_id).join(
        AnalysisRow, SemanticContractRow.analysis_id == AnalysisRow.id
    ).where(
        AnalysisRow.repository_id.in_(all_repo_ids),
        SemanticContractRow.statement.ilike(q_pattern)
    ).limit(5)
    contracts = (await db.execute(contract_stmt)).all()
    for row in contracts:
        c = row[0]
        rep_id = row[1]
        results.append(SearchResult(
            id=c.id, type="contract", label=c.statement[:100], href="/contracts", repository_id=rep_id
        ))
        
    # 5. Evidence
    evidence_stmt = select(EvidenceRow).where(
        EvidenceRow.repository_id.in_(all_repo_ids),
        or_(
            EvidenceRow.description.ilike(q_pattern),
            EvidenceRow.method.ilike(q_pattern)
        )
    ).limit(5)
    evidence_rows = (await db.execute(evidence_stmt)).scalars().all()
    for e in evidence_rows:
        results.append(SearchResult(
            id=e.id, type="evidence", label=(e.description or e.method or e.id)[:100], href="/evidence", repository_id=e.repository_id
        ))

    return SearchResponse(results=results)
