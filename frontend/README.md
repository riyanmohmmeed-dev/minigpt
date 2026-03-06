# Phase 4: Chat UI

Next.js 14 (App Router) frontend: dark theme, glassmorphism panels, sidebar sessions, chat bubbles with **code blocks** (syntax highlight + copy), and **streaming** from the Phase 3 API.

## Prerequisites

- **Backend** running at `http://localhost:8001` (see [backend/README.md](../backend/README.md)).
- **vLLM** running so the backend can proxy chat completions.

## Setup

```bash
cd mini-chatgpt-coding/frontend
npm install
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | Backend API base URL |
| `NEXT_PUBLIC_MODEL` | `default` | Model name sent in chat completions (backend/vLLM may ignore) |

Create `.env.local` to override:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

## Run

```bash
npm run dev
```

Open http://localhost:3000.

## Features

- **Sidebar:** New chat, list of sessions (create via backend), switch session.
- **Chat area:** User messages (right, violet), assistant messages (left, glass panel). Streaming shows a typing cursor.
- **Code blocks:** Messages can contain markdown-style fenced code (e.g. ```python). Rendered with syntax highlighting and a **Copy** button.
- **Input:** Expanding textarea. **Enter** sends, **Shift+Enter** adds a new line.

## Build

```bash
npm run build
npm start
```
