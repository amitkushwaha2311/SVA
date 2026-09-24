from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.contracts.models import SemanticContract
from app.persistence.models.contract import SemanticContractRow
from app.persistence.mappers.contract_mapper import ContractMapper


class ContractRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, contract: SemanticContract) -> None:
        """
        Save a contract. Preserves version history via parent_contract_id.
        Does NOT overwrite existing contract rows — each version is a new row.
        """
        row = ContractMapper.contract_to_row(contract)
        self.session.add(row)
        await self.session.flush()

    async def get_by_id(self, contract_id: str) -> Optional[SemanticContractRow]:
        stmt = select(SemanticContractRow).where(SemanticContractRow.contract_id == contract_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version_history(self, contract_id: str) -> List[SemanticContractRow]:
        """
        Walk the version history from a given contract ID backwards.
        """
        history = []
        current_id = contract_id
        while current_id:
            stmt = select(SemanticContractRow).where(SemanticContractRow.contract_id == current_id)
            result = await self.session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                break
            history.append(row)
            current_id = row.parent_contract_id
        return history

    async def get_by_requirement(self, requirement_id: str) -> List[SemanticContractRow]:
        stmt = select(SemanticContractRow).where(SemanticContractRow.requirement_id == requirement_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
