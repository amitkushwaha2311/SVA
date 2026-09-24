import os
import shutil
import tempfile
import time
from typing import Any

from app.execution.models import (
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    SandboxEnvironment,
    SandboxIdentity,
)
from app.execution.sandbox import Sandbox


class DockerSandboxBackend(Sandbox):
    """
    Real Docker sandbox backend for executing verification tasks securely.
    Must enforce non-root UID/GID, network_mode="none", cap_drop=["ALL"],
    and no-new-privileges. Read-only repository snapshot.
    """
    
    # Use a pinned digest for the SVA execution image (using alpine as a stand-in for the real image)
    APPROVED_IMAGE = "alpine@sha256:c5b1261d6d3e43071626931fc004fa70c82dae47a9c878b1731677353f47e3be"

    def __init__(self, snapshot_path: str):
        self.snapshot_path = snapshot_path
        self.container_id = None
        self.scratch_dir = None
        # We need the docker library. Import lazily to gracefully fail to UNSUPPORTED if not installed
        try:
            import docker
            self.client = docker.from_env()
            self._docker_available = True
        except Exception:
            self.client = None
            self._docker_available = False

    def create(self) -> None:
        """Create the necessary resources for execution."""
        # Always allocate a scratch directory for output, regardless of Docker availability
        self.scratch_dir = tempfile.mkdtemp(prefix="sva_sandbox_")
        
        if not self._docker_available:
            return
        
        # Verify the image exists or try to pull it
        try:
            self.client.images.get(self.APPROVED_IMAGE)
        except Exception:
            try:
                # Strictly only pull the approved image if missing
                self.client.images.pull(self.APPROVED_IMAGE)
            except Exception:
                # If we still can't get it, we fail at execute() later
                pass

    def execute(self, request: ExecutionRequest, policy: ExecutionPolicy) -> ExecutionObservation:
        identity = SandboxIdentity(
            backend_name="DOCKER",
            image_digest=self.APPROVED_IMAGE.split("@")[-1] if "@" in self.APPROVED_IMAGE else self.APPROVED_IMAGE
        )

        if not self._docker_available:
            return self._unsupported_result(request, policy, identity, "Docker not available on host")

        # Verify image exists
        try:
            self.client.images.get(self.APPROVED_IMAGE)
        except Exception:
            return self._unsupported_result(request, policy, identity, "Approved execution image unavailable")

        if not self.scratch_dir:
            return self._error_result(request, policy, identity, "Sandbox create() was not called or failed")

        start_time = time.time()
        
        # Enforce Explicit Environment Sanity
        env_vars = {}
        
        # Prepare mounts
        volumes = {
            os.path.abspath(self.snapshot_path): {
                "bind": "/repo",
                "mode": "ro"
            }
        }
        
        fs_limit = policy.limits.writable_fs_limit_mb if hasattr(policy.limits, 'writable_fs_limit_mb') else 100
        tmpfs = {
            "/scratch": f"size={fs_limit}m,mode=1777"
        }
        
        # Compute resources
        mem_limit = f"{policy.limits.memory_limit_mb}m" if policy.limits.memory_limit_mb else "512m"
        cpu_quota = int(policy.limits.cpu_limit_cores * 100000) if policy.limits.cpu_limit_cores else 100000
        cpu_period = 100000
        pids_limit = policy.limits.pid_limit if policy.limits.pid_limit else 256
        
        # Build strict working directory path inside container
        # Note: request.working_directory shouldn't contain traversal. The planner validates this.
        container_wd = "/repo"
        if request.working_directory and request.working_directory != ".":
            container_wd = os.path.normpath(f"/repo/{request.working_directory}")
            if not container_wd.startswith("/repo"):
                return self._error_result(request, policy, identity, "Working directory escapes repository boundary")

        try:
            # We use `run` in detach mode to enforce timeouts
            container = self.client.containers.run(
                self.APPROVED_IMAGE,
                command=request.command,
                working_dir=container_wd,
                volumes=volumes,
                tmpfs=tmpfs,
                environment=env_vars,
                detach=True,
                remove=False, # We clean it up explicitly in destroy
                
                # SECURITY ENFORCEMENTS
                network_mode="none",
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                user="1000:1000",
                read_only=True,
                
                # RESOURCE LIMITS
                mem_limit=mem_limit,
                cpu_quota=cpu_quota,
                cpu_period=cpu_period,
                pids_limit=pids_limit,
            )
            self.container_id = container.id
            
            # Wait for container with timeout
            try:
                result = container.wait(timeout=policy.limits.timeout_seconds)
                exit_code = result.get("StatusCode", -1)
                status = ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED
                
                max_bytes = policy.limits.output_size_limit_kb * 1024
                
                def _fetch_bounded_logs(stream, max_b) -> str:
                    collected = []
                    total = 0
                    for chunk in stream:
                        collected.append(chunk)
                        total += len(chunk)
                        if total > max_b:
                            collected.append(b"\n[OUTPUT TRUNCATED BY POLICY]")
                            break
                    return b"".join(collected).decode("utf-8", errors="replace")
                
                stdout = _fetch_bounded_logs(container.logs(stdout=True, stderr=False, stream=True), max_bytes // 2)
                stderr = _fetch_bounded_logs(container.logs(stdout=False, stderr=True, stream=True), max_bytes // 2)
                
                if "[OUTPUT TRUNCATED BY POLICY]" in stdout or "[OUTPUT TRUNCATED BY POLICY]" in stderr:
                    status = ExecutionStatus.RESOURCE_LIMIT
                    
                duration = time.time() - start_time
                
                return ExecutionObservation(
                    execution_id=request.execution_id,
                    status=status,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    sandbox_identity=identity,
                    environment=SandboxEnvironment(
                        env_vars_injected=[],
                        mounted_paths=["/repo:ro", "/scratch:rw"],
                        working_dir=container_wd
                    ),
                    policy_id=policy.policy_id,
                    repository_id=request.repository_id,
                    commit_id=request.commit_id,
                    snapshot_id=request.snapshot_id,
                )
                
            except Exception as e:
                import requests
                if isinstance(e, requests.exceptions.ReadTimeout):
                    # Manual timeout enforcement
                    container.kill()
                    return ExecutionObservation(
                        execution_id=request.execution_id,
                        status=ExecutionStatus.TIMEOUT,
                        exit_code=-1,
                        stdout="",
                        stderr=f"Execution timed out after {policy.limits.timeout_seconds} seconds",
                        duration_seconds=policy.limits.timeout_seconds,
                        timed_out=True,
                        sandbox_identity=identity,
                        policy_id=policy.policy_id,
                        repository_id=request.repository_id,
                        commit_id=request.commit_id,
                        snapshot_id=request.snapshot_id,
                    )
                raise e

        except Exception as e:
            return self._error_result(request, policy, identity, f"Container execution failed: {str(e)}")

    def collect(self) -> str:
        return f"Outputs available in scratch dir if needed: {self.scratch_dir}"

    def terminate(self) -> None:
        if self._docker_available and self.container_id:
            try:
                container = self.client.containers.get(self.container_id)
                container.kill()
            except Exception:
                pass

    def destroy(self) -> None:
        self.terminate()
        if self._docker_available and self.container_id:
            try:
                container = self.client.containers.get(self.container_id)
                container.remove(force=True)
            except Exception:
                pass
            
        if self.scratch_dir and os.path.exists(self.scratch_dir):
            try:
                shutil.rmtree(self.scratch_dir)
            except Exception:
                pass

    def _unsupported_result(self, request: ExecutionRequest, policy: ExecutionPolicy, identity: SandboxIdentity, reason: str) -> ExecutionObservation:
        return ExecutionObservation(
            execution_id=request.execution_id,
            status=ExecutionStatus.UNSUPPORTED,
            exit_code=None,
            stdout=f"Execution refused: {reason}",
            stderr="Safe fallback engaged. Returning UNSUPPORTED.",
            sandbox_identity=identity,
            policy_id=policy.policy_id,
            repository_id=request.repository_id,
            commit_id=request.commit_id,
            snapshot_id=request.snapshot_id,
        )

    def _error_result(self, request: ExecutionRequest, policy: ExecutionPolicy, identity: SandboxIdentity, reason: str) -> ExecutionObservation:
        return ExecutionObservation(
            execution_id=request.execution_id,
            status=ExecutionStatus.ERROR,
            exit_code=-1,
            stdout="",
            stderr=f"Execution Error: {reason}",
            sandbox_identity=identity,
            policy_id=policy.policy_id,
            repository_id=request.repository_id,
            commit_id=request.commit_id,
            snapshot_id=request.snapshot_id,
        )
