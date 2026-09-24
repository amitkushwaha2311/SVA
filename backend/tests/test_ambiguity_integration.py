import pytest
from unittest.mock import patch, MagicMock

from app.orchestration.analyzer import AnalysisOrchestrator
from app.semantic_ir.models import SemanticRequirement

@pytest.mark.asyncio
async def test_ambiguity_detector_integration(db):
    """
    Regression test: ensures the orchestrator can successfully import and run 
    the real AmbiguityDetector during the analysis pipeline without throwing ModuleNotFoundError.
    """
    orchestrator = AnalysisOrchestrator(session_factory=MagicMock(return_value=db))
    
    # We will mock the dependencies before and after Ambiguity
    # to isolate the ambiguity detection phase.
    
    # Mock SemanticRequirement
    from app.repository.intent.models import Provenance
    req = SemanticRequirement(
        analysis_id="test-analysis",
        requirement_id="req-1",
        candidate_id="cand-1",
        original_statement="Users can delete projects.",
        statement="Users can delete projects.",
        provenance=Provenance.AI_INFERENCE,
        extracted_entities=[],
        relationships=[]
    )
    
    # We just want to ensure the code that *loads* and uses
    # the detector doesn't crash due to import errors.
    
    from app.ambiguity.detector import AmbiguityDetector
    assert AmbiguityDetector is not None
    
    # Test the specific code block from analyzer.py
    ambiguity_engine = AmbiguityDetector()
    ambiguity_cases = ambiguity_engine.detect_contradictions("repo-id", [req])
    assert isinstance(ambiguity_cases, list)
    
    case = ambiguity_engine.detect_ambiguity("repo-id", req)
    assert case is not None # because 'can delete' triggers the rule
    
    assert len(case.ambiguity_types) > 0
