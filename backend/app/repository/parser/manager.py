"""
SVA Parser Manager
==================

Routes files to the correct language parser and provides error isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from app.core.logging_config import get_logger
from app.repository.parser.base import LanguageParser
from app.repository.parser.fallback import RegexParser
from app.repository.parser.javascript import JavaScriptParser
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id
from app.repository.parser.python import PythonParser
from app.repository.types import FileClassification, FileRecord

logger = get_logger("repository.parser.manager")


@dataclass
class FileParseResult:
    """Result of parsing a single file."""

    file_path: str
    language: str
    entities: list[CodeEntity] = field(default_factory=list)
    parse_error: str | None = None
    extraction_method: str = "UNKNOWN"


@dataclass
class ParseResult:
    """Aggregated result of parsing an entire repository."""

    repository_id: str
    analysis_id: str
    file_results: list[FileParseResult] = field(default_factory=list)
    total_entities: int = 0
    total_parse_errors: int = 0

    @property
    def all_entities(self) -> list[CodeEntity]:
        entities = []
        for fr in self.file_results:
            entities.extend(fr.entities)
        return entities


class ParserManager:
    """
    Routes source files to appropriate parsers and isolates errors.

    Security: All content must already have been read through PathGuard.
    This class never accesses the filesystem directly.
    """

    def __init__(self) -> None:
        self._parsers: list[LanguageParser] = [
            PythonParser(),
            JavaScriptParser(),
        ]
        self._fallback = RegexParser()

    def _get_parser(self, language: str) -> LanguageParser:
        for parser in self._parsers:
            if language in parser.supported_languages:
                return parser
        return self._fallback

    def parse_file(
        self,
        repository_id: str,
        analysis_id: str,
        file_record: FileRecord,
        content: bytes,
    ) -> FileParseResult:
        """
        Parse a single file with error isolation.

        A parser crash here results in a PARSE_ERROR record, not an exception.
        """
        language = file_record.language or "Unknown"
        file_path = file_record.relative_path

        parser = self._get_parser(language)
        method = "TREE_SITTER" if parser is not self._fallback else "REGEX"

        try:
            entities = list(parser.parse(
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                language=language,
                content=content,
            ))

            # Check if the parser itself returned a PARSE_ERROR record
            if len(entities) == 1 and entities[0].extraction_status == "PARSE_ERROR":
                return FileParseResult(
                    file_path=file_path,
                    language=language,
                    parse_error=f"Parser returned PARSE_ERROR for {file_path}",
                    extraction_method=method,
                )

            return FileParseResult(
                file_path=file_path,
                language=language,
                entities=entities,
                extraction_method=method,
            )

        except Exception as exc:
            logger.warning(
                "Parser failed on %s (%s): %s", file_path, language, exc
            )
            return FileParseResult(
                file_path=file_path,
                language=language,
                parse_error=f"EXCEPTION: {exc}",
                extraction_method=method,
            )

    def parse_repository(
        self,
        repository_id: str,
        analysis_id: str,
        file_records: list[FileRecord],
        content_map: dict[str, bytes],
    ) -> ParseResult:
        """
        Parse all parseable source files in a repository with per-file error isolation.

        Parameters
        ----------
        repository_id:
            Stable identifier for the repository.
        analysis_id:
            Identifier for this analysis run.
        file_records:
            All FileRecords from the scan.
        content_map:
            Mapping from relative_path → raw content bytes.
            Must be pre-loaded (no filesystem access here).
        """
        result = ParseResult(repository_id=repository_id, analysis_id=analysis_id)

        # Only attempt to parse source code, test, and certain other code files
        parseable_classifications = {
            FileClassification.SOURCE_CODE,
            FileClassification.TEST,
            FileClassification.DATABASE_SCHEMA,
        }

        for record in file_records:
            if record.is_binary or record.read_error:
                continue

            if record.classification not in parseable_classifications:
                continue

            content = content_map.get(record.relative_path)
            if content is None:
                continue

            file_result = self.parse_file(
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_record=record,
                content=content,
            )
            result.file_results.append(file_result)

            if file_result.parse_error:
                result.total_parse_errors += 1
            else:
                result.total_entities += len(file_result.entities)

        logger.info(
            "Parsing complete: %d files, %d entities, %d parse errors",
            len(result.file_results),
            result.total_entities,
            result.total_parse_errors,
        )
        return result
