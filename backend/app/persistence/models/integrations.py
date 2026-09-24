import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship

from app.persistence.database import Base


def _generate_uuid():
    return str(uuid.uuid4())


class ProviderConnectionRow(Base):
    __tablename__ = "provider_connections"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # "github", "gitlab"
    provider = Column(String(50), nullable=False)
    
    # Provider's internal ID for this connection/installation (e.g., GitHub App Installation ID)
    connection_identity = Column(String(255), nullable=True)
    
    # Encrypted secret/token
    encrypted_credential = Column(String(2048), nullable=True)
    encryption_key_version = Column(Integer, nullable=False, default=1)
    
    # CONNECTED, DISCONNECTED, REVOKED, INVALID, UNAVAILABLE, UNKNOWN
    status = Column(String(50), nullable=False, default="CONNECTED")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_validated_at = Column(DateTime(timezone=True), nullable=True)

    workspace = relationship("WorkspaceRow")


class WebhookEventRow(Base):
    """
    Idempotent storage for incoming webhooks.
    """
    __tablename__ = "webhook_events"

    # The unique delivery ID provided by the webhook (e.g. X-GitHub-Delivery)
    event_id = Column(String(255), primary_key=True)
    provider = Column(String(50), nullable=False)
    
    # Webhook type (e.g. "push")
    event_type = Column(String(100), nullable=False)
    
    # The provider's internal ID for the repository that triggered this
    provider_repository_id = Column(String(255), nullable=True, index=True)
    
    payload = Column(JSON, nullable=False)
    
    # PENDING, PROCESSED, FAILED, IGNORED
    status = Column(String(50), nullable=False, default="PENDING")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProviderAuditEventRow(Base):
    """
    Security-sensitive provider actions audit log.
    """
    __tablename__ = "provider_audit_events"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=True, index=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    provider = Column(String(50), nullable=False)
    connection_id = Column(String(36), ForeignKey("provider_connections.id"), nullable=True)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=True)
    
    operation = Column(String(255), nullable=False)
    outcome = Column(String(50), nullable=False)  # SUCCESS, FAILURE, DENIED
    
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Stubs for enterprise organization mappings (Phase 18C Enterprise foundations)

class ProviderOrganizationRow(Base):
    __tablename__ = "provider_organizations"
    
    id = Column(String(36), primary_key=True, default=_generate_uuid)
    provider = Column(String(50), nullable=False)
    provider_org_id = Column(String(255), nullable=False, unique=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)


class ProviderTeamMappingRow(Base):
    __tablename__ = "provider_team_mappings"
    
    id = Column(String(36), primary_key=True, default=_generate_uuid)
    provider_org_id = Column(String(36), ForeignKey("provider_organizations.id"), nullable=False)
    provider_team_id = Column(String(255), nullable=False)
    sva_role = Column(String(50), nullable=False) # Maps to WorkspaceRole
