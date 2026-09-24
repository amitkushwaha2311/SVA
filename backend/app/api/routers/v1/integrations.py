"""
Integrations Router — Phase 18C.

Manages provider connections (GitHub, GitLab) for workspaces.

Security model:
- Credentials are never returned in API responses (only status/metadata).
- Every operation validates the full ownership chain:
    authenticated user → workspace membership → connection belongs to workspace
- RBAC: ADMIN or higher required for create/delete.
- VIEWER/MEMBER can only list status.
- Credentials are encrypted at rest before persistence (see app/core/crypto.py).
- This router never exposes raw tokens, ciphertexts, or encryption keys.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    WorkspaceRole,
    get_current_user,
    require_workspace_role,
)
from app.core.crypto import encrypt_credential, decrypt_credential
from app.core.config import settings
from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.repositories.integration_repo import (
    ProviderConnectionRepo,
    ProviderAuditRepo,
)
from app.providers.repository.base import (
    ProviderError,
    validate_provider_url,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])

_SUPPORTED_PROVIDERS = {"github", "gitlab"}
_PROVIDER_ALLOWED_HOSTS = {
    "github": ("github.com",),
    "gitlab": ("gitlab.com",),
}


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ConnectProviderRequest(BaseModel):
    provider: str
    repository_url: str
    token: str  # PAT or App installation token — encrypted before persistence

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in _SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {v!r}. Supported: {sorted(_SUPPORTED_PROVIDERS)}")
        return v

    @field_validator("token")
    @classmethod
    def token_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Token must not be empty.")
        return v.strip()


class ProviderConnectionResponse(BaseModel):
    """
    Deliberately omits encrypted_credential, encryption_key_version, and any secret.
    """
    id: str
    workspace_id: str
    provider: str
    connection_identity: Optional[str]
    status: str
    created_at: str
    last_validated_at: Optional[str]

    model_config = {"from_attributes": True}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/{workspace_id}/connections", response_model=ProviderConnectionResponse)
async def connect_provider(
    workspace_id: str,
    body: ConnectProviderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserRow = Depends(get_current_user),
    membership=Depends(require_workspace_role(WorkspaceRole.ADMIN)),
):
    """
    Create a new provider connection for a workspace.

    Requires ADMIN role.
    - The token is encrypted before persistence.
    - The raw token is NEVER stored or returned.
    - The URL is validated before any API call is made.
    """
    # Validate URL before storing anything
    allowed_hosts = _PROVIDER_ALLOWED_HOSTS.get(body.provider, ())
    try:
        owner, repo = validate_provider_url(body.repository_url, allowed_hosts)
    except ProviderError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Encrypt before persistence
    try:
        encrypted = encrypt_credential(body.token)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to encrypt credential.")

    repo = ProviderConnectionRepo(db)
    audit = ProviderAuditRepo(db)

    connection = await repo.create(
        workspace_id=workspace_id,
        provider=body.provider,
        connection_identity=f"{owner}/{repo}",
        encrypted_credential=encrypted,
        encryption_key_version=settings.ENCRYPTION_KEY_VERSION,
    )

    await audit.log(
        provider=body.provider,
        operation="connect",
        outcome="SUCCESS",
        workspace_id=workspace_id,
        actor_id=current_user.id,
        connection_id=connection.id,
        ip_address=None,
        details={"repository_url": body.repository_url},
    )
    await db.commit()

    return _to_response(connection)


@router.get("/{workspace_id}/connections", response_model=list[ProviderConnectionResponse])
async def list_connections(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserRow = Depends(get_current_user),
    membership=Depends(require_workspace_role(WorkspaceRole.VIEWER)),
):
    """
    List all provider connections for a workspace.
    Requires at least VIEWER role.
    Response NEVER includes credentials.
    """
    repo = ProviderConnectionRepo(db)
    connections = await repo.list_by_workspace(workspace_id)
    return [_to_response(c) for c in connections]


@router.get("/{workspace_id}/connections/{connection_id}", response_model=ProviderConnectionResponse)
async def get_connection(
    workspace_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserRow = Depends(get_current_user),
    membership=Depends(require_workspace_role(WorkspaceRole.VIEWER)),
):
    """
    Get a single provider connection.
    Server-side validates connection belongs to this workspace.
    """
    repo = ProviderConnectionRepo(db)
    connection = await repo.get_by_id_and_workspace(connection_id, workspace_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")
    return _to_response(connection)


@router.delete("/{workspace_id}/connections/{connection_id}", status_code=204)
async def revoke_connection(
    workspace_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserRow = Depends(get_current_user),
    membership=Depends(require_workspace_role(WorkspaceRole.ADMIN)),
):
    """
    Revoke (disconnect) a provider connection.
    Requires ADMIN role.
    """
    conn_repo = ProviderConnectionRepo(db)
    connection = await conn_repo.get_by_id_and_workspace(connection_id, workspace_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found.")

    await conn_repo.update_status(connection_id, workspace_id, "REVOKED")

    audit = ProviderAuditRepo(db)
    await audit.log(
        provider=connection.provider,
        operation="disconnect",
        outcome="SUCCESS",
        workspace_id=workspace_id,
        actor_id=current_user.id,
        connection_id=connection_id,
    )
    await db.commit()


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _to_response(row) -> ProviderConnectionResponse:
    """
    Map a ProviderConnectionRow to a response — NEVER including credentials.
    """
    return ProviderConnectionResponse(
        id=row.id,
        workspace_id=row.workspace_id,
        provider=row.provider,
        connection_identity=row.connection_identity,
        status=row.status,
        created_at=row.created_at.isoformat() if row.created_at else "",
        last_validated_at=row.last_validated_at.isoformat() if row.last_validated_at else None,
    )
