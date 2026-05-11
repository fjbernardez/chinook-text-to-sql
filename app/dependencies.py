from functools import lru_cache

from app.services.ask_service import AskService
from app.services.openai_sql_generator import OpenAiSqlDecisionProvider
from app.services.sql_executor import SqlExecutor
from app.services.sql_validator import SqlValidator


@lru_cache
def build_ask_service() -> AskService:
    # OpenAI-specific wiring belongs here so AskService stays provider-agnostic.
    # The service is cached to reuse the OpenAI client and stateless collaborators.
    return AskService(
        llm_provider=OpenAiSqlDecisionProvider(),
        validator=SqlValidator(),
        executor=SqlExecutor(),
    )
