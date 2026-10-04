import asyncio
from pathlib import Path
import tempfile
import shutil

from app.providers.repository.git import GitProvider

async def main():
    target = Path(tempfile.mkdtemp()) / "repo"
    provider = GitProvider()
    print("Testing GitProvider with https://github.com/octocat/Hello-World")
    try:
        metadata = provider.fetch_snapshot("https://github.com/octocat/Hello-World", "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d", target)
        print(f"SUCCESS! Metadata: {metadata.resolved_commit}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
    finally:
        if target.parent.exists():
            import stat, os
            def rm_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(target.parent, onerror=rm_readonly)

if __name__ == "__main__":
    asyncio.run(main())
