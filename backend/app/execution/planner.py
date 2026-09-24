"""
SVA Execution Planner
=====================

Plans execution requests from SemanticContracts.
"""

import hashlib
import os

from app.contracts.models import ContractStatus, SemanticContract
from app.execution.models import ExecutionPermission, ExecutionRequest


# Explicit SVA-controlled executable allowlist
# No commands discovered in repositories can ever be executed.
COMMAND_ALLOWLIST = {
    "pytest": ["python", "-m", "pytest"],
    "unittest": ["python", "-m", "unittest"],
    "jest": ["npx", "jest"],
    "go_test": ["go", "test"],
}

FORBIDDEN_CHARS = {"&", "|", ";", ">", "<", "$", "`", "(", ")", "\n", "\r"}


class VerificationPlanner:
    """Plans controlled verification executions."""

    def plan(
        self,
        contract: SemanticContract,
        obligation_id: str,
        target_id: str,
        repository_id: str,
        commit_id: str,
        test_file: str,
        command_id: str = "pytest",
        expected_outcome: str = "PASS",
        job_id: str | None = None,
        analysis_id: str | None = None,
        snapshot_id: str | None = None,
    ) -> ExecutionRequest | None:
        """
        Creates an ExecutionRequest if the contract is READY and target/obligation exist.
        Returns None if planning fails (e.g. invalid inputs, blocked contract).
        """
        # 1. Contract must be READY
        if contract.compilation_status != ContractStatus.READY:
            return None

        # 2. Target must exist in contract
        target = next((t for t in contract.verification_targets if t.target_id == target_id), None)
        if not target:
            return None

        # 3. Command Allowlist
        base_cmd = COMMAND_ALLOWLIST.get(command_id)
        if not base_cmd:
            return None

        # 4. Input validation (Threat Model)
        # Prevent traversal, Git injection, and shell metacharacters
        if not test_file or test_file.startswith("-") or "--" in test_file:
            return None

        # Reject absolute paths (both POSIX and Windows style)
        if (
            os.path.isabs(test_file)        # Windows absolute: C:\ etc.
            or test_file.startswith("/")    # POSIX absolute: /etc/...
            or test_file.startswith("\\")  # UNC path
            or (len(test_file) >= 3 and test_file[1:3] == ":\\")  # Windows drive letter
            or ".." in test_file
        ):
            return None

        if any(c in test_file for c in FORBIDDEN_CHARS):
            return None

        # Construct argument array (NEVER shell=True)
        command = base_cmd + [test_file]

        # Generate deterministic-ish execution ID for traceability
        identity = f"{repository_id}:{contract.contract_id}:{obligation_id}:{target_id}:{commit_id}:{command_id}:{test_file}"
        execution_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()

        return ExecutionRequest(
            execution_id=execution_id,
            contract_id=contract.contract_id,
            obligation_id=obligation_id,
            target_id=target_id,
            repository_id=repository_id,
            commit_id=commit_id,
            job_id=job_id,
            analysis_id=analysis_id,
            snapshot_id=snapshot_id,
            command=command,
            working_directory=".", # Root of repo by default
            requested_permissions=[
                ExecutionPermission.READ_REPOSITORY,
                ExecutionPermission.EXECUTE_PROCESS
            ],
            timeout_seconds=60,
            expected_outcome=expected_outcome,
        )
