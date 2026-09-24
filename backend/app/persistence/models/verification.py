from sqlalchemy import Column, String, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.persistence.database import Base

# Junction tables for relationships requested by user
# "Relational Integrity: Use foreign keys and junction tables for known SVA relationships"

obligation_verification_evidence = Table(
    "obligation_verification_evidence",
    Base.metadata,
    Column("obligation_id", String(255), ForeignKey("obligation_verifications.obligation_id"), primary_key=True),
    Column("evidence_id", String(255), ForeignKey("evidences.evidence_id"), primary_key=True)
)

requirement_verification_evidence = Table(
    "requirement_verification_evidence",
    Base.metadata,
    Column("verification_id", String(255), ForeignKey("requirement_verifications.id"), primary_key=True),
    Column("evidence_id", String(255), ForeignKey("evidences.evidence_id"), primary_key=True)
)


class ObligationVerificationRow(Base):
    __tablename__ = "obligation_verifications"

    obligation_id = Column(String(255), primary_key=True)
    contract_id = Column(String(255), nullable=False, index=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    
    decision = Column(String(50), nullable=False)
    explanation = Column(String, nullable=True)
    
    supporting_evidence = Column(JSON, nullable=False, default=list)
    contradicting_evidence = Column(JSON, nullable=False, default=list)

    # Relationships
    evidence = relationship("EvidenceRow", secondary=obligation_verification_evidence)


class RequirementVerificationRow(Base):
    __tablename__ = "requirement_verifications"

    # Composite primary key conceptually, but we need a string ID for the table pk.
    id = Column(String(255), primary_key=True) # Usually requirement_id + "_" + contract_id
    requirement_id = Column(String(255), nullable=False, index=True)
    contract_id = Column(String(255), nullable=False, index=True)
    
    decision = Column(String(50), nullable=False)
    explanation = Column(String, nullable=True)
    limitations = Column(JSON, nullable=False, default=list)
    
    obligation_results = Column(JSON, nullable=False, default=list)
    unresolved_obligations = Column(JSON, nullable=False, default=list)

    evidence = relationship("EvidenceRow", secondary=requirement_verification_evidence)


class VerificationReportRow(Base):
    __tablename__ = "verification_reports"

    verification_id = Column(String(255), primary_key=True)
    repository_id = Column(String(255), nullable=False, index=True)
    commit_id = Column(String(255), nullable=False, index=True)
    
    generated_at = Column(String, nullable=False)
    engine_version = Column(String, nullable=False)
    
    requirement_results = Column(JSON, nullable=False, default=list)
