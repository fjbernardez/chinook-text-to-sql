import pytest

from app.exceptions.api_exceptions import UnsafeSqlError
from app.services.sql_validator import SqlValidator


@pytest.fixture
def validator() -> SqlValidator:
    return SqlValidator()


def test_accepts_simple_select(validator: SqlValidator) -> None:
    sql = validator.validate("SELECT name FROM artist LIMIT 10", max_rows=50)

    assert sql == "SELECT name FROM artist LIMIT 10"


def test_accepts_select_with_join(validator: SqlValidator) -> None:
    sql = validator.validate(
        """
        SELECT artist.name, COUNT(track.track_id) AS track_count
        FROM artist
        JOIN album ON album.artist_id = artist.artist_id
        JOIN track ON track.album_id = album.album_id
        GROUP BY artist.name
        LIMIT 5
        """,
        max_rows=50,
    )

    assert "JOIN album" in sql
    assert "JOIN track" in sql


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO artist (name) VALUES ('x')",
        "UPDATE artist SET name = 'x'",
        "DELETE FROM artist",
        "DROP TABLE artist",
        "CREATE TABLE x (id int)",
    ],
)
def test_rejects_mutating_or_ddl_sql(validator: SqlValidator, sql: str) -> None:
    with pytest.raises(UnsafeSqlError):
        validator.validate(sql, max_rows=50)


def test_rejects_multiple_statements(validator: SqlValidator) -> None:
    with pytest.raises(UnsafeSqlError):
        validator.validate("SELECT * FROM artist; SELECT * FROM album", max_rows=50)


@pytest.mark.parametrize(
    "sql",
    [
        "-- comment\nSELECT * FROM artist",
        "SELECT * FROM artist /* comment */",
    ],
)
def test_rejects_comments(validator: SqlValidator, sql: str) -> None:
    with pytest.raises(UnsafeSqlError):
        validator.validate(sql, max_rows=50)


def test_rejects_unknown_table(validator: SqlValidator) -> None:
    with pytest.raises(UnsafeSqlError):
        validator.validate("SELECT * FROM payment LIMIT 10", max_rows=50)


def test_adds_limit_when_missing(validator: SqlValidator) -> None:
    sql = validator.validate("SELECT name FROM artist", max_rows=25)

    assert sql == "SELECT name FROM artist LIMIT 25"


def test_caps_limit_above_max_rows(validator: SqlValidator) -> None:
    sql = validator.validate("SELECT name FROM artist LIMIT 500", max_rows=50)

    assert sql == "SELECT name FROM artist LIMIT 50"


def test_accepts_valid_aggregate_queries(validator: SqlValidator) -> None:
    sql = validator.validate("SELECT COUNT(*) AS artists FROM artist", max_rows=50)

    assert sql == "SELECT COUNT(*) AS artists FROM artist LIMIT 50"


def test_rejects_non_chinook_tables(validator: SqlValidator) -> None:
    with pytest.raises(UnsafeSqlError):
        validator.validate("SELECT * FROM users", max_rows=50)
