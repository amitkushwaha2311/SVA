from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from app.persistence.database import Base

class EvidenceRow(Base):
    __tablename__ = "evidences"

    evidence_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), nullable=True, index=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    repository_id = Column(String(255), nullable=False, index=True)
    commit_id = Column(String(255), nullable=False, index=True)
    
    evidence_type = Column(String(50), nullable=False)
    verification_method = Column(String(50), nullable=False)
    result = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    
    description = Column(String, nullable=False)
    observation = Column(String, nullable=False)
    
    collected_at = Column(String, nullable=False) # Keep as ISO string to preserve exact SVA formatting
    
    # Relationships 
    # Integrity and fingerprint are usually 1:1, so we map them to their own tables
    
class EvidenceIntegrityRow(Base):
    __tablename__ = "evidence_integrities"

    evidence_id = Column(String(255), ForeignKey("evidences.evidence_id"), primary_key=True)
    evidence_hash = Column(String, nullable=False)
    hash_algorithm = Column(String, nullable=False)
    
    input_hashes = Column(JSON, nullable=False, default=dict)
    parent_evidence_ids = Column(JSON, nullable=False, default=list)

class EnvironmentFingerprintRow(Base):
    __tablename__ = "environment_fingerprints"

    evidence_id = Column(String(255), ForeignKey("evidences.evidence_id"), primary_key=True)
    os_name = Column(String, nullable=True)
    python_version = Column(String, nullable=True)
    tool_name = Column(String, nullable=True)
    tool_version = Column(String, nullable=True)
    dependency_lock_hash = Column(String, nullable=True)
