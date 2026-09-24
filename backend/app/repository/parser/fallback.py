"""
SVA Regex Fallback Parser
=========================

Conservative fallback parser for unsupported languages.
Uses regex to detect basic structural elements like functions and classes.
Does not make confident semantic claims.
"""

import re
from typing import Sequence

from app.repository.parser.base import LanguageParser
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id


class RegexParser(LanguageParser):
    """Fallback regex parser for unsupported languages."""

    @property
    def supported_languages(self) -> frozenset[str]:
        # Represents all languages not explicitly supported
        return frozenset({"*"})

    def parse(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        content: bytes,
    ) -> Sequence[CodeEntity]:
        
        entities: list[CodeEntity] = []
        
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            # If it's not valid utf-8, we can't reliably regex it
            return [
                CodeEntity(
                    entity_id=generate_entity_id(repository_id, file_path, EntityType.MODULE, "parse_error", 0),
                    repository_id=repository_id,
                    analysis_id=analysis_id,
                    file_path=file_path,
                    entity_type=EntityType.MODULE,
                    name="parse_error",
                    start_line=0,
                    end_line=0,
                    language=language,
                    extraction_method="REGEX",
                    extraction_status="PARSE_ERROR"
                )
            ]

        lines = text.splitlines()

        # Very conservative heuristics:
        # Looking for `func name(` or `function name(` or `class name`
        func_pattern = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+)*(?:func|function|def)\s+([a-zA-Z_]\w*)")
        class_pattern = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|abstract\s+)*class\s+([a-zA-Z_]\w*)")

        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Check function
            f_match = func_pattern.search(line)
            if f_match:
                name = f_match.group(1)
                e_type = EntityType.FUNCTION
                if name.startswith("test") or name.startswith("Test"):
                    e_type = EntityType.TEST
                    
                e_id = generate_entity_id(repository_id, file_path, e_type, name, line_num)
                entities.append(
                    CodeEntity(
                        entity_id=e_id,
                        repository_id=repository_id,
                        analysis_id=analysis_id,
                        file_path=file_path,
                        entity_type=e_type,
                        name=name,
                        start_line=line_num,
                        end_line=line_num, # Regex fallback doesn't know end line
                        language=language,
                        extraction_method="REGEX"
                    )
                )
                continue

            # Check class
            c_match = class_pattern.search(line)
            if c_match:
                name = c_match.group(1)
                e_type = EntityType.CLASS
                if name.startswith("Test"):
                    e_type = EntityType.TEST
                    
                e_id = generate_entity_id(repository_id, file_path, e_type, name, line_num)
                entities.append(
                    CodeEntity(
                        entity_id=e_id,
                        repository_id=repository_id,
                        analysis_id=analysis_id,
                        file_path=file_path,
                        entity_type=e_type,
                        name=name,
                        start_line=line_num,
                        end_line=line_num,
                        language=language,
                        extraction_method="REGEX"
                    )
                )

        return entities
