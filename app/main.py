import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.v1.ask_router import router as ask_router
from app.database import connect
from app.exceptions.api_exceptions import (
    LlmGenerationError,
    SqlExecutionError,
    UnsafeSqlError,
)

app = FastAPI(title="chinook-text-to-sql")
app.include_router(ask_router)


@app.exception_handler(LlmGenerationError)
def handle_llm_generation_error(
    request: Request,
    exc: LlmGenerationError,
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(UnsafeSqlError)
def handle_unsafe_sql_error(request: Request, exc: UnsafeSqlError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(SqlExecutionError)
def handle_sql_execution_error(
    request: Request,
    exc: SqlExecutionError,
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-health")
def db_health() -> dict[str, str]:
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except (psycopg.Error, ValidationError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connectivity check failed. Verify DB_* environment variables and network access.",
        ) from exc

    return {"database": "ok"}


@app.get("/artists/count")
def artists_count() -> dict[str, int]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS artists FROM artist")
            result = cursor.fetchone()

    return {"artists": result["artists"]}


@app.get("/artists/top-by-albums")
def top_artists_by_albums() -> list[dict[str, int | str]]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    artist.name,
                    COUNT(*) AS albums
                FROM artist
                JOIN album ON album.artist_id = artist.artist_id
                GROUP BY artist.name
                ORDER BY albums DESC
                LIMIT 10;
                """
            )
            return list(cursor.fetchall())
