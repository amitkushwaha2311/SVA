"""
Tests for RepositoryManifest
============================

Verifies the aggregation of FileRecords into a top-level manifest.
"""

from __future__ import annotations

from pathlib import Path

from app.repository.manifest.repository_manifest import build_manifest
from app.repository.scanner.file_discovery import FileDiscovery
from app.repository.scanner.path_guard import PathGuard


class TestRepositoryManifest:
    def test_build_manifest_from_simple_python(self, simple_guard: PathGuard) -> None:
        discovery = FileDiscovery(guard=simple_guard)
        scan_result = discovery.scan()
        
        manifest = build_manifest(analysis_id="test-123", scan_result=scan_result)
        
        assert manifest.analysis_id == "test-123"
        assert manifest.file_count == scan_result.file_count
        assert manifest.total_size_bytes > 0
        assert manifest.repository_hash != ""
        
        # Check language inventory
        assert manifest.detected_languages.get("Python", 0) > 0
        
        # Check package manager detection
        # Should detect 'pip' because we have requirements.txt
        assert any(p.name == "pip" for p in manifest.detected_package_managers)
        
        # Check classification counts
        assert manifest.classification_counts.get("source_code", 0) > 0
        assert manifest.classification_counts.get("test", 0) > 0
        
        assert manifest.prompt_injection_finding_count == 0

    def test_build_manifest_from_injection_repo(self, injection_repo: Path) -> None:
        guard = PathGuard(root=injection_repo)
        discovery = FileDiscovery(guard=guard)
        scan_result = discovery.scan()
        
        manifest = build_manifest(analysis_id="test-inj", scan_result=scan_result)
        
        assert manifest.prompt_injection_finding_count > 0
