import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch

from app.providers.repository.local import LocalProvider


@pytest.fixture
def workspace_dir(tmp_path):
    w = tmp_path / "workspace"
    w.mkdir()
    return str(w)


@pytest.fixture
def source_repo(tmp_path):
    # We must patch LocalProvider._is_authorized_path to allow tmp_path
    repo = tmp_path / "source_repo"
    repo.mkdir()
    
    (repo / "safe.txt").write_text("safe content")
    (repo / "dir").mkdir()
    (repo / "dir" / "nested.txt").write_text("nested content")
    
    try:
        # Internal symlink
        (repo / "internal_link.txt").symlink_to("safe.txt")
        
        # External symlink
        external_file = tmp_path / "external.txt"
        external_file.write_text("secret content")
        (repo / "external_link.txt").symlink_to(str(external_file))
        
        # Cyclic symlink
        (repo / "cycle1").symlink_to("cycle2")
        (repo / "cycle2").symlink_to("cycle1")
    except OSError as e:
        if getattr(e, 'winerror', None) == 1314:
            pytest.skip("Symlinks require Developer Mode or admin privileges on Windows")
        raise
        
    return str(repo)


def test_local_provider_ingest(workspace_dir, source_repo):
    provider = LocalProvider(source_repo, workspace_dir)
    
    # Mock authorization so it doesn't fail the "C:\Users..." absolute check on Windows testing
    with patch.object(provider, '_is_authorized_path', return_value=True):
        import asyncio
        asyncio.run(provider.ingest("main"))
        
    dest_path = Path(provider.get_target_directory())
    assert dest_path.exists()
    
    # Verify safe files were copied
    assert (dest_path / "safe.txt").read_text() == "safe content"
    assert (dest_path / "dir" / "nested.txt").read_text() == "nested content"
    
    # Verify symlinks were NOT evaluated as their target contents!
    # They should have been rejected or copied strictly as symlinks (PathGuard rejects symlink traversals)
    # The current local provider implementation skips symlinks to avoid escapes
    assert not (dest_path / "internal_link.txt").exists()
    assert not (dest_path / "external_link.txt").exists()
    assert not (dest_path / "cycle1").exists()
    assert not (dest_path / "cycle2").exists()

    # Fingerprint check
    manifest = provider.fingerprint()
    assert "safe.txt" in manifest
    assert "dir/nested.txt" in manifest
    assert "external_link.txt" not in manifest
    assert "cycle1" not in manifest

    # Cleanup check
    provider.cleanup()
    assert not dest_path.exists()
