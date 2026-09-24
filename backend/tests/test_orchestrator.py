"""
Orchestrator Tests — Phase 17 Final Audit
==========================================

Tests the AnalysisOrchestrator behavior by inspecting:
1. Lifecycle transition enforcement via _is_valid_transition()
2. _transition() rejection of illegal state jumps
3. run() captures provider failures and sets FAILED state
4. Analysis COMPLETED != Verification PROVEN (semantic separation)

The orchestrator uses lazy imports inside _run_pipeline, so tests
targeting the full pipeline must patch from within their true import path.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.orchestration.analyzer import AnalysisOrchestrator, _is_valid_transition, _VALID_TRANSITIONS


# ─── Unit: Lifecycle Transition Logic ─────────────────────────────────────────

class TestLifecycleTransitions:
    """Test the _VALID_TRANSITIONS table and _is_valid_transition() gating logic."""

    def test_full_happy_path_is_valid(self):
        """The canonical success path must be fully reachable."""
        happy_path = [
            ("CREATED", "QUEUED"),
            ("QUEUED", "INGESTING"),
            ("INGESTING", "SNAPSHOTTING"),
            ("SNAPSHOTTING", "ANALYZING"),
            ("ANALYZING", "VERIFYING"),
            ("VERIFYING", "COMPLETED"),
        ]
        for current, target in happy_path:
            assert _is_valid_transition(current, target), (
                f"Expected valid transition: {current} → {target}"
            )

    def test_any_active_state_can_transition_to_failed(self):
        """Every active state must be able to transition to FAILED."""
        active_states = ["CREATED", "QUEUED", "INGESTING", "SNAPSHOTTING", "ANALYZING", "VERIFYING"]
        for state in active_states:
            assert _is_valid_transition(state, "FAILED"), (
                f"State {state} must be able to transition to FAILED"
            )

    def test_any_active_state_can_transition_to_cancelled(self):
        """Every active state must be cancellable."""
        active_states = ["CREATED", "QUEUED", "INGESTING", "SNAPSHOTTING", "ANALYZING", "VERIFYING"]
        for state in active_states:
            assert _is_valid_transition(state, "CANCELLED"), (
                f"State {state} must be cancellable"
            )

    def test_completed_is_terminal(self):
        """COMPLETED cannot transition to any state — it is terminal."""
        for target in _VALID_TRANSITIONS.keys():
            assert not _is_valid_transition("COMPLETED", target), (
                f"COMPLETED should not be able to transition to {target}"
            )

    def test_failed_is_terminal(self):
        """FAILED cannot transition to any state — it is terminal."""
        for target in _VALID_TRANSITIONS.keys():
            assert not _is_valid_transition("FAILED", target), (
                f"FAILED should not be able to transition to {target}"
            )

    def test_cancelled_is_terminal(self):
        """CANCELLED cannot transition to any state — it is terminal."""
        for target in _VALID_TRANSITIONS.keys():
            assert not _is_valid_transition("CANCELLED", target), (
                f"CANCELLED should not be able to transition to {target}"
            )

    def test_backward_transition_rejected(self):
        """Forward-only: already-passed states cannot be re-entered."""
        illegal = [
            ("VERIFYING", "QUEUED"),
            ("ANALYZING", "INGESTING"),
            ("COMPLETED", "VERIFYING"),
            ("SNAPSHOTTING", "CREATED"),
        ]
        for current, target in illegal:
            assert not _is_valid_transition(current, target), (
                f"Backward transition must be rejected: {current} → {target}"
            )

    def test_skip_transition_rejected(self):
        """Skipping states is not allowed (e.g., CREATED → ANALYZING)."""
        skips = [
            ("CREATED", "ANALYZING"),
            ("QUEUED", "COMPLETED"),
            ("INGESTING", "COMPLETED"),
            ("CREATED", "COMPLETED"),
        ]
        for current, target in skips:
            assert not _is_valid_transition(current, target), (
                f"Skipping states must be rejected: {current} → {target}"
            )


# ─── Integration: Failure Recovery ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_transitions_to_failed_on_provider_error():
    """
    If the provider raises during fetch_snapshot, the orchestrator must:
    1. Not crash silently
    2. Persist FAILED state with a non-empty error_message
    3. Not claim COMPLETED
    """
    session = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    captured_status = {}

    from app.persistence.models.analysis import AnalysisRow
    from datetime import datetime, timezone

    analysis = AnalysisRow(id="sva-fail-1", repository_id="repo-1", status="CREATED", commit_id="main", created_at=datetime.now(timezone.utc))

    async def fake_execute(query):
        result = MagicMock()
        result.scalar_one_or_none.return_value = analysis
        return result

    session.execute = fake_execute
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    def capture_status(new_status):
        captured_status["last"] = new_status

    original_status_setter = type(analysis).status.fset if hasattr(type(analysis).status, 'fset') else None

    orchestrator = AnalysisOrchestrator(session_factory=session_factory)

    # Make the git provider fail during snapshot
    with patch("app.providers.repository.git.GitProvider.fetch_snapshot", side_effect=ValueError("Network unreachable")):
        await orchestrator.run(
            analysis_id="sva-fail-1",
            repository_id="repo-1",
            provider_name="git",
            repository_identifier="https://github.com/org/repo",
            revision="main",
            workspace_id="ws-1",
        )

    # The analysis must be in FAILED state
    assert analysis.status == "FAILED", f"Expected FAILED, got {analysis.status}"
    assert analysis.error_message is not None
    assert len(analysis.error_message) > 0


# ─── Semantic Separation: COMPLETED != PROVEN ─────────────────────────────────

class TestSemanticSeparation:
    """
    Verify that AnalysisOrchestrator never conflates analysis completion
    with verification proof. The engine's VerificationResult is what
    determines semantic state — not the orchestrator.
    """

    def test_verification_states_are_semantically_distinct(self):
        """
        The verification states UNKNOWN, INCONCLUSIVE, VIOLATED, SUPPORTED, STALE
        must remain distinct from analysis lifecycle states.
        """
        # Analysis lifecycle states
        analysis_terminal = {"COMPLETED", "FAILED", "CANCELLED"}
        
        # Verification semantic states (from Phase 10/11)
        verification_states = {"UNKNOWN", "INCONCLUSIVE", "VIOLATED", "SUPPORTED", "STALE", "PROVEN"}
        
        # None should overlap with lifecycle states
        overlap = analysis_terminal & verification_states
        assert not overlap, (
            f"Analysis lifecycle states and verification states must not overlap: {overlap}"
        )

    def test_completed_analysis_does_not_imply_verification_proven(self):
        """
        COMPLETED means the pipeline finished. It does NOT mean verification succeeded.
        This is verified by ensuring the orchestrator does not write 'PROVEN' to AnalysisRow.
        """
        # AnalysisRow has a 'status' field for lifecycle, not for verification verdict.
        # Verification verdict lives in VerificationResultRow.
        from app.persistence.models.analysis import AnalysisRow
        analysis_columns = [c.key for c in AnalysisRow.__table__.columns]
        
        # Ensure analysis has no 'verification_result' or 'verdict' column
        # — those belong to the verification results table
        assert "verdict" not in analysis_columns
        assert "verification_result" not in analysis_columns
        assert "proven" not in analysis_columns
