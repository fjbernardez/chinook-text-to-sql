import logging

from app.exceptions.api_exceptions import LlmGenerationError, UnsafeSqlError
from app.schemas.ask import AskResponse
from app.services.openai_sql_generator import OpenAISqlGenerator
from app.services.sql_executor import SqlExecutor
from app.services.sql_validator import SqlValidator

logger = logging.getLogger(__name__)


class AskService:
    def __init__(
        self,
        generator: OpenAISqlGenerator | None = None,
        validator: SqlValidator | None = None,
        executor: SqlExecutor | None = None,
    ) -> None:
        self.generator = generator or OpenAISqlGenerator()
        self.validator = validator or SqlValidator()
        self.executor = executor or SqlExecutor()

    def ask(self, question: str, max_rows: int) -> AskResponse:
        logger.info("Ask request received")

        decision = self.generator.generate_decision(question, max_rows)
        logger.info("OpenAI decision type", extra={"decision_type": decision.type})

        if decision.type in {"ambiguous", "unsupported"}:
            return AskResponse(
                type=decision.type,
                message=decision.message,
                sql=None,
                data=None,
            )

        validation_result = self._validate_or_repair(question, max_rows, decision.sql)
        if isinstance(validation_result, AskResponse):
            return validation_result

        safe_sql = validation_result
        logger.info("SQL validation succeeded", extra={"sql": safe_sql})

        data = self.executor.execute(safe_sql, max_rows)
        return AskResponse(
            type="query",
            message="Query executed successfully.",
            sql=safe_sql,
            data=data,
        )

    def _validate_or_repair(
        self,
        question: str,
        max_rows: int,
        sql: str | None,
    ) -> str | AskResponse:
        try:
            return self.validator.validate(sql or "", max_rows)
        except UnsafeSqlError as first_error:
            logger.warning(
                "SQL validation failed; requesting one repair attempt",
                extra={"error": str(first_error)},
            )

            repair = self.generator.repair_decision(
                question=question,
                max_rows=max_rows,
                invalid_sql=sql or "",
                validator_error=str(first_error),
            )
            logger.info("OpenAI repair decision type", extra={"decision_type": repair.type})

            if repair.type in {"ambiguous", "unsupported"}:
                return AskResponse(
                    type=repair.type,
                    message=repair.message,
                    sql=None,
                    data=None,
                )

            try:
                return self.validator.validate(repair.sql or "", max_rows)
            except UnsafeSqlError as repair_error:
                logger.warning(
                    "SQL repair validation failed",
                    extra={"error": str(repair_error)},
                )
                raise repair_error from first_error
        except LlmGenerationError:
            raise
