from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        json_schema_extra={
            "example": "Which are the top 5 artists by number of tracks?"
        },
    )
    max_rows: int = Field(default=50, ge=1, le=100)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question cannot be blank")
        return value.strip()


class AskResponse(BaseModel):
    type: Literal["query", "ambiguous", "unsupported"]
    message: str
    sql: str | None
    data: list[dict[str, Any]] | None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "query",
                    "message": "Query executed successfully.",
                    "sql": "SELECT artist.name AS artist_name, COUNT(track.track_id) AS track_count FROM artist JOIN album ON album.artist_id = artist.artist_id JOIN track ON track.album_id = album.album_id GROUP BY artist.name ORDER BY track_count DESC LIMIT 50",
                    "data": [{"artist_name": "Iron Maiden", "track_count": 213}],
                },
                {
                    "type": "ambiguous",
                    "message": "The question is ambiguous. Please submit a new complete question clarifying whether 'best customers' means highest total spending, most invoices, or highest average invoice value.",
                    "sql": None,
                    "data": None,
                },
                {
                    "type": "unsupported",
                    "message": "This question cannot be answered from the Chinook database schema.",
                    "sql": None,
                    "data": None,
                },
            ]
        }
    }
