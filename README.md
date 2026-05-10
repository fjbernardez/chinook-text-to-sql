# chinook-text-to-sql

Minimal FastAPI API for the Chinook PostgreSQL database.

This milestone includes health checks and direct PostgreSQL connectivity checks only. OpenAI integration, text-to-SQL, GitHub Actions, and k3s deployment automation will be added later.

## Requirements

- Python 3.12
- uv
- Access to a PostgreSQL database already loaded with the Chinook schema using lower_snake_case table and column names

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
uv pip install -e .
```

Create a local environment file:

```bash
cp .env.example .env
```

Then edit `.env` with your PostgreSQL connection settings.

## Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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
