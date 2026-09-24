"""
Tests for FileDiscovery
=======================

Verifies that the scanner correctly traverses the repository via PathGuard,
classifies files, handles encoding/binary, and creates FileRecords.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.repository.scanner.file_discovery import FileDiscovery
from app.repository.scanner.path_guard import PathGuard
from app.repository.types import FileClassification


class TestFileDiscovery:
    def test_scan_simple_python_repo(self, simple_guard: PathGuard) -> None:
        """Scan the fixture repository and verify results."""
        discovery = FileDiscovery(guard=simple_guard)
        result = discovery.scan()

        assert result.root_path == simple_guard.root
        assert len(result.scan_errors) == 0
        assert result.file_count > 0

        # Verify specific files are classified correctly
        files_by_name = {Path(f.relative_path).name: f for f in result.files}

        assert "README.md" in files_by_name
        readme = files_by_name["README.md"]
        assert readme.classification == FileClassification.DOCUMENTATION
        assert readme.language == "Markdown"
        assert not readme.is_binary

        assert "utils.py" in files_by_name
        utils = files_by_name["utils.py"]
        assert utils.classification == FileClassification.SOURCE_CODE
        assert utils.language == "Python"
        assert utils.content_hash

        assert "test_utils.py" in files_by_name
        test_utils = files_by_name["test_utils.py"]
        assert test_utils.classification == FileClassification.TEST
        assert test_utils.language == "Python"

        assert "pyproject.toml" in files_by_name
        pyproject = files_by_name["pyproject.toml"]
        assert pyproject.classification == FileClassification.CONFIGURATION
        assert pyproject.language == "TOML"

    def test_scan_injection_repo(self, injection_repo: Path) -> None:
        """Verify prompt injection is detected but not acted upon."""
        guard = PathGuard(root=injection_repo)
        discovery = FileDiscovery(guard=guard)
        result = discovery.scan()

        # The scan must complete successfully
        assert len(result.scan_errors) == 0

        # It must find the security findings
        assert result.total_security_findings > 0

        # Verify the findings are attached to the right files
        files_by_name = {Path(f.relative_path).name: f for f in result.files}
        
        readme = files_by_name["README.md"]
        assert len(readme.prompt_injection_findings) > 0
        
        security = files_by_name["SECURITY.md"]
        assert len(security.prompt_injection_findings) > 0
        
        safe_code = files_by_name["safe_code.py"]
        assert len(safe_code.prompt_injection_findings) == 0

    def test_binary_file_handling(self, tmp_guard: PathGuard, tmp_repo: Path) -> None:
        """Verify binary files are detected and not decoded."""
        f = tmp_repo / "data.bin"
        f.write_bytes(bytes(range(256)))

        discovery = FileDiscovery(guard=tmp_guard)
        result = discovery.scan()

        assert result.file_count == 1
        record = result.files[0]
        assert record.is_binary is True
        assert record.encoding is None
        assert record.classification == FileClassification.ASSET

    def test_file_too_large_skipped(self, tmp_guard: PathGuard, tmp_repo: Path) -> None:
        """Verify files over max size are marked with read_error but not crashed."""
        f = tmp_repo / "huge.txt"
        f.write_bytes(b"x" * 1500)
        
        # Override guard max size
        guard = PathGuard(root=tmp_repo, max_file_size_bytes=1000)
        discovery = FileDiscovery(guard=guard)
        result = discovery.scan()

        assert result.file_count == 1
        record = result.files[0]
        assert "FILE_TOO_LARGE" in record.read_error
        assert record.content_hash == ""

    def test_max_files_limit(self, tmp_guard: PathGuard, tmp_repo: Path) -> None:
        """Verify the scan stops after max_files limit."""
        for i in range(5):
            (tmp_repo / f"file_{i}.txt").write_text("test")

        discovery = FileDiscovery(guard=tmp_guard, max_files=3)
        result = discovery.scan()

        assert result.file_count == 3
