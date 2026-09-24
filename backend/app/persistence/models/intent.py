from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship

from app.persistence.database import Base


class IntentCandidateRow(Base):
    __tablename__ = "intent_candidates"

    candidate_id = Column(String(255), primary_key=True)
    analysis_id = Column(String(255), nullable=False, index=True)
    original_statement = Column(String, nullable=False)
    normalized_statement = Column(String, nullable=True)
    status = Column(String(50), nullable=False)
    human_confirmed = Column(Boolean, nullable=False, default=False)
    extraction_method = Column(String(50), nullable=False)
    
    # JSON composites
    sources = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=False, default=list)

