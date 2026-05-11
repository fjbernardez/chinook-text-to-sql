from app.dependencies import build_ask_service
from app.services.ask_service import AskService
from app.services.openai_sql_generator import OpenAiSqlDecisionProvider
from app.services.sql_executor import SqlExecutor
from app.services.sql_validator import SqlValidator


def test_build_ask_service_wires_production_dependencies(monkeypatch) -> None:
    build_ask_service.cache_clear()

    class FakeOpenAiSqlDecisionProvider:
        pass

    monkeypatch.setattr(
        "app.dependencies.OpenAiSqlDecisionProvider",
        FakeOpenAiSqlDecisionProvider,
    )

    service = build_ask_service()

    assert isinstance(service, AskService)
    assert isinstance(service.llm_provider, FakeOpenAiSqlDecisionProvider)
    assert isinstance(service.validator, SqlValidator)
    assert isinstance(service.executor, SqlExecutor)

    build_ask_service.cache_clear()


def test_build_ask_service_is_cached(monkeypatch) -> None:
    build_ask_service.cache_clear()

    class FakeOpenAiSqlDecisionProvider:
        pass

    monkeypatch.setattr(
        "app.dependencies.OpenAiSqlDecisionProvider",
        FakeOpenAiSqlDecisionProvider,
    )

    first = build_ask_service()
    second = build_ask_service()

    assert first is second

    build_ask_service.cache_clear()


def test_dependency_module_owns_openai_provider_import() -> None:
    assert OpenAiSqlDecisionProvider is not None
