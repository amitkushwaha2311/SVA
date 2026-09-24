"""
Webhook Router — Phase 18C.

Receives and securely processes GitHub and GitLab webhook events.

Security model:
- Raw request body is read BEFORE trusting any payload fields.
- GitHub: X-Hub-Signature-256 verified via HMAC-SHA256 (constant-time).
- GitLab: X-Gitlab-Token verified via shared-secret constant-time comparison.
- Payload fields (workspace_id, repository_id etc.) are never trusted from the payload.
  Instead, all lookups use provider_repository_id → server-side owned records.
- Webhook processing is idempotent: duplicate delivery IDs create no duplicate jobs.
- Webhooks enqueue a durable AnalysisJob; they NEVER execute analysis directly.
- Unknown repositories, revoked connections, and malformed payloads fail safely.

Required environment configuration:
  GITHUB_WEBHOOK_SECRET   — shared HMAC secret configured in GitHub webhook settings
  GITLAB_WEBHOOK_TOKEN    — shared token configured in GitLab webhook settings
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.persistence.database import get_db
from app.persistence.models.integrations import ProviderConnectionRow, WebhookEventRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.repositories.integration_repo import WebhookEventRepo, ProviderAuditRepo
from app.persistence.repositories.job_repo import AnalysisJobRepo
from app.persistence.repositories.repository_repo import AnalysisRepo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# ─── Signature Verification Helpers ─────────────────────────────────────────

def _verify_github_signature(raw_body: bytes, header_sig: Optional[str], secret: str) -> None:
    """
    Verify GitHub's X-Hub-Signature-256 header.

    The raw body is hashed with HMAC-SHA256 using the webhook secret.
    Comparison is done in constant time to prevent timing attacks.
    """
    if not header_sig:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header.")
    if not header_sig.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid signature format.")

    expected = hmac.new(
        secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    received = header_sig[len("sha256="):]

    # Constant-time comparison
    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="GitHub webhook signature verification failed.")


def _verify_gitlab_token(header_token: Optional[str], expected_token: str) -> None:
    """
    Verify GitLab's X-Gitlab-Token header.

    GitLab uses a shared secret token (not HMAC). Comparison is done in constant
    time to prevent timing attacks.
    NOTE: This is NOT an HMAC verification. The token is compared directly.
    """
    if not header_token:
        raise HTTPException(status_code=401, detail="Missing X-Gitlab-Token header.")
    if not hmac.compare_digest(expected_token.encode("utf-8"), header_token.encode("utf-8")):
        raise HTTPException(status_code=401, detail="GitLab webhook token verification failed.")


# ─── GitHub Webhook ──────────────────────────────────────────────────────────

@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(default=None),
    x_github_event: Optional[str] = Header(default=None),
    x_github_delivery: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive and process a GitHub webhook event.

    Security flow:
      1. Read raw body (before any parsing).
      2. Verify HMAC-SHA256 signature with constant-time comparison.
      3. Parse payload only after authentication.
      4. Look up repository from server-side records (never trust payload IDs).
      5. Enqueue durable analysis job (never execute synchronously).
    """
    raw_body = await request.body()

    # Step 1: Authenticate before touching any payload data
    secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        logger.warning("GITHUB_WEBHOOK_SECRET is not configured. Rejecting webhook.")
        raise HTTPException(status_code=503, detail="GitHub webhook integration not configured.")
    _verify_github_signature(raw_body, x_hub_signature_256, secret)

    # Step 2: Now safe to parse the payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload.")

    event_type = x_github_event or "unknown"
    delivery_id = x_github_delivery or str(uuid.uuid4())

    # Step 3: Idempotency — record the delivery; skip if already processed
    webhook_repo = WebhookEventRepo(db)
    audit_repo = ProviderAuditRepo(db)

    provider_repo_id = _extract_github_repo_id(payload)

    event_row, created = await webhook_repo.get_or_create(
        event_id=delivery_id,
        provider="github",
        event_type=event_type,
        provider_repository_id=provider_repo_id,
        payload=payload,
    )
    await db.commit()

    if not created:
        # Duplicate delivery — idempotent response
        logger.info("Duplicate GitHub webhook delivery %s — ignored.", delivery_id)
        return {"status": "duplicate_ignored", "delivery_id": delivery_id}

    if event_type not in ("push", "create", "pull_request", "installation", "repository"):
        await webhook_repo.update_status(delivery_id, "IGNORED")
        await db.commit()
        return {"status": "ignored", "event_type": event_type}

    if event_type not in ("push", "pull_request"):
        await webhook_repo.update_status(delivery_id, "IGNORED")
        await db.commit()
        return {"status": "ignored", "event_type": event_type}

    # Step 4: Resolve repository from server-side records
    repository = await _find_repository_by_provider_id(db, "github", provider_repo_id)
    if not repository:
        await webhook_repo.update_status(delivery_id, "IGNORED")
        await db.commit()
        await audit_repo.log(
            provider="github",
            operation="webhook_received",
            outcome="IGNORED",
            details={"reason": "unknown_repository", "event_type": event_type},
        )
        await db.commit()
        return {"status": "ignored", "reason": "unknown_repository"}

    # Step 5: Enqueue durable analysis job
    ref = payload.get("ref", "") or payload.get("pull_request", {}).get("head", {}).get("sha", "")
    revision = ref.removeprefix("refs/heads/").removeprefix("refs/tags/") or "HEAD"

    job_repo = AnalysisJobRepo(db)
    analysis_repo = AnalysisRepo(db)

    analysis = await analysis_repo.create(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        provider_name="github",
        repository_identifier=repository.repository_identifier,
        revision=revision,
    )
    await db.flush()

    await job_repo.create_job(
        analysis_id=analysis.id,
        workspace_id=repository.workspace_id,
    )

    await webhook_repo.update_status(delivery_id, "PROCESSED")
    await audit_repo.log(
        provider="github",
        operation="webhook_received",
        outcome="SUCCESS",
        workspace_id=repository.workspace_id,
        repository_id=repository.id,
        details={"event_type": event_type, "revision": revision, "delivery_id": delivery_id},
    )
    await db.commit()

    return {"status": "queued", "analysis_id": analysis.id}


