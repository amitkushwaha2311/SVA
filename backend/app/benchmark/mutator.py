"""
SVA-Bench Mutation Framework
=============================

Declarative, deterministic mutations applied to fixture text.

SECURITY BOUNDARY:
    Mutations operate on abstract fixture text/content only.
    They NEVER execute repository code, invoke shells, or install
    dependencies from benchmark fixtures.

DETERMINISM:
    All mutations produce the same output for the same input.
    No randomness. No external calls.
"""

from __future__ import annotations

from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseDifficulty,
    EvidenceSufficiency,
    FileFixture,
    GroundTruth,
    MutationDefinition,
    MutationType,
    RepositoryFixture,
)
from app.evidence.models import VerificationState
from app.drift.models import SemanticCIDecision


# ---------------------------------------------------------------------------
# Text-level mutation helpers (operate on strings, never on execution)
# ---------------------------------------------------------------------------

def apply_text_mutation(
    original_content: str,
    mutation_type: MutationType,
    target_pattern: str,
    replacement: str,
) -> tuple[str, bool]:
    """
    Apply a declarative text mutation.
    Returns (mutated_content, was_applied).

    SECURITY: No subprocess, no exec, no eval. Pure string manipulation.
    """
    if target_pattern not in original_content:
        return original_content, False
    mutated = original_content.replace(target_pattern, replacement, 1)
    return mutated, True


# ---------------------------------------------------------------------------
# Mutation application to a repository fixture
# ---------------------------------------------------------------------------

def apply_mutation_to_fixture(
    fixture: RepositoryFixture,
    mutation_type: MutationType,
    target_file_path: str,
    target_pattern: str,
    replacement: str,
) -> RepositoryFixture:
    """
    Produce a new RepositoryFixture by applying a declarative text mutation to one file.

    The original fixture is not mutated. Returns a new fixture.
    """
    new_files = []
    applied = False
    for file in fixture.files:
        if file.relative_path == target_file_path:
            new_content, was_applied = apply_text_mutation(
                file.content, mutation_type, target_pattern, replacement
            )
            applied = was_applied
            new_files.append(FileFixture(
                relative_path=file.relative_path,
                content=new_content,
                description=file.description + f" [MUTATED: {mutation_type.value}]",
            ))
        else:
            new_files.append(file)

    if not applied:
        raise ValueError(
            f"Mutation {mutation_type.value} could not be applied: "
            f"pattern not found in {target_file_path}."
        )

    return RepositoryFixture(
        fixture_id=fixture.fixture_id + f"_mut_{mutation_type.value.lower()}",
        description=fixture.description + f" [MUTATED: {mutation_type.value}]",
        files=new_files,
        commit_ref=fixture.commit_ref + "_mut",
        version=str(int(fixture.version) + 1) if fixture.version.isdigit() else "2",
    )


# ---------------------------------------------------------------------------
# Mutation derivation: creates a new BenchmarkCase from a parent
# ---------------------------------------------------------------------------

def derive_mutated_case(
    parent_case: BenchmarkCase,
    mutation_def: MutationDefinition,
    target_file_path: str,
    target_pattern: str,
    replacement: str,
) -> BenchmarkCase:
    """
    Derive a child BenchmarkCase by applying a MutationDefinition to a parent case.

    The new case inherits the parent's structure but has:
    - A mutated fixture
    - A new independent ground truth defined in the MutationDefinition
    - A new case_id referencing the mutation

    SECURITY: No execution. Pure string mutation on fixture content.
    """
    mutated_fixture = apply_mutation_to_fixture(
        fixture=parent_case.repository_fixture,
        mutation_type=mutation_def.mutation_type,
        target_file_path=target_file_path,
        target_pattern=target_pattern,
        replacement=replacement,
    )

    return BenchmarkCase(
        case_id=f"{parent_case.case_id}__mut_{mutation_def.mutation_id}",
        version="1",
        category=parent_case.category,
        difficulty=parent_case.difficulty,
        requirement_text=parent_case.requirement_text,
        requirement_sources=list(parent_case.requirement_sources),
        repository_fixture=mutated_fixture,
        ground_truth=mutation_def.ground_truth_result,
        mutations=[mutation_def],
        notes=(
            f"Derived from '{parent_case.case_id}' by mutation "
            f"'{mutation_def.mutation_type.value}': {mutation_def.description}"
        ),
        metadata={
            "parent_case_id": parent_case.case_id,
            "mutation_id": mutation_def.mutation_id,
            "mutation_type": mutation_def.mutation_type.value,
        },
    )
