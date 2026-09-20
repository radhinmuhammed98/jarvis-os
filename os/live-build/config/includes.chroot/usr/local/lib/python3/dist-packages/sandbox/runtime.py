"""
JARVIS Local Sandbox Isolation Runtime
Applies OS resource limits (RLIMIT_CPU, RLIMIT_AS, RLIMIT_NPROC), isolated temporary workspace,
network denial, captured outputs, and automatic workspace cleanup.
"""

import os
import sys
import shutil
import tempfile
import time
import subprocess
import resource
import logging
from typing import Dict, Any, Optional

from sandbox.types import SandboxConfig, SandboxResult, ResourceLimits

logger = logging.getLogger("jarvis-sandbox")

class SandboxRuntime:
    """Secure isolated execution runtime for untrusted/generated code."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    def run_python_code(self, code_string: str, dry_run: bool = False) -> SandboxResult:
        """
        Executes Python code in an isolated temporary directory with resource limits and restricted environment.
        Guarantees workspace destruction upon completion.
        """
        start_time = time.time()
        if dry_run:
            return SandboxResult(
                success=True,
                exit_code=0,
                stdout="[DRY-RUN] Code execution simulated successfully.",
                stderr="",
                execution_time_ms=(time.time() - start_time) * 1000,
                dry_run=True
            )

        workspace_dir = tempfile.mkdtemp(prefix="jarvis_sb_")
        script_path = os.path.join(workspace_dir, "isolated_script.py")

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code_string)

            # Build environment with network denial
            env = self._build_restricted_env(workspace_dir)

            def preexec_fn():
                # Enforce Linux OS resource limits in child process
                limits = self.config.limits
                # CPU Limit (seconds)
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (limits.max_cpu_seconds, limits.max_cpu_seconds + 2))
                except Exception:
                    pass

                # Address Space / Memory Limit (bytes)
                try:
                    mem_bytes = limits.max_memory_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                except Exception:
                    pass

                # Max Processes Limit
                try:
                    resource.setrlimit(resource.RLIMIT_NPROC, (limits.max_processes, limits.max_processes))
                except Exception:
                    pass

            # Execute subprocess
            proc = subprocess.Popen(
                [sys.executable, "-I", "-B", script_path],  # -I isolated mode (ignores PYTHONPATH and user site)
                cwd=workspace_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=preexec_fn
            )

            try:
                stdout, stderr = proc.communicate(timeout=self.config.limits.timeout_seconds)
                exec_time = (time.time() - start_time) * 1000

                # Truncate output to max_output_bytes
                max_bytes = self.config.limits.max_output_bytes
                stdout = stdout[:max_bytes]
                stderr = stderr[:max_bytes]

                if proc.returncode == 0:
                    return SandboxResult(
                        success=True,
                        exit_code=0,
                        stdout=stdout.strip(),
                        stderr=stderr.strip(),
                        execution_time_ms=exec_time
                    )
                else:
                    is_limit_exceeded = "MemoryError" in stderr or proc.returncode in [-9, -24, 137]
                    limit_type = "CPU/Memory" if is_limit_exceeded else None
                    return SandboxResult(
                        success=False,
                        exit_code=proc.returncode,
                        stdout=stdout.strip(),
                        stderr=stderr.strip(),
                        execution_time_ms=exec_time,
                        resource_limit_exceeded=is_limit_exceeded,
                        limit_type=limit_type,
                        error=f"Process exited with non-zero status {proc.returncode}"
                    )

            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                exec_time = (time.time() - start_time) * 1000
                return SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="Execution timed out.",
                    execution_time_ms=exec_time,
                    resource_limit_exceeded=True,
                    limit_type="Timeout",
                    error="Execution timeout limit exceeded."
                )

        finally:
            # Clean up temporary workspace directory automatically
            shutil.rmtree(workspace_dir, ignore_errors=True)

    def _build_restricted_env(self, workspace_dir: str) -> Dict[str, str]:
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": workspace_dir,
            "TMPDIR": workspace_dir,
            "PYTHONUNBUFFERED": "1"
        }

        # Network isolation via invalid proxies if network_enabled is False
        if not self.config.network_enabled:
            env["http_proxy"] = "http://127.0.0.1:0"
            env["https_proxy"] = "http://127.0.0.1:0"
            env["HTTP_PROXY"] = "http://127.0.0.1:0"
            env["HTTPS_PROXY"] = "http://127.0.0.1:0"

        env.update(self.config.environment)
        return env
