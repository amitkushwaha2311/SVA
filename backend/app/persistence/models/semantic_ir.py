from sqlalchemy import Column, String, JSON
from app.persistence.database import Base

class SemanticRequirementRow(Base):
    __tablename__ = "semantic_requirements"

    requirement_id = Column(String(255), primary_key=True)
    candidate_id = Column(String(255), nullable=True, index=True)
    analysis_id = Column(String(255), nullable=False, index=True)
    
    statement = Column(String, nullable=False)
    original_statement = Column(String, nullable=False)
    status = Column(String(50), nullable=False)

    sources = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=True)

class SemanticConditionRow(Base):
    __tablename__ = "semantic_conditions"

    id = Column(String(255), primary_key=True)
    requirement_id = Column(String(255), nullable=False, index=True)
    statement = Column(String, nullable=False)
    status = Column(String(50), nullable=False)
    
    source_refs = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=True)
