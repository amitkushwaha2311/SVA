"""
SVA Execution Sandbox
=====================

Sandbox protocol and safe fallback implementation.
"""

from typing import Protocol

from app.execution.models import ExecutionObservation, ExecutionPolicy, ExecutionRequest, ExecutionStatus, SandboxIdentity


class Sandbox(Protocol):
    """Protocol for secure execution sandbox backends."""
    def create(self) -> None: ...
    def execute(self, request: ExecutionRequest, policy: ExecutionPolicy) -> ExecutionObservation: ...
    def collect(self) -> str: ...
    def terminate(self) -> None: ...
    def destroy(self) -> None: ...


class LocalSafeFallbackSandbox:
    """
    Safe fallback sandbox for environments without guaranteed OS-level isolation (e.g., plain Windows).

    ALWAYS returns UNSUPPORTED and refuses to execute rather than executing
    untrusted repository code on the host.
    """

    def __init__(self) -> None:
        self.backend_name = "SAFE_FALLBACK"

    def create(self) -> None:
        pass

    def execute(self, request: ExecutionRequest, policy: ExecutionPolicy) -> ExecutionObservation:
        # We explicitly refuse to execute on the host
        return ExecutionObservation(
            execution_id=request.execution_id,
            status=ExecutionStatus.UNSUPPORTED,
            stdout="Execution refused: Secure execution backend unavailable in current environment.",
            stderr="Safe fallback engaged. Returning UNSUPPORTED.",
            sandbox_identity=SandboxIdentity(backend_name=self.backend_name),
            policy_id=policy.policy_id,
            repository_id=request.repository_id,
            commit_id=request.commit_id,
            snapshot_id=request.snapshot_id,
        )

    def collect(self) -> str:
        return "No artifacts collected. Execution was safely blocked."

    def terminate(self) -> None:
        pass

    def destroy(self) -> None:
        pass
