import pytest

from app.exceptions.api_exceptions import LlmGenerationError, UnsafeSqlError
from app.schemas.llm import LlmDecision
from app.services.ask_service import AskService
from app.services.llm_provider import SqlDecisionProvider


class FakeGenerator:
    def __init__(self, decisions: list[LlmDecision] | None = None, error: Exception | None = None):
        self.decisions = decisions or []
        self.error = error
        self.generate_calls = 0
        self.repair_calls = 0

    def generate_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
    ) -> LlmDecision:
        self.generate_calls += 1
        if self.error:
            raise self.error
        return self.decisions.pop(0)

    def repair_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
        invalid_sql: str,
        validator_error: str,
    ) -> LlmDecision:
        self.repair_calls += 1
        return self.decisions.pop(0)


class FakeValidator:
    def __init__(self, results: list[str | Exception]):
        self.results = results
        self.calls = 0

    def validate(self, sql: str, max_rows: int) -> str:
        self.calls += 1
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeExecutor:
    def __init__(self) -> None:
        self.calls = 0
        self.sql = None

    def execute(self, sql: str, max_rows: int) -> list[dict[str, int | str]]:
        self.calls += 1
        self.sql = sql
        return [{"artist_name": "Iron Maiden", "track_count": 213}]


def test_ambiguous_response_returns_without_executing_sql() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="ambiguous",
                sql=None,
                message="Please submit a new complete question.",
                confidence=0.8,
            )
        ]
    )
    validator = FakeValidator([])
    executor = FakeExecutor()

    response = AskService(generator, validator, executor).ask("best customers", 50)

    assert response.type == "ambiguous"
    assert response.sql is None
    assert response.data is None
    assert validator.calls == 0
    assert executor.calls == 0


def test_ask_service_accepts_fake_sql_decision_provider() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="ambiguous",
                sql=None,
                message="Please submit a new complete question.",
                confidence=0.8,
            )
        ]
    )

    assert isinstance(generator, SqlDecisionProvider)


def test_unsupported_response_returns_without_executing_sql() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="unsupported",
                sql=None,
                message="This cannot be answered from Chinook.",
                confidence=0.9,
            )
        ]
    )
    validator = FakeValidator([])
    executor = FakeExecutor()

    response = AskService(generator, validator, executor).ask("Bitcoin prices", 50)

    assert response.type == "unsupported"
    assert validator.calls == 0
    assert executor.calls == 0


def test_valid_query_validates_and_executes() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="query",
                sql="SELECT name FROM artist",
                message="ok",
                confidence=0.9,
            )
        ]
    )
    validator = FakeValidator(["SELECT name FROM artist LIMIT 50"])
    executor = FakeExecutor()

    response = AskService(generator, validator, executor).ask("artists", 50)

    assert response.type == "query"
    assert response.sql == "SELECT name FROM artist LIMIT 50"
    assert response.data == [{"artist_name": "Iron Maiden", "track_count": 213}]
    assert executor.calls == 1


def test_invalid_generated_sql_triggers_exactly_one_repair_attempt() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="query",
                sql="DELETE FROM artist",
                message="ok",
                confidence=0.9,
            ),
            LlmDecision(
                type="query",
                sql="SELECT name FROM artist",
                message="repaired",
                confidence=0.9,
            ),
        ]
    )
    validator = FakeValidator(
        [
            UnsafeSqlError("Only SELECT queries are allowed."),
            "SELECT name FROM artist LIMIT 50",
        ]
    )
    executor = FakeExecutor()

    response = AskService(generator, validator, executor).ask("artists", 50)

    assert response.type == "query"
    assert generator.repair_calls == 1
    assert validator.calls == 2
    assert executor.calls == 1


def test_invalid_sql_after_repair_raises_safe_422_error() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="query",
                sql="DELETE FROM artist",
                message="ok",
                confidence=0.9,
            ),
            LlmDecision(
                type="query",
                sql="DROP TABLE artist",
                message="bad repair",
                confidence=0.9,
            ),
        ]
    )
    validator = FakeValidator(
        [
            UnsafeSqlError("Only SELECT queries are allowed."),
            UnsafeSqlError("Only SELECT queries are allowed."),
        ]
    )
    executor = FakeExecutor()

    with pytest.raises(UnsafeSqlError):
        AskService(generator, validator, executor).ask("artists", 50)

    assert generator.repair_calls == 1
    assert executor.calls == 0


def test_repair_can_return_ambiguous_without_executing_sql() -> None:
    generator = FakeGenerator(
        [
            LlmDecision(
                type="query",
                sql="SELECT * FROM artist",
                message="ok",
                confidence=0.9,
            ),
            LlmDecision(
                type="ambiguous",
                sql=None,
                message="Please submit a new complete question clarifying the metric.",
                confidence=0.8,
            ),
        ]
    )
    validator = FakeValidator([UnsafeSqlError("Generated SQL is ambiguous.")])
    executor = FakeExecutor()

    response = AskService(generator, validator, executor).ask("top artists", 50)

    assert response.type == "ambiguous"
    assert response.sql is None
    assert response.data is None
    assert generator.repair_calls == 1
    assert executor.calls == 0


def test_openai_error_maps_to_service_level_error() -> None:
    generator = FakeGenerator(error=LlmGenerationError("OpenAI is unavailable."))
    service = AskService(generator, FakeValidator([]), FakeExecutor())

    with pytest.raises(LlmGenerationError):
        service.ask("artists", 50)
