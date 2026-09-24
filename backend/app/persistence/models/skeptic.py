from sqlalchemy import Column, String, JSON, Integer
from app.persistence.database import Base


class CounterexampleRow(Base):
    __tablename__ = "counterexamples"

    counterexample_id = Column(String(255), primary_key=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    contract_id = Column(String(255), nullable=True, index=True)
    obligation_id = Column(String(255), nullable=True, index=True)
    target_id = Column(String(255), nullable=True, index=True)
    
    scenario_id = Column(String(255), nullable=True)
    hypothesis = Column(String, nullable=False)
    
    preconditions = Column(JSON, nullable=False, default=list)


class SkepticReportRow(Base):
    __tablename__ = "skeptic_reports"

    report_id = Column(String(255), primary_key=True)
    requirement_id = Column(String(255), nullable=True, index=True)
    contract_id = Column(String(255), nullable=True, index=True)
    
    total_generated = Column(Integer, nullable=False, default=0)
    total_deduplicated = Column(Integer, nullable=False, default=0)
    
    strategies_applied = Column(JSON, nullable=False, default=list)
    counterexamples = Column(JSON, nullable=False, default=list)
    
    generated_at = Column(String, nullable=False)
