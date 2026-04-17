# AI Chatbot API

Production-style FastAPI backend for a secure, memory-enabled chatbot powered by GitHub Models via Azure AI Inference SDK.

## Features

- Chat endpoint backed by GitHub-hosted LLMs
- Per-request API key authentication (`X-API-Key`)
- In-memory sliding-window rate limiting
- Input validation and sanitization
- Conversation memory persisted in SQLite
- Conversation history and management endpoints
- Security headers middleware
- Unit and integration tests with pytest

## Tech Stack

- Python 3.12+
- FastAPI
- Uvicorn
- Azure AI Inference SDK (`azure-ai-inference`)
- SQLite
- Pytest

## Project Structure

```text
project-file/
|-- app/
|   |-- api/
|   |   |-- chat.py
|   |   `-- history.py
|   |-- core/
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- exceptions.py
|   |   `-- security.py
|   |-- middleware/
|   |   `-- security_middleware.py
|   |-- models/
|   |   |-- chat.py
|   |   `-- memory.py
|   |-- repositories/
|   |   `-- memory_repository.py
|   |-- services/
|   |   |-- llm_service.py
|   |   |-- memory_service.py
|   |   `-- prompt_service.py
|   `-- main.py
|-- tests/
|   |-- integration/
|   |-- unit/
|   `-- evaluation/
|-- .env.example
|-- conftest.py
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.12 or newer
- A GitHub Models token/API key with access to your target model

## Setup

### 1. Clone and enter project

```bash
git clone https://github.com/Tharindu-Nimsara/AI-Chatbot-API.git
cd AI-Chatbot-API
```

### 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and set values.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Minimum required values:

- `GITHUB_TOKEN`
- `API_SECRET_KEY`

Optional values are listed in the next section.

## Environment Variables

Defined in `.env.example` and loaded by `app/core/config.py`.

### App

- `APP_NAME` (default: `AI Chatbot API`)
- `APP_VERSION` (default: `1.0.0`)
- `DEBUG` (default: `False`)

### GitHub Models

- `GITHUB_TOKEN` (required)
- `GITHUB_MODEL_ENDPOINT` (default: `https://models.github.ai/inference`)
- `GITHUB_MODEL_NAME` (default in code: `xai/grok-3-mini`)

### Generation

- `MAX_TOKENS` (default: `1000`)
- `TEMPERATURE` (default: `0.7`)
- `TOP_P` (default: `1.0`)

### Persona

- `BOT_NAME` (default: `Aria`)
- `BOT_PERSONA`
- `BOT_LANGUAGE_STYLE`
- `MAX_RESPONSE_LENGTH`

### Memory

- `DATABASE_URL` (default: `data/chatbot.db`)
- `MAX_HISTORY_MESSAGES` (default: `10`)
- `MAX_HISTORY_TOKENS` (default: `3000`)

### Security

- `API_SECRET_KEY` (required for authenticated routes)
- `RATE_LIMIT_REQUESTS` (default: `10`)
- `RATE_LIMIT_WINDOW` (default: `60` seconds)
- `MAX_MESSAGE_LENGTH` (default: `2000`)
- `ALLOWED_ORIGINS` (default: `*`)

## Run the API

```bash
uvicorn app.main:app --reload
```

Server:

- Base URL: `http://127.0.0.1:8000`
- OpenAPI UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Authentication

Protected endpoints require:

- Header: `X-API-Key`
- Value: your `API_SECRET_KEY`

Unauthenticated requests return `401`.

## API Endpoints

### Health

- `GET /health`
- No auth required

Response:

```json
{ "status": "healthy" }
```

### Root

- `GET /`
- No auth required

### Chat

- `POST /api/v1/chat`
- Auth required (`X-API-Key`)

Request body:

```json
{
  "message": "Explain what an API is in simple terms",
  "session_id": "optional-session-id"
}
```

Successful response:

```json
{
  "reply": "An API is like a messenger between apps.",
  "session_id": "9f2f02f8-0c6b-4b4a-a632-9ef68c5f09dc",
  "model": "xai/grok-3-mini",
  "input_tokens": 32,
  "output_tokens": 14
}
```

Common statuses:

- `200` success
- `400` validation or model config/token issues
- `401` missing/invalid API key
- `429` rate limit exceeded
- `503` upstream LLM/provider issues
- `500` unexpected server error

### History by Session

- `GET /api/v1/history/{session_id}`
- Auth required

### List Conversations

- `GET /api/v1/conversations`
- Auth required

### Clear Session History

- `DELETE /api/v1/history/{session_id}`
- Auth required

## Usage Examples

### PowerShell (recommended)

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/chat" `
  -Headers @{ "X-API-Key" = "your-api-secret" } `
  -ContentType "application/json" `
  -Body '{"message":"Explain what an API is in simple terms"}'
```

### curl (cmd/bash)

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "X-API-Key: your-api-secret" \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain what an API is in simple terms"}'
```

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run only unit tests:

```bash
pytest tests/unit -v
```

Run only integration tests:

```bash
pytest tests/integration -v
```

## How Memory Works

- Each new chat can generate a `session_id` if not provided.
- User and assistant messages are stored in SQLite (`conversations` and `messages` tables).
- Recent messages are fetched for context, then trimmed by token budget before LLM call.
- History endpoints expose and manage stored conversations.

## Security Notes

- Never commit a real `.env` file.
- Use a strong `API_SECRET_KEY` in non-test environments.
- Current rate limiting is in-memory (single-process); use Redis for distributed deployments.
- CORS defaults are open (`*`); restrict `ALLOWED_ORIGINS` in production.

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'` when running tests

Run tests from the repository root and ensure the root `conftest.py` exists (it sets project path for pytest).

### PowerShell `curl` header errors

PowerShell aliases `curl` to `Invoke-WebRequest`. Use `Invoke-RestMethod` syntax (shown above) or use `curl.exe` explicitly.

### Missing virtual environment activation script

If `venv/Scripts/Activate.ps1` is missing, your environment was created incompletely. Recreate it:

```powershell
Remove-Item -Recurse -Force .\venv
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Uvicorn not found

Either activate venv first or run with interpreter directly:

```powershell
.\venv\Scripts\python -m uvicorn app.main:app --reload
```

## Development Notes

- Logging is configured in `app/main.py`.
- Database initializes on startup via FastAPI lifespan.
- Security middleware adds standard response headers to all requests.


## Author

- Repository owner: Tharindu-Nimsara
