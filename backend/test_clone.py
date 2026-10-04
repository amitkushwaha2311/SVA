import subprocess
import os

env = os.environ.copy()
env['GIT_TERMINAL_PROMPT'] = '0'
env['GIT_ASKPASS'] = '/bin/false'
env['SSH_ASKPASS'] = '/bin/false'

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

clone_args = base_args + [
    "clone",
    "--no-checkout",
    "--quiet",
    "https://github.com/amitkushwaha2311/LIFE-OS.git",
    "test_clone",
]

try:
    subprocess.run(
        clone_args,
        check=True,
        shell=False,
        env=env,
        capture_output=True,
        text=True,
    )
    print("Success")
except subprocess.CalledProcessError as e:
    print("Error code:", e.returncode)
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
