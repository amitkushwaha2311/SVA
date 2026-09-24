from sqlalchemy import Column, String, JSON
from app.persistence.database import Base


class ChangeRecordRow(Base):
    __tablename__ = "change_records"

    change_id = Column(String(255), primary_key=True)
    repository_id = Column(String(255), nullable=False, index=True)
    base_commit = Column(String(255), nullable=False, index=True)
    target_commit = Column(String(255), nullable=False, index=True)
    
    file_path = Column(String(1024), nullable=True)
    file_classification = Column(String(50), nullable=True)
    file_change_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)


class SemanticImpactRow(Base):
    __tablename__ = "semantic_impacts"

    impact_id = Column(String(255), primary_key=True)
    change_id = Column(String(255), nullable=False, index=True)
    
    artifact_type = Column(String(50), nullable=False)
    artifact_id = Column(String(255), nullable=False)
    
    affected_requirements = Column(JSON, nullable=False, default=list)
    affected_contracts = Column(JSON, nullable=False, default=list)
    affected_obligations = Column(JSON, nullable=False, default=list)
    affected_targets = Column(JSON, nullable=False, default=list)


class InvalidationRecordRow(Base):
    __tablename__ = "invalidation_records"

    invalidation_id = Column(String(255), primary_key=True)
    artifact_type = Column(String(50), nullable=False)
    artifact_id = Column(String(255), nullable=False)
    
    previous_commit = Column(String(255), nullable=False)
    target_commit = Column(String(255), nullable=False)
    
    reason = Column(String, nullable=False)
    status = Column(String(50), nullable=False)
    
    related_change_ids = Column(JSON, nullable=False, default=list)


class DriftReportRow(Base):
    __tablename__ = "drift_reports"

    drift_id = Column(String(255), primary_key=True)
    repository_id = Column(String(255), nullable=False, index=True)
    base_commit = Column(String(255), nullable=False, index=True)
    target_commit = Column(String(255), nullable=False, index=True)
    
    changes = Column(JSON, nullable=False, default=list)
    impacts = Column(JSON, nullable=False, default=list)
    invalidations = Column(JSON, nullable=False, default=list)
    summary = Column(JSON, nullable=True)
