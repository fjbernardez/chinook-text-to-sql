from typing import Protocol, runtime_checkable

from app.schemas.llm import LlmDecision


@runtime_checkable
class SqlDecisionProvider(Protocol):
    def generate_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
    ) -> LlmDecision:
        """Return a structured decision for a natural language question."""

    def repair_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
        invalid_sql: str,
        validator_error: str,
    ) -> LlmDecision:
        """Return one semantic correction attempt after validator rejection."""
