"""
SVA Repository Manifest
=======================

Builds the top-level summary of a scanned repository — the entry point
for all downstream SVA analysis.

A RepositoryManifest is produced AFTER FileDiscovery completes.
It aggregates metadata across all FileRecords to produce summary statistics,
repository-level hash, and a framework/package-manager inventory.

This is purely a read-only summary. It does not execute any code.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.repository.types import (
    FileClassification,
    FileRecord,
    FrameworkCandidate,
    PackageManagerCandidate,
    ScanResult,
)


# ---------------------------------------------------------------------------
# Framework / package manager fingerprints
# ---------------------------------------------------------------------------
# Each entry: (display_name, [filenames that indicate this tool/framework])
# ---------------------------------------------------------------------------

_FRAMEWORK_FINGERPRINTS: list[tuple[str, list[str]]] = [
    # Python frameworks
    ("FastAPI", ["main.py"]),          # heuristic — refined by content later
    ("Django", ["manage.py", "settings.py"]),
    ("Flask", ["app.py", "wsgi.py"]),
    ("pytest", ["pytest.ini", "conftest.py"]),
    # JS / TS frameworks
    ("Next.js", ["next.config.js", "next.config.ts", "next.config.mjs"]),
    ("Vite", ["vite.config.js", "vite.config.ts"]),
    ("React", ["src/App.jsx", "src/App.tsx"]),
    ("Vue", ["vue.config.js", "src/main.vue"]),
    ("Angular", ["angular.json"]),
    ("Svelte", ["svelte.config.js"]),
    ("NestJS", ["nest-cli.json"]),
    ("Express", ["app.js", "server.js"]), # Weak heuristic
    # Java
    ("Spring Boot", ["pom.xml", "build.gradle"]), # Weak heuristic, refined later
    # Mobile
    ("Flutter", ["pubspec.yaml"]),
    ("React Native", ["metro.config.js"]),
    # Infrastructure
    ("Docker", ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]),
    ("Kubernetes", ["k8s", "kubernetes"]),
    ("Terraform", ["main.tf"]),
    ("Ansible", ["playbook.yml", "site.yml"]),
]

_PACKAGE_MANAGER_FINGERPRINTS: list[tuple[str, list[str]]] = [
    ("npm", ["package-lock.json"]),
    ("yarn", ["yarn.lock", ".yarnrc.yml"]),
    ("pnpm", ["pnpm-lock.yaml", ".pnpmfile.cjs"]),
    ("bun", ["bun.lockb", "bun.lock"]),
    ("poetry", ["poetry.lock"]),
    ("pipenv", ["Pipfile.lock"]),
    ("uv", ["uv.lock"]),
    ("pip", ["requirements.txt", "requirements-dev.txt"]),
    ("conda", ["environment.yml", "environment.yaml", "conda.yml"]),
    ("cargo", ["Cargo.lock"]),
    ("go modules", ["go.mod", "go.sum"]),
    ("bundler", ["Gemfile.lock"]),
    ("maven", ["pom.xml"]),
    ("gradle", ["build.gradle", "build.gradle.kts"]),
    ("composer", ["composer.json", "composer.lock"]),
    ("nuget", ["*.csproj", "packages.config", "NuGet.Config"]),
    ("pub", ["pubspec.lock"]),
    ("mix", ["mix.lock"]),
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class RepositoryManifest:
    """
    Top-level summary of a scanned repository.

    Produced from a ScanResult after FileDiscovery completes.
    All values are derived from the scanned FileRecords — nothing is
    inferred, executed, or fabricated.
    """

    analysis_id: str
    root_path: str
    timestamp: datetime

    # Repository fingerprint
    repository_hash: str  # SHA-256 of sorted "path:hash" pairs

    # Counts
    file_count: int
    source_file_count: int
    test_file_count: int
    documentation_count: int
    total_size_bytes: int

    # Language inventory: { language_name → file_count }
    detected_languages: dict[str, int] = field(default_factory=dict)

    # Detected frameworks and package managers with evidence
    detected_frameworks: list[FrameworkCandidate] = field(default_factory=list)
    detected_package_managers: list[PackageManagerCandidate] = field(default_factory=list)

    # Classification breakdown
    classification_counts: dict[str, int] = field(default_factory=dict)

    # Security summary
    prompt_injection_finding_count: int = 0
    files_skipped_too_large: int = 0
    files_with_read_errors: int = 0


def build_manifest(
    analysis_id: str,
    scan_result: ScanResult,
    timestamp: datetime | None = None,
) -> RepositoryManifest:
    """
    Build a RepositoryManifest from a completed ScanResult.
    """
    if timestamp is None:
        timestamp = datetime.now(tz=timezone.utc)

    files = scan_result.files

    # --- Repository hash -------------------------------------------------
    repo_hash = _compute_repository_hash(files)

    # --- Totals ----------------------------------------------------------
    total_size = sum(f.size_bytes for f in files)
    
    source_count = 0
    test_count = 0
    doc_count = 0

    # --- Language inventory ----------------------------------------------
    lang_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    
    for f in files:
        if f.language:
            lang_counts[f.language] = lang_counts.get(f.language, 0) + 1
            
        key = f.classification.value
        class_counts[key] = class_counts.get(key, 0) + 1
        
        if f.classification == FileClassification.SOURCE_CODE:
            source_count += 1
        elif f.classification == FileClassification.TEST:
            test_count += 1
        elif f.classification == FileClassification.DOCUMENTATION:
            doc_count += 1

    # --- Framework / package manager detection ---------------------------
    path_map = {Path(f.relative_path).name.lower(): f.relative_path for f in files}

    frameworks = _detect_frameworks(path_map)
    package_managers = _detect_package_managers(path_map)

    # --- Security summary ------------------------------------------------
    injection_count = sum(
        len(f.prompt_injection_findings) for f in files
    )
    files_with_errors = sum(1 for f in files if f.read_error is not None)

    return RepositoryManifest(
        analysis_id=analysis_id,
        root_path=str(scan_result.root_path),
        timestamp=timestamp,
        repository_hash=repo_hash,
        file_count=len(files),
        source_file_count=source_count,
        test_file_count=test_count,
        documentation_count=doc_count,
        total_size_bytes=total_size,
        detected_languages=dict(
            sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        detected_frameworks=frameworks,
        detected_package_managers=package_managers,
        classification_counts=class_counts,
        prompt_injection_finding_count=injection_count,
        files_skipped_too_large=scan_result.skipped_too_large,
        files_with_read_errors=files_with_errors,
    )


def _compute_repository_hash(files: list[FileRecord]) -> str:
    """
    Compute a deterministic SHA-256 hash representing the repository state.
    Built from sorted ``relative_path:content_hash`` pairs.
    """
    h = hashlib.sha256()
    for f in sorted(files, key=lambda x: x.relative_path):
        entry = f"{f.relative_path}:{f.content_hash or 'UNREAD'}\n"
        h.update(entry.encode("utf-8"))
    return h.hexdigest()


def _detect_frameworks(path_map: dict[str, str]) -> list[FrameworkCandidate]:
    """
    Heuristically detect frameworks by filename presence.
    """
    detected = []
    seen = set()
    for name, indicators in _FRAMEWORK_FINGERPRINTS:
        for indicator in indicators:
            ind_lower = indicator.lower()
            # Simple filename match
            if ind_lower in path_map:
                if name not in seen:
                    detected.append(FrameworkCandidate(
                        name=name,
                        evidence_type="filename",
                        evidence_path=path_map[ind_lower],
                        reason=f"Found framework indicator file '{indicator}'"
                    ))
                    seen.add(name)
                break
            
            # Directory/path match
            for filename, full_path in path_map.items():
                if f"/{ind_lower}/" in f"/{full_path.lower()}/" or full_path.lower().startswith(f"{ind_lower}/"):
                    if name not in seen:
                        detected.append(FrameworkCandidate(
                            name=name,
                            evidence_type="directory",
                            evidence_path=full_path,
                            reason=f"Found framework directory indicator '{indicator}'"
                        ))
                        seen.add(name)
                    break
    return detected


def _detect_package_managers(path_map: dict[str, str]) -> list[PackageManagerCandidate]:
    """
    Detect package managers by characteristic filename presence.
    """
    detected = []
    seen = set()
    for name, indicators in _PACKAGE_MANAGER_FINGERPRINTS:
        for indicator in indicators:
            ind_lower = indicator.lower()
            if ind_lower.startswith("*"):
                ext = ind_lower[1:]
                for filename, full_path in path_map.items():
                    if filename.endswith(ext):
                        if name not in seen:
                            detected.append(PackageManagerCandidate(
                                name=name,
                                evidence_type="filename_pattern",
                                evidence_path=full_path,
                                reason=f"Found package manager file pattern '{indicator}'"
                            ))
                            seen.add(name)
                        break
            elif ind_lower in path_map:
                if name not in seen:
                    detected.append(PackageManagerCandidate(
                        name=name,
                        evidence_type="filename",
                        evidence_path=path_map[ind_lower],
                        reason=f"Found package manager lockfile/config '{indicator}'"
                    ))
                    seen.add(name)
                break
    return detected
