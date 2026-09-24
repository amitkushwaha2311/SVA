"""
Integration Repository — Manages ProviderConnections, WebhookEvents, and ProviderAuditEvents.

Security notes:
- Credentials are NEVER returned in raw form. Only ciphertext is stored.
- All resource queries enforce workspace ownership before returning data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.models.integrations import (
    ProviderConnectionRow,
    WebhookEventRow,
    ProviderAuditEventRow,
)

logger = logging.getLogger(__name__)


class ProviderConnectionRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        workspace_id: str,
        provider: str,
        connection_identity: Optional[str],
        encrypted_credential: str,
        encryption_key_version: int,
    ) -> ProviderConnectionRow:
        row = ProviderConnectionRow(
            workspace_id=workspace_id,
            provider=provider,
            connection_identity=connection_identity,
            encrypted_credential=encrypted_credential,
            encryption_key_version=encryption_key_version,
            status="CONNECTED",
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id_and_workspace(
        self, connection_id: str, workspace_id: str
    ) -> Optional[ProviderConnectionRow]:
        """Get a connection only if it belongs to the given workspace."""
        stmt = select(ProviderConnectionRow).where(
            ProviderConnectionRow.id == connection_id,
            ProviderConnectionRow.workspace_id == workspace_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self, workspace_id: str
    ) -> list[ProviderConnectionRow]:
        stmt = select(ProviderConnectionRow).where(
            ProviderConnectionRow.workspace_id == workspace_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self, connection_id: str, workspace_id: str, status: str
    ) -> Optional[ProviderConnectionRow]:
        row = await self.get_by_id_and_workspace(connection_id, workspace_id)
        if row:
            row.status = status
            row.updated_at = datetime.now(timezone.utc)
            await self._session.flush()
        return row

    async def update_validated_at(
        self, connection_id: str, workspace_id: str
    ) -> Optional[ProviderConnectionRow]:
        row = await self.get_by_id_and_workspace(connection_id, workspace_id)
        if row:
            row.last_validated_at = datetime.now(timezone.utc)
            await self._session.flush()
        return row


class WebhookEventRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        event_id: str,
        provider: str,
        event_type: str,
        provider_repository_id: Optional[str],
        payload: dict,
    ) -> tuple[WebhookEventRow, bool]:
        """
        Returns (row, created). If event_id already exists, returns existing row
        and created=False to allow idempotent handling.
        """
        existing = await self._session.get(WebhookEventRow, event_id)
        if existing:
            return existing, False

        row = WebhookEventRow(
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            provider_repository_id=provider_repository_id,
            payload=payload,
            status="PENDING",
        )
        self._session.add(row)
        await self._session.flush()
        return row, True

    async def update_status(self, event_id: str, status: str) -> None:
        row = await self._session.get(WebhookEventRow, event_id)
        if row:
            row.status = status
            await self._session.flush()


class ProviderAuditRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        provider: str,
        operation: str,
        outcome: str,
        workspace_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        repository_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> ProviderAuditEventRow:
        """
        Persist a security-sensitive audit event.
        NEVER include credentials, tokens, or secrets in `details`.
        """
        row = ProviderAuditEventRow(
            workspace_id=workspace_id,
            actor_id=actor_id,
            provider=provider,
            connection_id=connection_id,
            repository_id=repository_id,
            operation=operation,
            outcome=outcome,
            ip_address=ip_address,
            details=details or {},
        )
        self._session.add(row)
        await self._session.flush()
        return row
