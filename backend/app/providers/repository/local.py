import os
import shutil
from pathlib import Path
import hashlib
from typing import Optional

from .base import RepositoryProvider, RepositoryMetadata, IngestionError

class LocalProviderError(IngestionError):
    pass


class LocalProvider(RepositoryProvider):
    """
    Provider for securely ingesting local directories.
    
    Security controls:
    - Walk via lstat (no symlink traversal).
    - Silently drop or explicitly reject symlinks to prevent escapes.
    - Reject special devices/sockets.
    - Path containment check on destination.
    """

    def fetch_snapshot(self, identifier: str, revision: str, target_dir: Path) -> RepositoryMetadata:
        source = Path(identifier).resolve()
        
        if not source.exists() or not source.is_dir():
            raise LocalProviderError(f"Local source directory not found: {identifier}")

        self._safe_copy(source, target_dir)

        # For a purely local directory that isn't a Git repo, we simulate a commit hash
        # or we could parse local git if it exists, but we'll treat it as a pure directory.
        pseudo_commit = self._hash_directory(target_dir)

        return RepositoryMetadata(
            provider="local",
            repository_identifier=str(source),
            default_branch="main",
            revision="local",
            resolved_commit=pseudo_commit
        )

    def _safe_copy(self, source_root: Path, target_root: Path) -> None:
        """
        Securely copy source to target without dereferencing symlinks
        and rejecting unsafe file types.
        """
        for root, dirs, files in os.walk(source_root, followlinks=False):
            rel_root = Path(root).relative_to(source_root)
            dest_dir = target_root / rel_root
            
            # Ensure dest_dir stays within target_root (containment)
            if not dest_dir.resolve().is_relative_to(target_root.resolve()):
                raise LocalProviderError(f"Path traversal detected in destination: {dest_dir}")
                
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Process files safely using lstat
            for f in files:
                src_file = Path(root) / f
                
                try:
                    stat_info = src_file.lstat()
                except OSError:
                    continue # Ignore files we can't stat
                    
                # Reject symlinks entirely for maximum safety during snapshot creation
                import stat
                if stat.S_ISLNK(stat_info.st_mode):
                    continue
                    
                # Reject anything that is not a regular file
                if not stat.S_ISREG(stat_info.st_mode):
                    continue

                dest_file = dest_dir / f
                
                # Check for traversal on individual file
                if not dest_file.resolve().is_relative_to(target_root.resolve()):
                    raise LocalProviderError(f"Path traversal detected for file: {dest_file}")
                
                try:
                    shutil.copy2(src_file, dest_file, follow_symlinks=False)
                except OSError as e:
                    raise LocalProviderError(f"Failed to copy file {src_file}: {e}")

    def _hash_directory(self, dir_path: Path) -> str:
        """Generate a stable pseudo-commit hash based on filenames and contents."""
        hasher = hashlib.sha256()
        
        # Sort files to ensure deterministic hashing
        files = sorted(dir_path.rglob("*"))
        for f in files:
            if f.is_file():
                rel_path = f.relative_to(dir_path).as_posix()
                hasher.update(rel_path.encode('utf-8'))
                # For large directories this could be slow, but it's local dev provider.
                try:
                    hasher.update(f.read_bytes())
                except OSError:
                    pass
                    
        return hasher.hexdigest()
