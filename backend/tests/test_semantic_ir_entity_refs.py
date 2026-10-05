"""
Focused tests: SemanticIRBuilder.code_entity_refs propagation
=============================================================

Verifies that ``SemanticRequirement.code_entity_refs`` is populated only
when a deterministic MODULE-entity match exists (exact file_path equality)
and is empty in all other cases.

Rules under test (from builder.py):
  - Only EntityType.MODULE entities are indexed.
  - A ref is emitted iff the candidate SourceLocation.path exactly equals
    the MODULE entity's file_path (no normalisation, no fuzzy matching).
  - Duplicates across multiple sources are collapsed by entity_id.
  - When code_entities is not supplied the field stays empty.
  - build_all() applies the same rules across a batch of candidates.
"""

import pytest

from app.repository.intent.models import (
    CandidateStatus,
    IntentCandidate,
    Provenance,
    SourceLocation,
)
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id
from app.semantic_ir.builder import SemanticIRBuilder, _build_module_index, _resolve_module_refs


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

REPO_ID = "test-repo"
ANALYSIS_ID = "test-run"

CODE_FILE = "app/auth/permissions.py"
OTHER_FILE = "app/models/user.py"


def make_module_entity(file_path: str) -> CodeEntity:
    eid = generate_entity_id(
        repository_id=REPO_ID,
        file_path=file_path,
        entity_type=EntityType.MODULE,
        name=file_path,
        start_line=1,
    )
    return CodeEntity(
        entity_id=eid,
        repository_id=REPO_ID,
        analysis_id=ANALYSIS_ID,
        file_path=file_path,
        entity_type=EntityType.MODULE,
        name=file_path,
        start_line=1,
        end_line=200,
        language="python",
        extraction_method="ast",
    )


def make_function_entity(file_path: str, name: str) -> CodeEntity:
    eid = generate_entity_id(
        repository_id=REPO_ID,
        file_path=file_path,
        entity_type=EntityType.FUNCTION,
        name=name,
        start_line=10,
    )
    return CodeEntity(
        entity_id=eid,
        repository_id=REPO_ID,
        analysis_id=ANALYSIS_ID,
        file_path=file_path,
        entity_type=EntityType.FUNCTION,
        name=name,
        start_line=10,
        end_line=30,
        language="python",
        extraction_method="ast",
    )


def make_candidate(
    sources,
    statement="Only project owners can delete projects.",
    provenance=Provenance.DOCUMENT,
):
    return IntentCandidate(
        candidate_id="cand-ref-test",
        analysis_id=ANALYSIS_ID,
        sources=sources,
        original_statement=statement,
        provenance=provenance,
        status=CandidateStatus.CANDIDATE,
        human_confirmed=False,
    )


@pytest.fixture
def builder():
    return SemanticIRBuilder()


@pytest.fixture
def module_entity():
    return make_module_entity(CODE_FILE)


@pytest.fixture
def other_module_entity():
    return make_module_entity(OTHER_FILE)


# ---------------------------------------------------------------------------
# _build_module_index unit tests
# ---------------------------------------------------------------------------

class TestBuildModuleIndex:
    def test_indexes_module_entity_by_file_path(self, module_entity):
        idx = _build_module_index([module_entity])
        assert CODE_FILE in idx
        assert idx[CODE_FILE] is module_entity

    def test_non_module_entities_are_excluded(self, module_entity):
        func = make_function_entity(CODE_FILE, "check_permission")
        idx = _build_module_index([module_entity, func])
        assert len(idx) == 1
        assert idx[CODE_FILE] is module_entity

    def test_empty_list_returns_empty_index(self):
        assert _build_module_index([]) == {}

    def test_indexes_multiple_modules(self, module_entity, other_module_entity):
        idx = _build_module_index([module_entity, other_module_entity])
        assert CODE_FILE in idx
        assert OTHER_FILE in idx


# ---------------------------------------------------------------------------
# _resolve_module_refs unit tests
# ---------------------------------------------------------------------------

