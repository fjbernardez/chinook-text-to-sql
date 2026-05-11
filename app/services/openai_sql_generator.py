import logging

from openai import APIConnectionError, APITimeoutError, OpenAI, OpenAIError
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.exceptions.api_exceptions import LlmGenerationError
from app.prompts.sql_generation_prompt import (
    SQL_GENERATION_SYSTEM_PROMPT,
    build_generation_input,
    build_repair_input,
)
from app.schemas.llm import LlmDecision
from app.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAiSqlDecisionProvider:
    def __init__(
        self,
        client: OpenAI | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        if client is not None:
            self.model = model or "gpt-4o-mini"
            self.timeout_seconds = timeout_seconds or 30
            self.client = client
            return

        settings = get_settings()
        if not settings.openai_api_key:
            raise LlmGenerationError("OPENAI_API_KEY is not configured.")

        self.model = model or settings.openai_model
        self.timeout_seconds = timeout_seconds or settings.openai_timeout_seconds
        self.client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=self.timeout_seconds,
        )

    def generate_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
    ) -> LlmDecision:
        prompt_input = build_generation_input(
            schema_context=schema_context,
            question=question,
            max_rows=max_rows,
        )
        return self._request_decision(prompt_input)

    def repair_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
        invalid_sql: str,
        validator_error: str,
    ) -> LlmDecision:
        prompt_input = build_repair_input(
            schema_context=schema_context,
            question=question,
            max_rows=max_rows,
            invalid_sql=invalid_sql,
            validator_error=validator_error,
        )
        return self._request_decision(prompt_input)

    @retry(
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        reraise=True,
    )
    def _request_openai(self, prompt_input: str):
        return self.client.responses.parse(
            model=self.model,
            instructions=SQL_GENERATION_SYSTEM_PROMPT,
            input=prompt_input,
            text_format=LlmDecision,
            temperature=0,
        )

    def _request_decision(self, prompt_input: str) -> LlmDecision:
        try:
            response = self._request_openai(prompt_input)
            decision = response.output_parsed
        except (APIConnectionError, APITimeoutError, OpenAIError) as exc:
            logger.warning("OpenAI request failed", extra={"error_type": type(exc).__name__})
            raise LlmGenerationError("OpenAI is unavailable or timed out.") from exc
        except ValidationError as exc:
            raise LlmGenerationError("OpenAI returned an invalid structured decision.") from exc

        if decision is None:
            raise LlmGenerationError("OpenAI returned an empty structured decision.")

        logger.info("OpenAI decision received", extra={"decision_type": decision.type})
        return decision
