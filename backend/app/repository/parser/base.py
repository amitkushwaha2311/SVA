"""
SVA Base Parser Abstraction
===========================

Defines the abstract interface for all language-specific parsers.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from app.repository.parser.models import CodeEntity


class LanguageParser(ABC):
    """
    Abstract base class for extracting CodeEntities from source files.
    """

    @property
    @abstractmethod
    def supported_languages(self) -> frozenset[str]:
        """Languages this parser can handle (e.g. {'Python'})."""
        pass

    @abstractmethod
    def parse(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        content: bytes,
    ) -> Sequence[CodeEntity]:
        """
        Parse source content into a sequence of structural entities.

        Parameters
        ----------
        repository_id:
            Stable identifier for the repository.
        analysis_id:
            Identifier for this analysis run.
        file_path:
            Relative path to the file.
        language:
            The language detected by the LanguageDetector.
        content:
            The raw bytes of the file.

        Returns
        -------
        Sequence[CodeEntity]
            A list of successfully extracted entities.
        """
        pass
