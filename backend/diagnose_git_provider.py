"""
Reproduce the exact GitProvider failure.
Run this to see what error Python subprocess gets when using
the restricted safe_env (no PATH, no SYSTEMROOT, etc.)
"""
import subprocess
import os
import sys
import tempfile
from pathlib import Path

# This is the exact safe_env from git.py
safe_env_original = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_ASKPASS": "/bin/false",
    "SSH_ASKPASS": "/bin/false",
    "GIT_SSH_COMMAND": "ssh -o StrictHostKeyChecking=no -o BatchMode=yes",
}

base_args = [
    "git",
    "-c", "core.hooksPath=/dev/null",
    "-c", "credential.helper=",
    "-c", "core.askPass=",
    "-c", "alias.clone=",
    "-c", "alias.checkout=",
    "-c", "alias.rev-parse=",
    "-c", "protocol.allow=never",
    "-c", "protocol.https.allow=always",
]

target = Path(tempfile.mkdtemp()) / "repo"
target.mkdir(parents=True, exist_ok=True)

clone_args = base_args + [
    "clone",
    "--no-checkout",
    "--quiet",
    "https://github.com/octocat/Hello-World",
    str(target),
]

print("=== TEST 1: Original safe_env (no PATH) ===")
try:
    result = subprocess.run(
        clone_args,
        cwd=str(target.parent),
        check=True,
        shell=False,
        env=safe_env_original,
        capture_output=True,
        text=True,
    )
    print("SUCCESS (unexpected)")
except subprocess.CalledProcessError as e:
    print(f"CalledProcessError: returncode={e.returncode}")
    print(f"stderr: {e.stderr!r}")
    print(f"stdout: {e.stdout!r}")
except FileNotFoundError as e:
    print(f"FileNotFoundError: {e}")
    print("DIAGNOSIS: 'git' executable not found because PATH is not in safe_env!")
except Exception as e:
    print(f"Other error: {type(e).__name__}: {e}")

# Cleanup
import shutil, stat
def rm_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)
if (target / ".git").exists():
    shutil.rmtree(target / ".git", onerror=rm_readonly)
if target.exists():
    shutil.rmtree(target, onerror=rm_readonly)
if target.parent.exists():
    shutil.rmtree(target.parent, onerror=rm_readonly)

print()
print("=== TEST 2: safe_env WITH PATH inherited ===")
target2 = Path(tempfile.mkdtemp()) / "repo"
target2.mkdir(parents=True, exist_ok=True)
clone_args2 = base_args + [
    "clone", "--no-checkout", "--quiet",
    "https://github.com/octocat/Hello-World",
    str(target2),
]
safe_env_with_path = {**safe_env_original}
if sys.platform == "win32":
    # On Windows, PATH and SYSTEMROOT are needed to find git.exe
    for k in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE"):
        if k in os.environ:
            safe_env_with_path[k] = os.environ[k]
    # GIT_ASKPASS must point to a real file on Windows -- /bin/false doesn't exist
    # Use a no-op: just remove GIT_ASKPASS so git uses built-in fail
    safe_env_with_path.pop("GIT_ASKPASS", None)
    safe_env_with_path.pop("SSH_ASKPASS", None)
else:
    if "PATH" in os.environ:
        safe_env_with_path["PATH"] = os.environ["PATH"]

try:
    result = subprocess.run(
        clone_args2,
        cwd=str(target2.parent),
        check=True,
        shell=False,
        env=safe_env_with_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    print("SUCCESS")
    print(f"stdout: {result.stdout!r}")
except subprocess.CalledProcessError as e:
    print(f"CalledProcessError: returncode={e.returncode}")
    print(f"stderr: {e.stderr!r}")
except FileNotFoundError as e:
    print(f"FileNotFoundError: {e}")
except Exception as e:
    print(f"Other error: {type(e).__name__}: {e}")

# Cleanup 2
if target2.exists():
    try:
        shutil.rmtree(target2.parent, onerror=rm_readonly)
    except Exception:
        pass
