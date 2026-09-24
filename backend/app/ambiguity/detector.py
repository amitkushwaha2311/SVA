"""
SVA Ambiguity Detector
======================

Rule-based static detection of intent ambiguities.
"""

from typing import Iterable

from app.ambiguity.ids import (
    generate_ambiguity_id,
    generate_interpretation_id,
    generate_question_id,
    generate_scenario_id,
)
from app.ambiguity.models import (
    AmbiguityCase,
    AmbiguityType,
    ClarificationQuestion,
    ClarificationStatus,
    DistinguishingScenario,
    Interpretation,
    InterpretationStatus,
    QuestionOption,
)
from app.repository.intent.models import Provenance
from app.semantic_ir.models import SemanticRequirement
from app.semantic_ir.validator import SemanticIRValidationError


class AmbiguityDetector:
    """Detects and constructs ambiguity cases statically without guessing human intent."""

    def __init__(self) -> None:
        from app.ambiguity.validator import AmbiguityValidator
        self.validator = AmbiguityValidator()

    def detect_contradictions(self, repository_id: str, requirements: Iterable[SemanticRequirement]) -> list[AmbiguityCase]:
        """
        Detects explicit contradictions (e.g. from tests passing in competing requirements).
        For Phase 6, this demonstrates how two requirements can form an AmbiguityCase.
        """
        # A simple static contradiction rule for demonstration (as requested by user example):
        # If one says "Users can delete projects." and another says "Only owners can delete projects."
        
        reqs = list(requirements)
        cases = []
        
        # O(N^2) naive scan looking for specific conflicting textual patterns
        for i, r1 in enumerate(reqs):
            for r2 in reqs[i+1:]:
                # Very simple heuristic for Phase 6 static detection
                s1 = r1.statement.lower().strip(".")
                s2 = r2.statement.lower().strip(".")
                
                # Check if they are about the same action but differ in authorization/actor
                if "delete projects" in s1 and "delete projects" in s2:
                    if s1 != s2:
                        case_id = generate_ambiguity_id(repository_id, f"CONTRADICTION:{r1.requirement_id}:{r2.requirement_id}")
                        
                        # Build Interpretation A
                        int_a_id = generate_interpretation_id(case_id, r1.statement)
                        int_a = Interpretation(
                            interpretation_id=int_a_id,
                            requirement_id=r1.requirement_id,
                            statement=r1.statement,
                            provenance=Provenance.AI_INFERENCE,
                            status=InterpretationStatus.PROPOSED
                        )
                        
                        # Build Interpretation B
                        int_b_id = generate_interpretation_id(case_id, r2.statement)
                        int_b = Interpretation(
                            interpretation_id=int_b_id,
                            requirement_id=r2.requirement_id,
                            statement=r2.statement,
                            provenance=Provenance.AI_INFERENCE,
                            status=InterpretationStatus.PROPOSED
                        )
                        
                        # Distinguishing scenario
                        desc = f"Determine which rule governs {s1}"
                        scen_id = generate_scenario_id(case_id, desc)
                        scenario = DistinguishingScenario(
                            scenario_id=scen_id,
                            description=desc,
                            expected_outcomes={
                                int_a_id: "Follow Rule A",
                                int_b_id: "Follow Rule B",
                            }
                        )
                        
                        # Question
                        q_text = f"Which rule is correct for: {s1}?"
                        q_id = generate_question_id(case_id, q_text)
                        question = ClarificationQuestion(
                            question_id=q_id,
                            ambiguity_id=case_id,
                            question=q_text,
                            distinguishing_scenario_id=scen_id,
                            # Information gain is deterministic. 2 options eliminated = score of 2.
                            information_gain=2.0,
                            options=[
                                QuestionOption(option_id=f"{q_id}-1", text=r1.statement, maps_to_interpretation_id=int_a_id),
                                QuestionOption(option_id=f"{q_id}-2", text=r2.statement, maps_to_interpretation_id=int_b_id),
                            ]
                        )
                        
                        case = AmbiguityCase(
                            ambiguity_id=case_id,
                            requirement_ids=[r1.requirement_id, r2.requirement_id],
                            candidate_ids=[r1.candidate_id, r2.candidate_id],
                            statement=f"Contradiction between: '{r1.statement}' and '{r2.statement}'",
                            ambiguity_types=[AmbiguityType.CONTRADICTION, AmbiguityType.AUTHORIZATION],
                            interpretations=[int_a, int_b],
                            distinguishing_scenarios=[scenario],
                            clarification_question=question,
                        )
                        
                        self.validator.validate(case)
                        cases.append(case)
                        
        return cases

    def detect_ambiguity(self, repository_id: str, requirement: SemanticRequirement) -> AmbiguityCase | None:
        """
        Statically detects single-requirement ambiguities without inventing unsupported rules.
        """
        statement = requirement.statement.lower()
        
        # 1. Ambiguous Authorization ("can")
        if "can delete" in statement or "can access" in statement:
            # We don't invent "Account ending in 7". We use grounded actor distinctions.
            case_id = generate_ambiguity_id(repository_id, requirement.statement)
            
            int_a_id = generate_interpretation_id(case_id, "Any authenticated user can perform the action.")
            int_b_id = generate_interpretation_id(case_id, "Only resource owners can perform the action.")
            
            int_a = Interpretation(
                interpretation_id=int_a_id,
                requirement_id=requirement.requirement_id,
                statement="Any authenticated user can perform the action.",
                provenance=Provenance.AI_INFERENCE,
            )
            int_b = Interpretation(
                interpretation_id=int_b_id,
                requirement_id=requirement.requirement_id,
                statement="Only resource owners can perform the action.",
                provenance=Provenance.AI_INFERENCE,
            )
            
            scen_id = generate_scenario_id(case_id, "Authenticated non-owner attempts the action.")
            scenario = DistinguishingScenario(
                scenario_id=scen_id,
                description="Authenticated non-owner attempts the action.",
                expected_outcomes={
                    int_a_id: "ALLOW",
                    int_b_id: "DENY",
                }
            )
            
            q_text = "Should an authenticated non-owner be allowed to perform the action?"
            q_id = generate_question_id(case_id, q_text)
            question = ClarificationQuestion(
                question_id=q_id,
                ambiguity_id=case_id,
                question=q_text,
                distinguishing_scenario_id=scen_id,
                information_gain=2.0,
                options=[
                    QuestionOption(option_id=f"{q_id}-1", text="Yes", maps_to_interpretation_id=int_a_id),
                    QuestionOption(option_id=f"{q_id}-2", text="No", maps_to_interpretation_id=int_b_id),
                ]
            )
            
            case = AmbiguityCase(
                ambiguity_id=case_id,
                requirement_ids=[requirement.requirement_id],
                candidate_ids=[requirement.candidate_id],
                statement=requirement.statement,
                ambiguity_types=[AmbiguityType.AUTHORIZATION, AmbiguityType.ACTOR],
                interpretations=[int_a, int_b],
                distinguishing_scenarios=[scenario],
                clarification_question=question,
            )
            self.validator.validate(case)
            return case
            
        # 2. Ambiguous Scope ("should receive")
        if "should receive notifications" in statement:
            case_id = generate_ambiguity_id(repository_id, requirement.statement)
            
            int_a_id = generate_interpretation_id(case_id, "All users receive notifications.")
            int_b_id = generate_interpretation_id(case_id, "Only opted-in users receive notifications.")
            
            int_a = Interpretation(
                interpretation_id=int_a_id,
                requirement_id=requirement.requirement_id,
                statement="All users receive notifications.",
                provenance=Provenance.AI_INFERENCE,
            )
            int_b = Interpretation(
                interpretation_id=int_b_id,
                requirement_id=requirement.requirement_id,
                statement="Only opted-in users receive notifications.",
                provenance=Provenance.AI_INFERENCE,
            )
            
            scen_id = generate_scenario_id(case_id, "System generates an event for a user who has not explicitly opted in.")
            scenario = DistinguishingScenario(
                scenario_id=scen_id,
                description="System generates an event for a user who has not explicitly opted in.",
                expected_outcomes={
                    int_a_id: "Notification sent",
                    int_b_id: "Notification not sent",
                }
            )
            
            q_text = "Should a user receive notifications if they have not explicitly opted in?"
            q_id = generate_question_id(case_id, q_text)
            question = ClarificationQuestion(
                question_id=q_id,
                ambiguity_id=case_id,
                question=q_text,
                distinguishing_scenario_id=scen_id,
                information_gain=2.0,
                options=[
                    QuestionOption(option_id=f"{q_id}-1", text="Yes", maps_to_interpretation_id=int_a_id),
                    QuestionOption(option_id=f"{q_id}-2", text="No", maps_to_interpretation_id=int_b_id),
                ]
            )
            
            case = AmbiguityCase(
                ambiguity_id=case_id,
                requirement_ids=[requirement.requirement_id],
                candidate_ids=[requirement.candidate_id],
                statement=requirement.statement,
                ambiguity_types=[AmbiguityType.SCOPE],
                interpretations=[int_a, int_b],
                distinguishing_scenarios=[scenario],
                clarification_question=question,
            )
            self.validator.validate(case)
            return case
            
        return None
