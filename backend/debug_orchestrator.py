import asyncio
import tempfile
from pathlib import Path
from app.providers.repository.git import GitProvider

async def main():
    try:
        p = GitProvider()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            print("Cloning into", target)
            p.fetch_snapshot("https://github.com/amitkushwaha2311/LIFE-OS.git", "main", target)
            print("Success")
    except Exception as e:
        print(f"Exception: {e}")

asyncio.run(main())