class TestResolveModuleRefs:
    def test_exact_path_match_yields_ref(self, module_entity):
        idx = _build_module_index([module_entity])
        candidate = make_candidate(
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)]
        )
        refs = _resolve_module_refs(candidate, idx)
        assert len(refs) == 1
        assert refs[0].entity_id == module_entity.entity_id
        assert "exact:source_path==module_file_path" in refs[0].match_reason
        assert CODE_FILE in refs[0].match_reason

    def test_case_different_path_yields_no_ref(self, module_entity):
        idx = _build_module_index([module_entity])
        candidate = make_candidate(
            sources=[SourceLocation(path="App/Auth/Permissions.py", start_line=1, end_line=1)]
        )
        refs = _resolve_module_refs(candidate, idx)
        assert refs == []

    def test_empty_sources_yields_no_refs(self, module_entity):
        idx = _build_module_index([module_entity])
        candidate = make_candidate(sources=[])
        refs = _resolve_module_refs(candidate, idx)
        assert refs == []

    def test_source_with_no_matching_module_yields_no_ref(self, module_entity):
        idx = _build_module_index([module_entity])
        candidate = make_candidate(
            sources=[SourceLocation(path="docs/README.md", start_line=1, end_line=1)]
        )
        refs = _resolve_module_refs(candidate, idx)
        assert refs == []

    def test_duplicate_sources_same_file_yields_single_ref(self, module_entity):
        idx = _build_module_index([module_entity])
        candidate = make_candidate(
            sources=[
                SourceLocation(path=CODE_FILE, start_line=5, end_line=5),
                SourceLocation(path=CODE_FILE, start_line=10, end_line=10),
            ]
        )
        refs = _resolve_module_refs(candidate, idx)
        assert len(refs) == 1
        assert refs[0].entity_id == module_entity.entity_id

    def test_two_sources_different_files_yields_two_refs(self, module_entity, other_module_entity):
        idx = _build_module_index([module_entity, other_module_entity])
        candidate = make_candidate(
            sources=[
                SourceLocation(path=CODE_FILE, start_line=1, end_line=1),
                SourceLocation(path=OTHER_FILE, start_line=1, end_line=1),
            ]
        )
        refs = _resolve_module_refs(candidate, idx)
        assert len(refs) == 2
        entity_ids = {r.entity_id for r in refs}
        assert module_entity.entity_id in entity_ids
        assert other_module_entity.entity_id in entity_ids


# ---------------------------------------------------------------------------
# SemanticIRBuilder integration tests
# ---------------------------------------------------------------------------

class TestBuilderCodeEntityRefs:
    def test_build_without_code_entities_yields_empty_refs(self, builder):
        candidate = make_candidate(
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)]
        )
        req = builder.build_from_candidate(REPO_ID, candidate)
        assert req.code_entity_refs == []

    def test_build_with_matching_module_entity_yields_ref(self, builder, module_entity):
        candidate = make_candidate(
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)]
        )
        req = builder.build_from_candidate(REPO_ID, candidate, code_entities=[module_entity])
        assert len(req.code_entity_refs) == 1
        assert req.code_entity_refs[0].entity_id == module_entity.entity_id

    def test_build_with_non_module_entity_yields_empty_refs(self, builder):
        func = make_function_entity(CODE_FILE, "check_permission")
        candidate = make_candidate(
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)]
        )
        req = builder.build_from_candidate(REPO_ID, candidate, code_entities=[func])
        assert req.code_entity_refs == []

    def test_build_with_path_mismatch_yields_empty_refs(self, builder, module_entity):
        candidate = make_candidate(
            sources=[SourceLocation(path="TOTALLY/DIFFERENT.py", start_line=1, end_line=1)]
        )
        req = builder.build_from_candidate(REPO_ID, candidate, code_entities=[module_entity])
        assert req.code_entity_refs == []

    def test_build_all_propagates_refs_per_candidate(self, builder, module_entity):
        c1 = IntentCandidate(
            candidate_id="c1",
            analysis_id=ANALYSIS_ID,
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)],
            original_statement="Only project owners can delete projects.",
            provenance=Provenance.DOCUMENT,
        )
        c2 = IntentCandidate(
            candidate_id="c2",
            analysis_id=ANALYSIS_ID,
            sources=[SourceLocation(path="docs/POLICY.md", start_line=5, end_line=5)],
            original_statement="Only admins can access the dashboard.",
            provenance=Provenance.DOCUMENT,
        )
        reqs = builder.build_all(REPO_ID, [c1, c2], code_entities=[module_entity])
        assert len(reqs) == 2
        assert len(reqs[0].code_entity_refs) == 1
        assert reqs[0].code_entity_refs[0].entity_id == module_entity.entity_id
        assert reqs[1].code_entity_refs == []

    def test_build_all_without_code_entities_yields_empty_for_all(self, builder):
        candidates = [
            IntentCandidate(
                candidate_id="cx",
                analysis_id=ANALYSIS_ID,
                sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)],
                original_statement="Only project owners can delete projects.",
                provenance=Provenance.DOCUMENT,
            )
        ]
        reqs = builder.build_all(REPO_ID, candidates)
        assert all(req.code_entity_refs == [] for req in reqs)

    def test_ref_match_reason_contains_file_path(self, builder, module_entity):
        candidate = make_candidate(
            sources=[SourceLocation(path=CODE_FILE, start_line=1, end_line=1)]
        )
        req = builder.build_from_candidate(REPO_ID, candidate, code_entities=[module_entity])
        assert req.code_entity_refs[0].match_reason.endswith(CODE_FILE)

    def test_regression_existing_callers_no_code_entities(self, builder):
        candidate = IntentCandidate(
            candidate_id="cand-old",
            analysis_id=ANALYSIS_ID,
            sources=[SourceLocation(path="README.md", start_line=10, end_line=10)],
            original_statement="Users must log in.",
            provenance=Provenance.README,
            status=CandidateStatus.CANDIDATE,
            human_confirmed=False,
        )
        req = builder.build_from_candidate(REPO_ID, candidate)
        assert req.code_entity_refs == []
        assert req.candidate_id == "cand-old"
        assert req.provenance == Provenance.README
