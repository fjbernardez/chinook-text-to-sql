from app.schemas.llm import LlmDecision
from app.services.llm_provider import SqlDecisionProvider
from app.services.openai_sql_generator import OpenAiSqlDecisionProvider


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs

        class Response:
            output_parsed = LlmDecision(
                type="query",
                sql="SELECT name FROM artist LIMIT 5",
                message="ok",
                confidence=0.9,
            )

        return Response()


class FakeOpenAiClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class FakeProvider:
    def generate_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
    ) -> LlmDecision:
        return LlmDecision(type="unsupported", sql=None, message="no", confidence=0.1)

    def repair_decision(
        self,
        question: str,
        max_rows: int,
        schema_context: str,
        invalid_sql: str,
        validator_error: str,
    ) -> LlmDecision:
        return LlmDecision(type="unsupported", sql=None, message="no", confidence=0.1)


def test_sql_decision_provider_protocol_accepts_matching_provider() -> None:
    assert isinstance(FakeProvider(), SqlDecisionProvider)


def test_openai_provider_requests_structured_decision() -> None:
    client = FakeOpenAiClient()
    provider = OpenAiSqlDecisionProvider(client=client)

    decision = provider.generate_decision(
        question="artists",
        max_rows=5,
        schema_context="artist table schema",
    )

    assert decision.type == "query"
    assert client.responses.kwargs["text_format"] is LlmDecision
    assert client.responses.kwargs["temperature"] == 0
    assert "artist table schema" in client.responses.kwargs["input"]
