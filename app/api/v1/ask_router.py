from fastapi import APIRouter, Depends

from app.schemas.ask import AskRequest, AskResponse
from app.services.ask_service import AskService

router = APIRouter(prefix="/api/v1", tags=["ask"])


def get_ask_service() -> AskService:
    return AskService()


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a natural language question about Chinook data",
    description=(
        "Receives a natural language analytics question, asks OpenAI for a "
        "structured SQL decision, validates any generated SQL as read-only "
        "PostgreSQL over the Chinook allowlist, and returns query data or a "
        "domain outcome."
    ),
    responses={
        200: {
            "description": "Domain outcome: query, ambiguous, or unsupported.",
            "content": {
                "application/json": {
                    "examples": {
                        "query": {
                            "summary": "Successful SQL execution",
                            "value": {
                                "type": "query",
                                "message": "Query executed successfully.",
                                "sql": "SELECT artist.name AS artist_name, COUNT(track.track_id) AS track_count FROM artist JOIN album ON album.artist_id = artist.artist_id JOIN track ON track.album_id = album.album_id GROUP BY artist.name ORDER BY track_count DESC LIMIT 50",
                                "data": [
                                    {
                                        "artist_name": "Iron Maiden",
                                        "track_count": 213,
                                    }
                                ],
                            },
                        },
                        "ambiguous": {
                            "summary": "Ambiguous question",
                            "value": {
                                "type": "ambiguous",
                                "message": "The question is ambiguous. Please submit a new complete question clarifying whether 'best customers' means highest total spending, most invoices, or highest average invoice value.",
                                "sql": None,
                                "data": None,
                            },
                        },
                        "unsupported": {
                            "summary": "Unsupported question",
                            "value": {
                                "type": "unsupported",
                                "message": "This question cannot be answered from the Chinook database schema.",
                                "sql": None,
                                "data": None,
                            },
                        },
                    }
                }
            },
        },
        422: {"description": "Unsafe SQL or SQL that cannot be safely validated."},
        503: {"description": "OpenAI unavailable or timed out."},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "top_artists_by_tracks": {
                            "summary": "Top artists by track count",
                            "value": {
                                "question": "Which are the top 5 artists by number of tracks?",
                                "max_rows": 50,
                            },
                        }
                    }
                }
            }
        }
    },
)
def ask(request: AskRequest, service: AskService = Depends(get_ask_service)) -> AskResponse:
    return service.ask(question=request.question, max_rows=request.max_rows)
