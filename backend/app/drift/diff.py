"""
SVA Semantic Drift Diff
=======================

Compares two repository states (base vs target) to detect file and entity changes.
Implements conservative, deterministic detection rules.
"""

from __future__ import annotations

from app.drift.models import (
    ChangeRecord,
    DriftSeverity,
    DriftType,
    EntityChangeType,
    FileChangeType,
    generate_change_id,
)
from app.repository.parser.models import CodeEntity, EntityType
from app.repository.types import FileClassification, FileRecord


class RepositoryDiff:
    """Detects deterministic changes between base and target repository states."""

    def detect_changes(
        self,
        repository_id: str,
        base_commit: str,
        target_commit: str,
        base_files: list[FileRecord],
        target_files: list[FileRecord],
        base_entities: list[CodeEntity],
        target_entities: list[CodeEntity],
    ) -> list[ChangeRecord]:
        """
        Compare base and target states to produce a list of ChangeRecords.
        """
        changes: list[ChangeRecord] = []
        
        # 1. File-level changes
        base_file_map = {f.relative_path: f for f in base_files}
        target_file_map = {f.relative_path: f for f in target_files}
        
        # Detect ADDED, MODIFIED, UNCHANGED files in target
        for path, t_file in target_file_map.items():
            if path not in base_file_map:
                changes.append(self._create_file_change(
                    repository_id, base_commit, target_commit,
                    path, t_file.classification, FileChangeType.ADDED,
                    None, t_file.content_hash,
                ))
            else:
                b_file = base_file_map[path]
                if t_file.content_hash != b_file.content_hash:
                    changes.append(self._create_file_change(
                        repository_id, base_commit, target_commit,
                        path, t_file.classification, FileChangeType.MODIFIED,
                        b_file.content_hash, t_file.content_hash,
                    ))
                # UNCHANGED files don't generate generic ChangeRecords unless entities within them change.
        
        # Detect REMOVED files from base
        for path, b_file in base_file_map.items():
            if path not in target_file_map:
                changes.append(self._create_file_change(
                    repository_id, base_commit, target_commit,
                    path, b_file.classification, FileChangeType.REMOVED,
                    b_file.content_hash, None,
                ))
        
        # Handle RENAMED heuristics (Same content hash, different path)
        # We replace the independent ADDED and REMOVED with a linked REMOVED + ADDED.
        # This keeps the diff explicit rather than silently merging.
        added_changes = [c for c in changes if c.file_change_type == FileChangeType.ADDED]
        removed_changes = [c for c in changes if c.file_change_type == FileChangeType.REMOVED]
        
        for ac in added_changes:
            for rc in removed_changes:
                if ac.target_content_hash == rc.base_content_hash and ac.target_content_hash is not None:
                    ac.file_change_type = FileChangeType.RENAMED
                    ac.description = f"File renamed from {rc.file_path}"
                    
                    rc.file_change_type = FileChangeType.RENAMED
                    rc.description = f"File renamed to {ac.file_path}"
                    break

        # 2. Entity-level changes
        base_entity_map = {e.entity_id: e for e in base_entities}
        target_entity_map = {e.entity_id: e for e in target_entities}
        
        # Detect ADDED entities
        for eid, t_ent in target_entity_map.items():
            if eid not in base_entity_map:
                # Is it a re-identification? (Same path, type, name; different start_line)
                reidentified = False
                for b_ent in base_entities:
                    if (b_ent.file_path == t_ent.file_path and 
                        b_ent.entity_type == t_ent.entity_type and 
                        b_ent.name == t_ent.name and 
                        b_ent.start_line != t_ent.start_line):
                        
                        changes.append(self._create_entity_change(
                            repository_id, base_commit, target_commit,
                            t_ent, EntityChangeType.REIDENTIFIED,
                            "Entity shifted/reidentified at a new location."
                        ))
                        reidentified = True
                        break
                
                if not reidentified:
                    changes.append(self._create_entity_change(
                        repository_id, base_commit, target_commit,
                        t_ent, EntityChangeType.ADDED,
                        f"New entity '{t_ent.name}' added."
                    ))
        
        # Detect REMOVED entities
        for eid, b_ent in base_entity_map.items():
            if eid not in target_entity_map:
                # If it was already marked reidentified above, skip.
                # We check if there's a target entity with same (path, type, name).
                reidentified = False
                for t_ent in target_entities:
                    if (b_ent.file_path == t_ent.file_path and 
                        b_ent.entity_type == t_ent.entity_type and 
                        b_ent.name == t_ent.name and 
                        b_ent.start_line != t_ent.start_line):
                        reidentified = True
                        break
                
                if not reidentified:
                    changes.append(self._create_entity_change(
                        repository_id, base_commit, target_commit,
                        b_ent, EntityChangeType.REMOVED,
                        f"Entity '{b_ent.name}' removed."
                    ))
        
        # Determine MODIFIED entities
        # Since Phase 3 lacks an entity body hash, we must infer modification from file changes.
        # If the file is modified, but the entity ID remains identical, its body *might* have changed.
        modified_file_paths = {c.file_path for c in changes if c.file_change_type == FileChangeType.MODIFIED}
        for eid, t_ent in target_entity_map.items():
            if eid in base_entity_map and t_ent.file_path in modified_file_paths:
                changes.append(self._create_entity_change(
                    repository_id, base_commit, target_commit,
                    t_ent, EntityChangeType.UNKNOWN,
                    "Entity identity unchanged, but containing file modified. Exact body modification is UNKNOWN."
                ))

        return changes

    def _create_file_change(
        self,
        repository_id: str,
        base_commit: str,
        target_commit: str,
        file_path: str,
        classification: FileClassification,
        change_type: FileChangeType,
        base_hash: str | None,
        target_hash: str | None,
    ) -> ChangeRecord:
        
        canonical = f"FILE_{change_type.value}:{file_path}"
        cid = generate_change_id(repository_id, base_commit, target_commit, file_path, canonical)
        
        drift_type = self._classify_file_drift(classification, change_type)
        severity = DriftSeverity.UNKNOWN if drift_type == DriftType.UNKNOWN else DriftSeverity.LOW
        
        return ChangeRecord(
            change_id=cid,
            repository_id=repository_id,
            base_commit=base_commit,
            target_commit=target_commit,
            file_path=file_path,
            file_classification=classification,
            file_change_type=change_type,
            drift_type=drift_type,
            drift_severity=severity,
            description=f"File {file_path} was {change_type.value.lower()}.",
            base_content_hash=base_hash,
            target_content_hash=target_hash,
        )

    def _create_entity_change(
        self,
        repository_id: str,
        base_commit: str,
        target_commit: str,
        entity: CodeEntity,
        change_type: EntityChangeType,
        description: str,
    ) -> ChangeRecord:
        
        canonical = f"ENTITY_{change_type.value}:{entity.entity_id}"
        cid = generate_change_id(repository_id, base_commit, target_commit, entity.file_path, canonical)
        
        drift_type = self._classify_entity_drift(entity, change_type)
        
        return ChangeRecord(
            change_id=cid,
            repository_id=repository_id,
            base_commit=base_commit,
            target_commit=target_commit,
            file_path=entity.file_path,
            # We don't have file_classification here directly, use UNKNOWN for safety.
            # Real implementation would look it up from files list.
            file_classification=FileClassification.UNKNOWN,
            file_change_type=FileChangeType.UNCHANGED,
            entity_id=entity.entity_id,
            entity_change_type=change_type,
            drift_type=drift_type,
            drift_severity=DriftSeverity.UNKNOWN,
            description=description,
        )

    def _classify_file_drift(self, classification: FileClassification, change_type: FileChangeType) -> DriftType:
        if classification in (FileClassification.DOCUMENTATION, FileClassification.ASSET, FileClassification.GENERATED):
            return DriftType.TEXTUAL
        if classification == FileClassification.CONFIGURATION:
            return DriftType.CONFIGURATION
        return DriftType.UNKNOWN

    def _classify_entity_drift(self, entity: CodeEntity, change_type: EntityChangeType) -> DriftType:
        auth_keywords = {"auth", "login", "permission", "role", "admin", "owner"}
        lower_name = entity.name.lower()
        
        if any(k in lower_name for k in auth_keywords):
            return DriftType.AUTHORIZATION
            
        if entity.entity_type == EntityType.API_ROUTE:
            return DriftType.API
            
        if entity.entity_type == EntityType.DATABASE_MODEL:
            return DriftType.DATA
            
        if change_type in (EntityChangeType.ADDED, EntityChangeType.REMOVED):
            return DriftType.STRUCTURAL
            
        if change_type == EntityChangeType.UNKNOWN:
            return DriftType.UNKNOWN
            
        return DriftType.BEHAVIORAL
