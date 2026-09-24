from sqlalchemy import Column, String, JSON, ForeignKey
from app.persistence.database import Base

class SemanticContractRow(Base):
    __tablename__ = "semantic_contracts"

    contract_id = Column(String(255), primary_key=True)
    contract_version = Column(String(50), nullable=False)
    parent_contract_id = Column(String(255), ForeignKey("semantic_contracts.contract_id"), nullable=True, index=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    candidate_id = Column(String(255), nullable=True, index=True)
    analysis_id = Column(String(255), nullable=False, index=True)
    
    statement = Column(String, nullable=False)
    compilation_status = Column(String(50), nullable=False)
    
    source_refs = Column(JSON, nullable=False, default=list)

class BehaviorExpectationRow(Base):
    __tablename__ = "behavior_expectations"

    behavior_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), ForeignKey("semantic_contracts.contract_id"), nullable=False, index=True)
    is_allowed = Column(String(50), nullable=False) # 'allowed' or 'forbidden'

    description = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    action = Column(String, nullable=True)
    resource = Column(String, nullable=True)
    expected_outcome = Column(String, nullable=True)
    
    provenance = Column(JSON, nullable=True)

class InvariantRow(Base):
    __tablename__ = "invariants"

    invariant_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), ForeignKey("semantic_contracts.contract_id"), nullable=False, index=True)
    statement = Column(String, nullable=False)
    
    provenance = Column(JSON, nullable=True)
    source_refs = Column(JSON, nullable=False, default=list)

class ContractAssumptionRow(Base):
    __tablename__ = "contract_assumptions"

    assumption_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), ForeignKey("semantic_contracts.contract_id"), nullable=False, index=True)
    statement = Column(String, nullable=False)
    
    provenance = Column(JSON, nullable=True)

class VerificationTargetRow(Base):
    __tablename__ = "verification_targets"

    target_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), ForeignKey("semantic_contracts.contract_id"), nullable=False, index=True)
    
    category = Column(String(50), nullable=False)
    description = Column(String, nullable=False)
    code_entity_ref = Column(JSON, nullable=True)
