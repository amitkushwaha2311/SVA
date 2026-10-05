"""
IntentMapper round-trip tests
==============================

Proves that SourceLocation objects survive:
  IntentCandidate -> IntentCandidateRow  (to_row)
  IntentCandidateRow -> IntentCandidate  (from_row)

These are pure in-process unit tests -- no database required.
"""
import pytest

from app.repository.intent.models import (
    CandidateStatus,
    IntentCandidate,
    Provenance,
    SourceLocation,
)
from app.persistence.models.intent import IntentCandidateRow
from app.persistence.mappers.intent_mapper import IntentMapper, _dict_to_source, _source_to_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidate(
    candidate_id: str = "cand-abc",
    analysis_id: str = "run-001",
    original_statement: str = "Only project owners can delete projects.",
    sources=None,
    provenance=Provenance.DOCUMENT,
    human_confirmed: bool = False,
    status=CandidateStatus.CANDIDATE,
):
    return IntentCandidate(
        candidate_id=candidate_id,
        analysis_id=analysis_id,
        original_statement=original_statement,
        sources=sources or [],
        provenance=provenance,
        status=status,
        human_confirmed=human_confirmed,
        extraction_method="RULE_BASED",
    )


# ---------------------------------------------------------------------------
# _source_to_dict / _dict_to_source unit tests
# ---------------------------------------------------------------------------

class TestSourceLocationSerialization:
    def test_source_to_dict_preserves_all_fields(self):
        src = SourceLocation(path="docs/README.md", start_line=7, end_line=7)
        d = _source_to_dict(src)
        assert d["path"] == "docs/README.md"
        assert d["start_line"] == 7
        assert d["end_line"] == 7

    def test_dict_to_source_preserves_all_fields(self):
        d = {"path": "api/swagger.yaml", "start_line": 42, "end_line": 44}
        src = _dict_to_source(d)
        assert src.path == "api/swagger.yaml"
        assert src.start_line == 42
        assert src.end_line == 44

    def test_round_trip_is_lossless(self):
        original = SourceLocation(path="policy.md", start_line=3, end_line=3)
        reconstructed = _dict_to_source(_source_to_dict(original))
        assert reconstructed == original


# ---------------------------------------------------------------------------
# IntentMapper.to_row() tests
# ---------------------------------------------------------------------------

class TestIntentMapperToRow:
    def test_to_row_serializes_single_source(self):
        src = SourceLocation(path="README.md", start_line=5, end_line=5)
        cand = _make_candidate(sources=[src])
        row = IntentMapper.to_row(cand)
        assert isinstance(row.sources, list)
        assert len(row.sources) == 1
        assert row.sources[0]["path"] == "README.md"
        assert row.sources[0]["start_line"] == 5
        assert row.sources[0]["end_line"] == 5

    def test_to_row_serializes_multiple_sources(self):
        srcs = [
            SourceLocation(path="a.md", start_line=1, end_line=1),
            SourceLocation(path="b.md", start_line=10, end_line=12),
        ]
        cand = _make_candidate(sources=srcs)
        row = IntentMapper.to_row(cand)
        assert len(row.sources) == 2
        assert row.sources[0]["path"] == "a.md"
        assert row.sources[1]["path"] == "b.md"

    def test_to_row_empty_sources_stores_empty_list(self):
        cand = _make_candidate(sources=[])
        row = IntentMapper.to_row(cand)
        assert row.sources == []


# ---------------------------------------------------------------------------
# IntentMapper.from_row() tests
# ---------------------------------------------------------------------------

