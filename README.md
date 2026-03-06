# minigpt

A coding chatbot built from scratch — custom dataset, LoRA fine-tuning, and a streaming chat UI.

> I wanted to understand how models like ChatGPT actually work under the hood, not just call an API. So I built one from the ground up: generated my own training data, fine-tuned a small model with LoRA, and wired it to a chat interface that streams responses in real time.

---

## What this does

- Generates a custom coding dataset from seed problems (or from your own repos)
- Fine-tunes Qwen2.5-Coder using LoRA (runs on a single GPU)
- Serves the model through a FastAPI backend with OpenAI-compatible endpoints
- Streams responses to a dark-mode Next.js chat UI with syntax highlighting

## Tech stack

**Training:** Python, Hugging Face Transformers, PEFT/LoRA, TRL SFTTrainer, bitsandbytes (4-bit)  
**Backend:** FastAPI, vLLM, httpx, SQLite (chat history)  
**Frontend:** Next.js 15, React, TailwindCSS, react-syntax-highlighter  

## Getting started

### 1. Generate the dataset

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A: Build from your own code (no API key needed)
python3 scripts/build_dataset_from_repo.py --root /path/to/your/code --out data/processed/repo_code_sft.jsonl

# Option B: Expand seed problems via teacher model (needs OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
python3 scripts/expand_dataset.py --seeds data/seeds --out data/raw
python3 scripts/to_jsonl.py --raw data/raw --out data/processed/code_sft.jsonl
```

### 2. Train the model (GPU required)

```bash
pip install -r training/requirements.txt

# 7B model with 4-bit quantization (~10GB VRAM)
python3 training/run_sft.py \
  --dataset data/processed/repo_code_sft.jsonl \
  --output_dir training/output \
  --use_4bit

# Or use the smaller 1.5B model (~6GB VRAM)
python3 training/run_sft.py \
  --model_name Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --dataset data/processed/repo_code_sft.jsonl \
  --output_dir training/output
```

### 3. Start the backend

```bash
# First, serve your model with vLLM
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct --port 8000

# Then start the API
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8001
```

API is OpenAI-compatible: `POST /v1/chat/completions` with `stream: true`.

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and start chatting.

## Project structure

```
minigpt/
├── scripts/                    # Dataset generation
│   ├── build_dataset_from_repo.py   # Scan code repos → training data
│   ├── expand_dataset.py            # Teacher model expansion
│   ├── to_jsonl.py                  # Convert to SFT format
│   └── upload_hf.py                 # Push dataset to Hugging Face
├── data/
│   ├── seeds/                  # Starter problems
│   └── processed/              # Generated .jsonl files
├── training/
│   └── run_sft.py              # LoRA fine-tuning script
├── backend/
│   └── app/
│       ├── main.py             # FastAPI server (streaming, sessions)
│       ├── config.py
│       └── storage.py          # SQLite chat history
└── frontend/
    └── src/
        ├── app/                # Next.js pages
        ├── components/         # ChatMessage, ChatInput, Sidebar
        └── lib/                # API client with SSE streaming
```

## Status

- [x] Dataset generation pipeline
- [x] LoRA training script
- [x] FastAPI inference backend
- [x] Next.js chat UI
- [ ] Full dataset training run
- [ ] Model deployment

## License

MIT
