"""
SVA Execution Validator
=======================

Pre-flight security validation for execution requests.
"""

import os
from pathlib import Path

from app.execution.models import ExecutionPermission, ExecutionPolicy, ExecutionRequest
from app.execution.planner import COMMAND_ALLOWLIST


class ExecutionValidationError(ValueError):
    """Raised when an execution request violates security boundaries."""
    pass


class ExecutionValidator:
    """Validates ExecutionRequests before they are sent to the Sandbox."""

    def validate(self, request: ExecutionRequest, policy: ExecutionPolicy) -> None:
        # 1. Command Allowlist
        if not request.command:
            raise ExecutionValidationError("Command cannot be empty.")

        # Reconstruct base command to check against allowlist
        base = " ".join(request.command[:3]) if len(request.command) >= 3 else " ".join(request.command)
        is_allowed = False
        for allowed_args in COMMAND_ALLOWLIST.values():
            allowed_base = " ".join(allowed_args)
            if base.startswith(allowed_base):
                is_allowed = True
                break

        if not is_allowed:
            raise ExecutionValidationError(f"Command '{base}' is not allowlisted.")

        # 2. Path Traversal & Escape checks (Basic Phase 1 PathGuard principles)
        # Working directory must not escape root
        wd = request.working_directory
        if ".." in wd or wd.startswith("/") or wd.startswith("\\") or ":" in wd:
            if wd != ".": # allow exact dot
                raise ExecutionValidationError(f"Working directory '{wd}' escapes repository boundary.")

        for arg in request.command:
            if ".." in arg or arg.startswith("/") or arg.startswith("\\") or ":" in arg:
                raise ExecutionValidationError(f"Command argument '{arg}' contains absolute or traversal paths.")

        # 3. Shell Metacharacters
        # Since we use argument arrays, the shell won't interpolate them, but we still reject
        # obvious shell chaining attempts just to be safe.
        forbidden_chars = ["&", "|", ";", ">", "<", "$", "`"]
        for arg in request.command:
            if any(c in arg for c in forbidden_chars):
                raise ExecutionValidationError(f"Command argument '{arg}' contains forbidden shell metacharacters.")

        # 4. Permissions check vs policy
        if ExecutionPermission.READ_SECRET in request.requested_permissions and not policy.secrets_allowed:
            raise ExecutionValidationError("Policy denies READ_SECRET permission.")
