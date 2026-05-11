import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.api.exception_handlers import register_exception_handlers
from app.api.v1.ask_router import router as ask_router
from app.database import connect

app = FastAPI(title="chinook-text-to-sql")
app.include_router(ask_router)
register_exception_handlers(app)


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
