"""
SVA Execution Models
====================

Strongly typed models for the Secure Verification Execution Engine.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionPermission(str, Enum):
    """Explicit permissions requested for an execution."""
    READ_REPOSITORY = "READ_REPOSITORY"
    WRITE_WORKSPACE = "WRITE_WORKSPACE"
    EXECUTE_PROCESS = "EXECUTE_PROCESS"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    READ_ENVIRONMENT = "READ_ENVIRONMENT"
    READ_SECRET = "READ_SECRET"
    INSTALL_DEPENDENCY = "INSTALL_DEPENDENCY"


class NetworkPolicy(str, Enum):
    DENY = "DENY"
    ALLOWLIST_ONLY = "ALLOWLIST_ONLY"


class FilesystemPolicy(str, Enum):
    RESTRICTED = "RESTRICTED"   # Read repo, write temporary workspace
    READ_ONLY = "READ_ONLY"     # Read repo only


class EnvironmentPolicy(str, Enum):
    MINIMAL_ALLOWLIST = "MINIMAL_ALLOWLIST"


class SecretPolicy(str, Enum):
    DENY = "DENY"


class SandboxResourceLimits(BaseModel):
    timeout_seconds: int = 60
    memory_limit_mb: int | None = 512
    cpu_limit_cores: float | None = 1.0
    output_size_limit_kb: int = 1024
    pid_limit: int = 256
    writable_fs_limit_mb: int = 100


class ExecutionPolicy(BaseModel):
    """Policy constraints that an execution must follow."""
    policy_id: str = "DEFAULT_POLICY"
    network: NetworkPolicy = NetworkPolicy.DENY
    filesystem: FilesystemPolicy = FilesystemPolicy.RESTRICTED
    secrets: SecretPolicy = SecretPolicy.DENY
    environment: EnvironmentPolicy = EnvironmentPolicy.MINIMAL_ALLOWLIST
    limits: SandboxResourceLimits = Field(default_factory=SandboxResourceLimits)

    # Legacy attributes for compatibility until removed
    timeout_seconds: int = 60
    memory_limit_mb: int | None = 512
    cpu_limit_cores: float | None = 1.0
    output_size_limit_kb: int = 1024
    secrets_allowed: bool = False

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.secrets_allowed:
            self.secrets = SecretPolicy.DENY  # Forced deny
        self.limits.timeout_seconds = self.timeout_seconds
        self.limits.memory_limit_mb = self.memory_limit_mb
        self.limits.cpu_limit_cores = self.cpu_limit_cores
        self.limits.output_size_limit_kb = self.output_size_limit_kb


class ExecutionRequest(BaseModel):
    """
    A planned execution request.
    Must originate from SVA planner, NEVER directly from LLM output.
    """
    execution_id: str
    contract_id: str
    obligation_id: str
    target_id: str
    repository_id: str
    commit_id: str
    job_id: str | None = None
    analysis_id: str | None = None
    snapshot_id: str | None = None

    command: list[str]  # Always array, never shell string
    working_directory: str
    requested_permissions: list[ExecutionPermission] = Field(default_factory=list)

    # Required limits
    timeout_seconds: int = 60
    memory_limit_mb: int | None = None
    cpu_limit_cores: float | None = None

    expected_outcome: str  # e.g., "PASS", "DENIED"


class ExecutionStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    ERROR = "ERROR"
    NOT_RUN = "NOT_RUN"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    POLICY_DENIED = "POLICY_DENIED"


class SandboxIdentity(BaseModel):
    backend_name: str
    image_digest: str | None = None
    runtime_version: str | None = None


class SandboxEnvironment(BaseModel):
    env_vars_injected: list[str]
    mounted_paths: list[str]
    working_dir: str


class ExecutionObservation(BaseModel):
    """Detailed observation of an execution."""
    execution_id: str
    status: ExecutionStatus
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    timed_out: bool = False
    resource_limit_exceeded: bool = False
    sandbox_identity: SandboxIdentity
    environment: SandboxEnvironment | None = None
    policy_id: str
    repository_id: str
    commit_id: str
    snapshot_id: str | None = None


class ExecutionResult(ExecutionObservation):
    """Alias for backwards compatibility in existing codebase."""
    sandbox_backend: str = "NONE"

    def __init__(self, **data: Any):
        if "sandbox_identity" not in data:
            sb = data.get("sandbox_backend", "NONE")
            data["sandbox_identity"] = SandboxIdentity(backend_name=sb)
        super().__init__(**data)


class ExecutionAudit(BaseModel):
    """Immutable audit record of execution boundary crossing."""
    execution_id: str
    contract_id: str
    obligation_id: str
    target_id: str
    repository_id: str
    commit_id: str

    requested_permissions: list[ExecutionPermission]
    granted_permissions: list[ExecutionPermission]
    sandbox_backend: str
    command_identity: str   # e.g., "python -m pytest" (args joined safely for logging)

    start_time: str
    end_time: str
    exit_status: ExecutionStatus
    evidence_id: str | None = None
