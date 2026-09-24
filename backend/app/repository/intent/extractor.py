"""
SVA Documentation Extractor
===========================

Conservative, rule-based extraction of intent candidates from text/markdown.
"""

import re
from typing import Iterator

from app.repository.intent.models import (
    CandidateStatus,
    IntentCandidate,
    Provenance,
    SourceLocation,
    generate_candidate_id,
)

# A simple heuristic pattern to find sentences that MIGHT express intent.
# This does NOT mean they are requirements.
# We match full sentences containing the keywords.
# e.g., "Users must authenticate before accessing projects."
# Or "The system shall log all errors."
_INTENT_KEYWORDS = r"\b(?:must|shall|should|required|only|cannot|may|users can|users must|system should|system shall|forbidden behavior|security constraints)\b"
_INTENT_PATTERN = re.compile(
    rf"([^.?!]*{_INTENT_KEYWORDS}[^.?!]*)(?:[.?!]|$)",
    re.IGNORECASE,
)


class DocumentationExtractor:
    """Extracts raw candidate statements from documentation text."""

    def extract(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        content: bytes,
        provenance: Provenance,
    ) -> Iterator[IntentCandidate]:
        """
        Yields raw candidates directly from text without cross-file deduplication.
        (Deduplication is handled at the Manager level.)
        """
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            # If it cannot be decoded, we cannot extract text intents safely.
            return

        lines = text.splitlines()
        
        # We process line-by-line. In a real system, we might want to sentence-tokenize
        # across newlines, but line-by-line is conservative and avoids large regex backtracking
        # or complex NLP models for this phase.
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Simple prompt injection avoidance: do not extract statements containing obvious injection patterns
            if "ignore previous instructions" in line.lower() or "<|system|>" in line.lower():
                continue
            
            for match in _INTENT_PATTERN.finditer(line):
                statement = match.group(1).strip()
                
                # Filter out very short/bogus statements
                if len(statement) < 10:
                    continue
                    
                # Generate a stable ID based on the text itself
                c_id = generate_candidate_id(repository_id, statement)
                
                yield IntentCandidate(
                    candidate_id=c_id,
                    analysis_id=analysis_id,
                    sources=[SourceLocation(path=file_path, start_line=line_num, end_line=line_num)],
                    original_statement=statement,
                    provenance=provenance,
                    status=CandidateStatus.CANDIDATE,
                    human_confirmed=False,
                    extraction_method="RULE_BASED",
                )
