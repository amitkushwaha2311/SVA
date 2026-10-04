import asyncio
import os
import tempfile
from pathlib import Path

# Adjust path if needed
import sys
sys.path.append('c:\\Users\\AMIT KUSHWAHA\\OneDrive\\Desktop\\SVA\\backend')

from app.providers.repository.git import GitProvider, GitProviderError

async def main():
    provider = GitProvider()
    with tempfile.TemporaryDirectory() as td:
        target_dir = Path(td) / "repo"
        print(f"Target dir: {target_dir}")
        try:
            # fetch_snapshot is synchronous in the file, wait let me check if it's async or sync
            snapshot = provider.fetch_snapshot(
                identifier="https://github.com/amitkushwaha2311/LIFE-OS.git",
                revision="main",
                target_dir=target_dir
            )
            print("Success!", snapshot)
        except Exception as e:
            print("FAILED:", type(e), str(e))
            if hasattr(e, '__cause__') and e.__cause__:
                print("Cause:", e.__cause__)
                if hasattr(e.__cause__, 'stderr'):
                    print("STDERR:", e.__cause__.stderr)
                if hasattr(e.__cause__, 'stdout'):
                    print("STDOUT:", e.__cause__.stdout)

if __name__ == "__main__":
    asyncio.run(main())
