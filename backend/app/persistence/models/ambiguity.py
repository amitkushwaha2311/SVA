from sqlalchemy import Column, String, JSON, ForeignKey, Float
from app.persistence.database import Base

class AmbiguityCaseRow(Base):
    __tablename__ = "ambiguity_cases"

    ambiguity_id = Column(String(255), primary_key=True)
    statement = Column(String, nullable=False)
    
    # JSON for lists of strings
    requirement_ids = Column(JSON, nullable=False, default=list)
    candidate_ids = Column(JSON, nullable=False, default=list)
    ambiguity_types = Column(JSON, nullable=False, default=list)

class InterpretationRow(Base):
    __tablename__ = "interpretations"

    interpretation_id = Column(String(255), primary_key=True)
    ambiguity_id = Column(String(255), ForeignKey("ambiguity_cases.ambiguity_id"), nullable=False, index=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    
    statement = Column(String, nullable=False)
    interpretation_method = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    semantic_fields = Column(JSON, nullable=True)
    assumptions = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=True)

class ClarificationQuestionRow(Base):
    __tablename__ = "clarification_questions"

    question_id = Column(String(255), primary_key=True)
    ambiguity_id = Column(String(255), ForeignKey("ambiguity_cases.ambiguity_id"), nullable=False, index=True)
    question = Column(String, nullable=False)
    distinguishing_scenario_id = Column(String(255), nullable=True)
    information_gain = Column(Float, nullable=True)
    status = Column(String(50), nullable=False)
    
    options = Column(JSON, nullable=False, default=list)

