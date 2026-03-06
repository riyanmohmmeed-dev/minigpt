"""
FastAPI app: OpenAI-compatible proxy to vLLM with streaming (SSE) and optional chat history.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .storage import get_storage

app = FastAPI(
    title="Mini-ChatGPT Coding API",
    description="OpenAI-compatible chat completions proxy to vLLM; optional chat history.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _vllm_url(path: str) -> str:
    base = settings.vllm_base_url.rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    """List models (proxy to vLLM)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(_vllm_url("v1/models"))
        r.raise_for_status()
        return r.json()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    """
    OpenAI-compatible chat completions. Proxies to vLLM.
    Supports stream=True for SSE streaming.
    Optional: pass header X-Session-Id to persist messages to chat history.
    """
    body = await request.json()
    stream = body.get("stream", False)
    session_id = request.headers.get("X-Session-Id") or None

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            if stream:
                return await _stream_completions(client, body, session_id)
            return await _nonstream_completions(client, body, session_id)
    except httpx.ConnectError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "message": "vLLM is not running. Start it with: vllm serve <model> --port 8000 (see backend README).",
                    "code": "vllm_unavailable",
                }
            },
        )
    except httpx.HTTPStatusError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.response.status_code,
            content={"error": {"message": str(e), "code": "upstream_error"}},
        )


async def _nonstream_completions(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    session_id: str | None,
) -> Response:
    """Non-streaming: forward to vLLM and optionally save to history."""
    url = _vllm_url("v1/chat/completions")
    r = await client.post(url, json=body)
    r.raise_for_status()
    data = r.json()

    if session_id and "choices" in data and data["choices"]:
        storage = get_storage()
        if storage:
            msg = data["choices"][0].get("message")
            if msg:
                storage.append_message(session_id, "assistant", msg.get("content", ""))

    return Response(content=r.content, media_type="application/json")


async def _stream_completions(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    session_id: str | None,
) -> Response:
    """Streaming: forward vLLM SSE stream to client."""
    url = _vllm_url("v1/chat/completions")
    body = {**body, "stream": True}

    async def generate() -> Any:
        full_content: list[str] = []
        async with client.stream("POST", url, json=body) as r:
            r.raise_for_status()
            async for chunk in r.aiter_bytes():
                full_content.append(chunk.decode("utf-8", errors="replace"))
                yield chunk

        if session_id and full_content:
            storage = get_storage()
            if storage:
                content = _extract_content_from_sse(full_content)
                if content:
                    storage.append_message(session_id, "assistant", content)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _extract_content_from_sse(sse_chunks: list[str]) -> str:
    """Parse SSE chunks and concatenate delta content."""
    parts: list[str] = []
    for raw in sse_chunks:
        for line in raw.split("\n"):
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    continue
                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        parts.append(delta["content"])
                except json.JSONDecodeError:
                    pass
    return "".join(parts)


# ---------- Optional: chat history (SQLite) ----------


@app.post("/v1/sessions")
async def create_session() -> dict[str, str]:
    """Create a new chat session. Returns session_id."""
    session_id = str(uuid.uuid4())
    storage = get_storage()
    if storage:
        storage.create_session(session_id)
    return {"session_id": session_id}


@app.get("/v1/sessions/{session_id}/messages")
async def get_session_messages(session_id: str) -> dict[str, Any]:
    """Get all messages for a session."""
    storage = get_storage()
    if not storage:
        return {"messages": []}
    messages = storage.get_messages(session_id)
    return {"messages": messages}


@app.post("/v1/sessions/{session_id}/messages")
async def append_message(session_id: str, request: Request) -> dict[str, str]:
    """Append a user message (for history tracking). Body: {"role": "user", "content": "..."}."""
    body = await request.json()
    role = body.get("role", "user")
    content = body.get("content", "")
    storage = get_storage()
    if storage:
        storage.append_message(session_id, role, content)
    return {"status": "ok"}