class TestIntentMapperFromRow:
    def _make_row(
        self,
        sources=None,
        candidate_id="cand-abc",
        analysis_id="run-001",
        original_statement="Only project owners can delete projects.",
        status="CANDIDATE",
        human_confirmed=False,
        provenance="DOCUMENT",
    ):
        return IntentCandidateRow(
            candidate_id=candidate_id,
            analysis_id=analysis_id,
            original_statement=original_statement,
            normalized_statement=None,
            status=status,
            human_confirmed=human_confirmed,
            extraction_method="RULE_BASED",
            sources=sources if sources is not None else [],
            provenance=provenance,
            evidence=[],
        )

    def test_from_row_deserializes_single_source(self):
        row = self._make_row(sources=[{"path": "README.md", "start_line": 5, "end_line": 5}])
        candidate = IntentMapper.from_row(row)
        assert len(candidate.sources) == 1
        assert candidate.sources[0].path == "README.md"
        assert candidate.sources[0].start_line == 5
        assert candidate.sources[0].end_line == 5

    def test_from_row_deserializes_multiple_sources(self):
        row = self._make_row(sources=[
            {"path": "a.md", "start_line": 1, "end_line": 1},
            {"path": "b.md", "start_line": 10, "end_line": 12},
        ])
        candidate = IntentMapper.from_row(row)
        assert len(candidate.sources) == 2
        assert candidate.sources[0].path == "a.md"
        assert candidate.sources[1].path == "b.md"
        assert candidate.sources[1].end_line == 12

    def test_from_row_empty_sources_returns_empty_list(self):
        row = self._make_row(sources=[])
        candidate = IntentMapper.from_row(row)
        assert candidate.sources == []

    def test_from_row_null_sources_returns_empty_list(self):
        """DB column may return None for rows inserted without sources."""
        row = self._make_row(sources=None)
        candidate = IntentMapper.from_row(row)
        assert candidate.sources == []

    def test_from_row_sources_are_source_location_instances(self):
        row = self._make_row(sources=[{"path": "p.md", "start_line": 1, "end_line": 2}])
        candidate = IntentMapper.from_row(row)
        assert all(isinstance(s, SourceLocation) for s in candidate.sources)


# ---------------------------------------------------------------------------
# Full round-trip tests
# ---------------------------------------------------------------------------

class TestIntentMapperRoundTrip:
    def test_round_trip_preserves_single_source_exactly(self):
        src = SourceLocation(path="docs/policy.md", start_line=7, end_line=7)
        original = _make_candidate(sources=[src])
        row = IntentMapper.to_row(original)
        reconstructed = IntentMapper.from_row(row)
        assert len(reconstructed.sources) == 1
        assert reconstructed.sources[0] == src

    def test_round_trip_preserves_multiple_sources_exactly(self):
        srcs = [
            SourceLocation(path="README.md", start_line=1, end_line=1),
            SourceLocation(path="SECURITY.md", start_line=42, end_line=42),
        ]
        original = _make_candidate(sources=srcs)
        row = IntentMapper.to_row(original)
        reconstructed = IntentMapper.from_row(row)
        assert reconstructed.sources == srcs

    def test_round_trip_preserves_empty_sources(self):
        original = _make_candidate(sources=[])
        row = IntentMapper.to_row(original)
        reconstructed = IntentMapper.from_row(row)
        assert reconstructed.sources == []

    def test_round_trip_preserves_multiline_source(self):
        src = SourceLocation(path="api/openapi.yaml", start_line=10, end_line=25)
        original = _make_candidate(sources=[src])
        row = IntentMapper.to_row(original)
        reconstructed = IntentMapper.from_row(row)
        assert reconstructed.sources[0].start_line == 10
        assert reconstructed.sources[0].end_line == 25

    def test_round_trip_preserves_other_candidate_fields(self):
        """Ensure sources fix does not disturb other fields."""
        src = SourceLocation(path="docs/req.md", start_line=3, end_line=3)
        original = _make_candidate(
            candidate_id="c-xyz",
            analysis_id="run-42",
            original_statement="Only project owners can delete projects.",
            sources=[src],
            provenance=Provenance.DOCUMENT,
            human_confirmed=False,
            status=CandidateStatus.CANDIDATE,
        )
        row = IntentMapper.to_row(original)
        reconstructed = IntentMapper.from_row(row)
        assert reconstructed.candidate_id == "c-xyz"
        assert reconstructed.analysis_id == "run-42"
        assert reconstructed.original_statement == "Only project owners can delete projects."
        assert reconstructed.provenance == Provenance.DOCUMENT
        assert reconstructed.human_confirmed is False
        assert reconstructed.status == CandidateStatus.CANDIDATE
        assert reconstructed.sources[0] == src
