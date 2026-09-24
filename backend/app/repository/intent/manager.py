"""
SVA Intent Manager
==================

Orchestrates intent discovery across a repository and performs cross-file deduplication.
"""

from __future__ import annotations

from app.core.logging_config import get_logger
from app.repository.intent.extractor import DocumentationExtractor
from app.repository.intent.models import IntentCandidate, Provenance
from app.repository.types import FileClassification, FileRecord

logger = get_logger("repository.intent.manager")


class IntentManager:
    """Discovers and manages intent candidates across the repository."""

    def __init__(self) -> None:
        self.extractor = DocumentationExtractor()

    def _determine_provenance(self, record: FileRecord) -> Provenance:
        """Map FileRecord classification to Provenance."""
        name_lower = record.relative_path.lower()
        if "readme" in name_lower:
            return Provenance.README
        if "api" in name_lower and ("swagger" in name_lower or "openapi" in name_lower):
            return Provenance.API_CONTRACT
        if record.classification == FileClassification.DOCUMENTATION:
            return Provenance.DOCUMENT
        # We don't extract from code/tests in this rule-based documentation phase
        return Provenance.DEFAULT

    def discover_intents(
        self,
        repository_id: str,
        analysis_id: str,
        file_records: list[FileRecord],
        content_map: dict[str, bytes],
    ) -> list[IntentCandidate]:
        """
        Discover intent candidates across all relevant files, deduplicating
        identical statements while preserving all source locations.
        """
        candidate_map: dict[str, IntentCandidate] = {}

        for record in file_records:
            if record.is_binary or record.read_error:
                continue

            provenance = self._determine_provenance(record)
            if provenance == Provenance.DEFAULT:
                # Skip non-documentation files for intent discovery in Phase 4
                continue

            content = content_map.get(record.relative_path)
            if not content:
                continue

            try:
                candidates = self.extractor.extract(
                    repository_id=repository_id,
                    analysis_id=analysis_id,
                    file_path=record.relative_path,
                    content=content,
                    provenance=provenance,
                )

                for c in candidates:
                    # Deduplication: If the exact statement already exists, append the source
                    if c.candidate_id in candidate_map:
                        existing = candidate_map[c.candidate_id]
                        # Don't add duplicate source locations (e.g. if the same line matches twice somehow)
                        for src in c.sources:
                            if src not in existing.sources:
                                existing.sources.append(src)
                        # We keep the provenance of the first discovery, or we could upgrade it.
                        # For now, first-seen provenance remains.
                    else:
                        candidate_map[c.candidate_id] = c
            except Exception as exc:
                # Parse error isolation
                logger.warning(
                    "Intent extraction failed on %s: %s", record.relative_path, exc
                )

        final_candidates = list(candidate_map.values())
        logger.info(
            "Intent discovery complete: %d unique candidates found.",
            len(final_candidates),
        )
        return final_candidates
