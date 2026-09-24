"""
SVA Execution Policy
====================

Defines and evaluates security policy constraints for execution.
"""

from app.execution.models import (
    EnvironmentPolicy,
    ExecutionPermission,
    ExecutionPolicy,
    FilesystemPolicy,
    NetworkPolicy,
)


def get_default_policy() -> ExecutionPolicy:
    """
    Returns the strict default SVA execution policy.
    Fail-safe defaults: Deny network, restrict filesystem, no secrets.
    """
    return ExecutionPolicy(
        policy_id="SVA_STRICT_DEFAULT",
        network=NetworkPolicy.DENY,
        filesystem=FilesystemPolicy.RESTRICTED,
        secrets_allowed=False,
        environment=EnvironmentPolicy.MINIMAL_ALLOWLIST,
        timeout_seconds=60,
        memory_limit_mb=512,
        cpu_limit_cores=1.0,
        output_size_limit_kb=1024,
    )


class PolicyEvaluator:
    """Evaluates requested permissions against an ExecutionPolicy."""

    def evaluate_permissions(
        self,
        requested: list[ExecutionPermission],
        policy: ExecutionPolicy,
    ) -> list[ExecutionPermission]:
        """
        Returns the subset of requested permissions that are granted by the policy.
        """
        granted = []
        for perm in requested:
            if perm == ExecutionPermission.READ_REPOSITORY:
                granted.append(perm)
            elif perm == ExecutionPermission.WRITE_WORKSPACE:
                if policy.filesystem == FilesystemPolicy.RESTRICTED:
                    granted.append(perm)
            elif perm == ExecutionPermission.EXECUTE_PROCESS:
                granted.append(perm)
            elif perm == ExecutionPermission.NETWORK_ACCESS:
                # Default policy denies network
                if policy.network != NetworkPolicy.DENY:
                    granted.append(perm)
            elif perm == ExecutionPermission.READ_ENVIRONMENT:
                if policy.environment == EnvironmentPolicy.MINIMAL_ALLOWLIST:
                    granted.append(perm)
            elif perm == ExecutionPermission.READ_SECRET:
                if policy.secrets_allowed:
                    granted.append(perm)
            elif perm == ExecutionPermission.INSTALL_DEPENDENCY:
                # Requires network and write workspace
                if policy.network != NetworkPolicy.DENY and policy.filesystem == FilesystemPolicy.RESTRICTED:
                    granted.append(perm)

        return granted
