import asyncio
import os
from pathlib import Path
import sys

# Configure UTF-8 stdout so Windows console won't crash on Unicode characters like '→'
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

# Default to backend/sva.db if DATABASE_URL is not explicitly set
if "DATABASE_URL" not in os.environ:
    db_file = BACKEND_DIR / "sva.db"
    if not db_file.exists():
        db_file = BACKEND_DIR / "sva_dev.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"

from sqlalchemy import func, select
from app.persistence.database import AsyncSessionLocal
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.intent import IntentCandidateRow
from app.persistence.models.contract import SemanticContractRow, VerificationTargetRow
from app.persistence.models.evidence import EvidenceRow
from app.persistence.models.verification import VerificationReportRow

async def main():
    print(f"Connecting to database: {os.environ.get('DATABASE_URL')}\n")
    async with AsyncSessionLocal() as session:
        # Repositories
        result = await session.execute(select(RepositoryRow))
        repos = result.scalars().all()
        print(f"=== Repositories ({len(repos)}) ===")
        for r in repos:
            print(f"  Repo ID: {r.id} | Identifier: {r.repository_identifier} | Provider: {r.provider_type}")

        # Analyses
        result = await session.execute(select(AnalysisRow).order_by(AnalysisRow.created_at.desc()))
        analyses = result.scalars().all()
        print(f"\n=== Analyses ({len(analyses)}) ===")
        for a in analyses:
            print(f"  Analysis ID: {a.id}")
            print(f"    Repo ID: {a.repository_id} | Status: {a.status} | Commit: {a.commit_id}")
            if a.error_message:
                print(f"    Error: {a.error_message}")

            # Counts of associated entities
            intents = (await session.execute(
                select(func.count(IntentCandidateRow.candidate_id)).where(IntentCandidateRow.analysis_id == a.id)
            )).scalar() or 0

            contracts = (await session.execute(
                select(func.count(SemanticContractRow.contract_id)).where(SemanticContractRow.analysis_id == a.id)
            )).scalar() or 0

            evidence = (await session.execute(
                select(func.count(EvidenceRow.evidence_id)).where(EvidenceRow.contract_id.in_(
                    select(SemanticContractRow.contract_id).where(SemanticContractRow.analysis_id == a.id)
                ))
            )).scalar() or 0

            reports = (await session.execute(
                select(func.count(VerificationReportRow.verification_id)).where(VerificationReportRow.verification_id.like(f"%{a.id}%"))
            )).scalar() or 0

            print(f"    Domain Data -> Intents: {intents} | Contracts: {contracts} | Evidence: {evidence} | Reports: {reports}\n")

if __name__ == "__main__":
    asyncio.run(main())

