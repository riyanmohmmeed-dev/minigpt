# Phase 3: Inference API

FastAPI backend that proxies to **vLLM** (OpenAI-compatible). Provides `POST /v1/chat/completions` with **streaming** (SSE) and optional **SQLite chat history**.

## Prerequisites

1. **vLLM** running with your model (base or LoRA-merged), e.g.:

   ```bash
   # Install vLLM (GPU): pip install vllm
   vllm serve Qwen/Qwen2.5-Coder-7B-Instruct --dtype auto --port 8000
   ```

   For a **trained LoRA adapter**, merge it with the base model first, or use vLLM’s `--enable-lora` if supported, then point the backend at that server.

2. **Backend** runs on a different port (e.g. 8001) and forwards requests to vLLM.

## Setup

From repo root:

```bash
cd mini-chatgpt-coding
pip install -r backend/requirements.txt
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_BASE_URL` | `http://localhost:8000` | vLLM server URL |
| `ENABLE_CHAT_HISTORY` | `true` | Enable SQLite chat history |
| `CHAT_HISTORY_DB` | `backend/chat_history.db` | SQLite file path |

## Run

```bash
# From repo root
uvicorn backend.app.main:app --reload --port 8001
```

Then:

- **API docs:** http://localhost:8001/docs  
- **Chat completions:** `POST http://localhost:8001/v1/chat/completions`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/v1/models` | List models (proxy to vLLM) |
| POST | `/v1/chat/completions` | OpenAI-compatible chat; use `"stream": true` for SSE |
| POST | `/v1/sessions` | Create chat session (returns `session_id`) |
| GET | `/v1/sessions/{id}/messages` | Get session messages |
| POST | `/v1/sessions/{id}/messages` | Append a message (e.g. user) |

## Chat completions (OpenAI format)

**Non-streaming:**

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "messages": [{"role": "user", "content": "Write a Python function to reverse a string."}]
  }'
```

**Streaming (SSE):**

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**With chat history:** send header `X-Session-Id: <session_id>`. Create a session via `POST /v1/sessions` first. Assistant responses are stored when this header is present.

## Frontend (Phase 4)

Point the Next.js app at `http://localhost:8001` (or your backend URL) as the API base for chat completions and streaming.
