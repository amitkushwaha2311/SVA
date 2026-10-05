import asyncio
import os
# Override the database URL before importing anything else
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./sva_dev.db"

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select

# Import after overriding env
from app.api.main import app
from app.persistence.database import async_session_maker
from app.persistence.models import UserRow, WorkspaceRow, AnalysisRow, IntentCandidateRow, IntentConfirmationEventRow, SemanticRequirementRow, SemanticContractRow, VerificationTargetRow, RequirementVerificationRow, EvidenceRow
from app.semantic_ir.models import IntentState

async def setup_db():
    async with async_session_maker() as session:
        # Create table manually if it doesn't exist
        await session.execute(text('''
            CREATE TABLE IF NOT EXISTS intent_confirmation_events (
                event_id VARCHAR(36) NOT NULL, 
                candidate_id VARCHAR(255) NOT NULL, 
                analysis_id VARCHAR(255) NOT NULL, 
                workspace_id VARCHAR(36) NOT NULL, 
                confirmed_by_user_id VARCHAR(36), 
                confirmed_at DATETIME NOT NULL, 
                action VARCHAR(20) NOT NULL, 
                PRIMARY KEY (event_id), 
                FOREIGN KEY(candidate_id) REFERENCES intent_candidates (candidate_id) ON DELETE CASCADE, 
                FOREIGN KEY(confirmed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        '''))
        await session.commit()

async def run_analysis(workspace_id: str, repo_id: str):
    from app.api.routers.v1.analyses import start_analysis
    # We can trigger it via the backend orchestrator directly
    from app.orchestrator.engine import OrchestratorEngine
    engine = OrchestratorEngine()
    analysis_id = await engine.start_analysis(repo_id, commit_id="main")
    
    # Poll until completed
    from app.persistence.repositories.analysis_repo import AnalysisRepository
    async with async_session_maker() as session:
        repo = AnalysisRepository(session)
        while True:
            analysis = await repo.get_analysis(analysis_id)
            if analysis.status in ["COMPLETED", "FAILED"]:
                break
            await asyncio.sleep(1)
    
    return analysis_id

async def main():
    await setup_db()
    
    async with async_session_maker() as db:
        user = (await db.execute(select(UserRow).limit(1))).scalar_one_or_none()
        ws = (await db.execute(select(WorkspaceRow).limit(1))).scalar_one_or_none()
        
        # Find candidate: "Only project owners can delete projects."
        stmt = select(AnalysisRow.id, AnalysisRow.repository_id, IntentCandidateRow.candidate_id, IntentCandidateRow.original_statement)\
            .join(IntentCandidateRow, AnalysisRow.id == IntentCandidateRow.analysis_id)\
            .where(IntentCandidateRow.original_statement.like('%Only project owners can delete projects%')).limit(1)
        res = (await db.execute(stmt)).first()
        
        if not res:
            print("Target candidate not found in db.")
            return
            
        analysis_id, repo_id, candidate_id, stmt_text = res
        print(f"Found Candidate '{candidate_id}' in Analysis '{analysis_id}' for Repo '{repo_id}'")

        # Mock current user for endpoints
        from app.api.dependencies import get_current_user
        app.dependency_overrides[get_current_user] = lambda: user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("1. GET intent API...")
        get_resp = await ac.get(f"/api/v1/intent/?workspace_id={ws.id}&analysis_id={analysis_id}")
        assert get_resp.status_code == 200
        items = get_resp.json()["items"]
        
        item = next(i for i in items if i["id"] == candidate_id)
        print("2. Initial State:", "human_confirmed =", item["human_confirmed"], "actor =", item["actor"], "action =", item["action"])
        assert item["human_confirmed"] is False
        assert item["actor"] == "project owner"
        
        print("3. Calling confirmation API...")
        post_resp = await ac.post(f"/api/v1/intent/{candidate_id}/confirm?workspace_id={ws.id}&analysis_id={analysis_id}")
        assert post_resp.status_code == 200
        
        print("4. Verify database state...")
        async with async_session_maker() as db:
            c = (await db.execute(select(IntentCandidateRow).where(IntentCandidateRow.candidate_id == candidate_id))).scalar_one()
            assert c.human_confirmed is True
            print(f"IntentCandidateRow human_confirmed = {c.human_confirmed}")
            
            print("5. Verify IntentConfirmationEventRow...")
            events = (await db.execute(select(IntentConfirmationEventRow).where(IntentConfirmationEventRow.candidate_id == candidate_id))).scalars().all()
            assert len(events) == 1
            print(f"Found 1 event: {events[0].action}")

        print("6. Verify GET intent again...")
        get_resp2 = await ac.get(f"/api/v1/intent/?workspace_id={ws.id}&analysis_id={analysis_id}")
        item2 = next(i for i in get_resp2.json()["items"] if i["id"] == candidate_id)
        assert item2["human_confirmed"] is True
        print(f"GET confirms human_confirmed = {item2['human_confirmed']}")

        print(f"7. Running a NEW analysis for repository {repo_id}...")
        new_analysis_id = await run_analysis(ws.id, repo_id)
        print(f"New analysis completed: {new_analysis_id}")
        
        async with async_session_maker() as db:
            # 8. Verify SemanticRequirement
            req = (await db.execute(
                select(SemanticRequirementRow)
                .where(SemanticRequirementRow.analysis_id == new_analysis_id)
                .where(SemanticRequirementRow.candidate_id == candidate_id)
            )).scalar_one_or_none()
            
            if not req:
                print("STOP: SemanticRequirement not found for the new analysis.")
                return
                
            print(f"8. Created SemanticRequirement '{req.requirement_id}' with status: {req.status}")
            assert req.status == IntentState.HUMAN_CONFIRMED.value, f"Expected HUMAN_CONFIRMED, got {req.status}"
            
            # 9. Verify Contract
            contract = (await db.execute(
                select(SemanticContractRow)
                .where(SemanticContractRow.analysis_id == new_analysis_id)
                .where(SemanticContractRow.requirement_id == req.requirement_id)
            )).scalar_one_or_none()
            
            if not contract:
                print("STOP: ContractCompiler did not produce a SemanticContract (or not found in DB).")
                return
                
            print(f"9. ContractCompiler produced Contract '{contract.contract_id}' with status {contract.status}")
            
            # 10. Verify verification targets
            vt_rows = (await db.execute(
                select(VerificationTargetRow).where(VerificationTargetRow.contract_id == contract.contract_id)
            )).scalars().all()
            
            print(f"10. Contract has {len(vt_rows)} verification targets.")
            
            # 11. Check Evidence/Verification
            req_ver = (await db.execute(
                select(RequirementVerificationRow).where(RequirementVerificationRow.analysis_id == new_analysis_id)
            )).scalars().all()
            
            evidences = (await db.execute(
                select(EvidenceRow).where(EvidenceRow.analysis_id == new_analysis_id)
            )).scalars().all()
            
            print(f"11. Verification count: {len(req_ver)}, Evidence count: {len(evidences)}")
            print("E2E Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())