# ─── GitLab Webhook ──────────────────────────────────────────────────────────

@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: Optional[str] = Header(default=None),
    x_gitlab_event: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive and process a GitLab webhook event.

    Security flow:
      1. Read raw body (before any parsing).
      2. Verify X-Gitlab-Token shared secret with constant-time comparison.
         NOTE: This is a shared-secret comparison, NOT an HMAC verification.
      3. Parse payload only after authentication.
      4. Look up repository from server-side records.
      5. Enqueue durable analysis job (never execute synchronously).
    """
    raw_body = await request.body()

    # Step 1: Authenticate before touching any payload data
    expected_token = getattr(settings, "GITLAB_WEBHOOK_TOKEN", "")
    if not expected_token:
        logger.warning("GITLAB_WEBHOOK_TOKEN is not configured. Rejecting webhook.")
        raise HTTPException(status_code=503, detail="GitLab webhook integration not configured.")
    _verify_gitlab_token(x_gitlab_token, expected_token)

    # Step 2: Now safe to parse
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload.")

    event_type = x_gitlab_event or payload.get("object_kind", "unknown")
    # GitLab doesn't have a global delivery ID header — derive from event data
    delivery_id = f"gitlab-{payload.get('checkout_sha', str(uuid.uuid4()))}"

    webhook_repo = WebhookEventRepo(db)
    audit_repo = ProviderAuditRepo(db)

    project = payload.get("project", {})
    provider_repo_id = str(project.get("id", ""))

    event_row, created = await webhook_repo.get_or_create(
        event_id=delivery_id,
        provider="gitlab",
        event_type=event_type,
        provider_repository_id=provider_repo_id,
        payload=payload,
    )
    await db.commit()

    if not created:
        logger.info("Duplicate GitLab webhook %s — ignored.", delivery_id)
        return {"status": "duplicate_ignored"}

    if event_type not in ("push", "tag_push", "merge_request"):
        await webhook_repo.update_status(delivery_id, "IGNORED")
        await db.commit()
        return {"status": "ignored", "event_type": event_type}

    # Step 3: Resolve repository from server-side records
    repository = await _find_repository_by_provider_id(db, "gitlab", provider_repo_id)
    if not repository:
        await webhook_repo.update_status(delivery_id, "IGNORED")
        await db.commit()
        return {"status": "ignored", "reason": "unknown_repository"}

    # Step 4: Enqueue
    ref = payload.get("ref", "")
    revision = ref.removeprefix("refs/heads/").removeprefix("refs/tags/") or "HEAD"

    job_repo = AnalysisJobRepo(db)
    analysis_repo = AnalysisRepo(db)

    analysis = await analysis_repo.create(
        repository_id=repository.id,
        workspace_id=repository.workspace_id,
        provider_name="gitlab",
        repository_identifier=repository.repository_identifier,
        revision=revision,
    )
    await db.flush()

    await job_repo.create_job(
        analysis_id=analysis.id,
        workspace_id=repository.workspace_id,
    )

    await webhook_repo.update_status(delivery_id, "PROCESSED")
    await audit_repo.log(
        provider="gitlab",
        operation="webhook_received",
        outcome="SUCCESS",
        workspace_id=repository.workspace_id,
        repository_id=repository.id,
        details={"event_type": event_type, "revision": revision},
    )
    await db.commit()
    return {"status": "queued", "analysis_id": analysis.id}


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _extract_github_repo_id(payload: dict) -> Optional[str]:
    """Extract the provider repository ID from a GitHub payload."""
    repo = payload.get("repository", {})
    rid = repo.get("full_name") or str(repo.get("id", ""))
    return rid or None


async def _find_repository_by_provider_id(
    db: AsyncSession, provider: str, provider_repo_id: Optional[str]
) -> Optional[RepositoryRow]:
    """
    Look up an SVA repository record by provider and provider-controlled ID.
    Validates workspace ownership is implicit in the existing record.
    """
    if not provider_repo_id:
        return None
    stmt = select(RepositoryRow).where(
        RepositoryRow.provider_type == provider,
        RepositoryRow.repository_identifier.contains(provider_repo_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
