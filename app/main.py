import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.database import connect

app = FastAPI(title="chinook-text-to-sql")


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
