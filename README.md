# chinook-text-to-sql

FastAPI API for asking natural language questions over a PostgreSQL Chinook database.

The API exposes health checks, direct database connectivity checks, and a Natural Language to SQL endpoint backed by OpenAI structured outputs. Generated SQL is validated before execution and only read-only Chinook queries are accepted.

## Requirements

- Python 3.12
- uv
- Access to a PostgreSQL database already loaded with the Chinook schema using lower_snake_case table and column names
- An OpenAI API key

## Environment Variables

Create a local `.env` from `.env.example`:

```bash
cp .env.example .env
```

Required database variables:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

OpenAI variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`, defaults to `gpt-4o-mini`
- `OPENAI_TIMEOUT_SECONDS`, defaults to `30`

## Local Setup

Create and activate a virtual environment:

```bash
uv venv
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
uv sync
```

Run locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger/OpenAPI is available at:

```text
http://localhost:8000/docs
```

## Test Endpoints

```bash
curl http://localhost:8000/health
curl http://localhost:8000/db-health
curl http://localhost:8000/artists/count
curl http://localhost:8000/artists/top-by-albums
```

Expected `/health` response:

```json
{"status":"ok"}
```

Expected `/db-health` response when PostgreSQL is reachable:

```json
{"database":"ok"}
```

## Ask Endpoint

`POST /api/v1/ask`

Successful query example:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Which are the top 5 artists by number of tracks?","max_rows":50}'
```

Example response:

```json
{
  "type": "query",
  "message": "Query executed successfully.",
  "sql": "SELECT artist.name AS artist_name, COUNT(track.track_id) AS track_count FROM artist JOIN album ON album.artist_id = artist.artist_id JOIN track ON track.album_id = album.album_id GROUP BY artist.name ORDER BY track_count DESC LIMIT 50",
  "data": [
    {
      "artist_name": "Iron Maiden",
      "track_count": 213
    }
  ]
}
```

Ambiguous request example:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me the best customers","max_rows":50}'
```

Example response:

```json
{
  "type": "ambiguous",
  "message": "The question is ambiguous. Please submit a new complete question clarifying whether best customers means highest total spending, most invoices, highest average invoice value, or most tracks purchased.",
  "sql": null,
  "data": null
}
```

Unsupported request example:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me current Bitcoin prices","max_rows":50}'
```

Example response:

```json
{
  "type": "unsupported",
  "message": "This question cannot be answered from the Chinook database schema.",
  "sql": null,
  "data": null
}
```

## Tests

Run unit tests:

```bash
uv run pytest
```

The tests cover SQL validation and ask-service orchestration with mocked OpenAI and database dependencies.

## Docker

Build the image locally:

```bash
docker build -t chinook-text-to-sql:local .
```

Run the container:

```bash
docker run --rm -p 8000:8000 --env-file .env chinook-text-to-sql:local
```

## Kubernetes

Manifests are in `k8s/`.

The Deployment expects a Kubernetes Secret named `chinook-db-secret` in the `chinook` namespace with these keys:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

It also expects a Kubernetes Secret named `app-secrets` with:

- `OPENAI_API_KEY`

`OPENAI_MODEL` and `OPENAI_TIMEOUT_SECONDS` are configured in the Deployment manifest.

For GitHub Actions deploys, store `OPENAI_API_KEY` as a GitHub Actions secret. The deploy workflow creates or updates the Kubernetes `app-secrets` secret without hardcoding the key in the repository.

## Security Considerations

- This demo validates generated SQL at the application layer before execution.
- Only `SELECT` queries over an explicit Chinook table allowlist are accepted.
- Multiple statements, comments, unknown tables, and mutating operations are rejected.
- Result size is limited by `max_rows` with a hard cap of 100.
- The API never executes SQL when the model returns `ambiguous` or `unsupported`.
- OpenAI API keys are provided only through environment variables and Kubernetes secrets.
- In production, the database connection should use a dedicated read-only PostgreSQL user.
- The read-only user should only have `SELECT` permissions on the allowed Chinook tables.
- Application-level validation is necessary but not sufficient as the only production security boundary.
- Query timeout or statement timeout should be enforced to avoid expensive `SELECT` queries.
