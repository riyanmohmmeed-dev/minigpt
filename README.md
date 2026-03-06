# minigpt

A coding chatbot built from scratch — custom dataset, LoRA fine-tuning, and a streaming chat UI.

See **[BLUEPRINT.md](BLUEPRINT.md)** for the full plan and research notes.

## Phases

| Phase | Description |
|-------|-------------|
| **1** | Dataset pipeline: seed problems → teacher expansion → quadruplets → `.jsonl` → Hugging Face |
| **2** | LoRA fine-tuning (Qwen2.5-Coder-7B, TRL SFTTrainer) |
| **3** | Inference API (FastAPI + vLLM, OpenAI-compatible, streaming) |
| **4** | Next.js chat UI (dark, code highlight, copy) |

## Quick Start (Phase 2)

After Phase 1, train a LoRA adapter on the SFT dataset (GPU required):

```bash
pip install -r training/requirements.txt

# Default: 7B-Instruct (needs ~16GB VRAM without 4-bit)
python3 training/run_sft.py --dataset data/processed/code_sft.jsonl --output_dir training/output

# Low VRAM: 1.5B + 4-bit (~6GB)
python3 training/run_sft.py --model_name Qwen/Qwen2.5-Coder-1.5B-Instruct --use_4bit \
  --dataset data/processed/code_sft.jsonl --output_dir training/output
```

See **[training/README.md](training/README.md)** for all options and using the trained adapter.

## Quick Start (Phase 3)

Run the inference API (proxy to vLLM). Start vLLM first, then:

```bash
pip install -r backend/requirements.txt
export VLLM_BASE_URL=http://localhost:8000   # optional if vLLM is on 8000
uvicorn backend.app.main:app --reload --port 8001
```

- API docs: http://localhost:8001/docs  
- Chat: `POST http://localhost:8001/v1/chat/completions` (OpenAI-compatible, supports `stream: true`)

See **[backend/README.md](backend/README.md)** for env vars and chat history.

## Quick Start (Phase 4)

Run the chat UI (with backend on 8001):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in `.env.local` if the backend is not on port 8001.

See **[frontend/README.md](frontend/README.md)** for options.

## Quick Start (Phase 1)

```bash
cd mini-chatgpt-coding
python3 -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Optional: set OPENAI_API_KEY for teacher-based expansion
export OPENAI_API_KEY=sk-...

# Generate expanded dataset from seeds (small batch for testing)
python3 scripts/expand_dataset.py --seeds data/seeds --out data/raw --limit 5

# Compile to training .jsonl (SFT messages format)
# Without running the teacher, you can test with the sample: --raw data/raw/expanded_sample.jsonl
python3 scripts/to_jsonl.py --raw data/raw --out data/processed/code_sft.jsonl

# Optional: upload to Hugging Face
python3 scripts/upload_hf.py --dataset data/processed/code_sft.jsonl --repo YOUR_USERNAME/code-instruct-sft
```

**Train on your repo code (no API key):** See [TRAINING-LOCAL.md](TRAINING-LOCAL.md). Run `scripts/build_dataset_from_repo.py` to build a dataset from all code in your workspace, then train with `training/run_sft.py`.

## Project Layout

```
mini-chatgpt-coding/
├── BLUEPRINT.md
├── data/
│   ├── seeds/          # Seed problems (JSON)
│   ├── raw/            # Teacher outputs
│   └── processed/      # .jsonl for training
├── scripts/
│   ├── expand_dataset.py
│   ├── to_jsonl.py
│   ├── build_dataset_from_repo.py   # Build SFT from repo code (no API key)
│   └── upload_hf.py
├── training/           # Phase 2: LoRA SFT
│   ├── README.md
│   ├── requirements.txt
│   ├── run_sft.py
│   └── output/         # adapter saved here by default
├── backend/            # Phase 3: FastAPI + vLLM proxy
│   ├── README.md
│   ├── requirements.txt
│   └── app/
│       ├── main.py     # /v1/chat/completions, streaming, sessions
│       ├── config.py
│       └── storage.py  # optional SQLite chat history
├── frontend/           # Phase 4: Next.js chat UI
│   ├── README.md
│   ├── package.json
│   └── src/
│       ├── app/        # layout, page
│       ├── components/ # Sidebar, ChatMessage, ChatInput
│       └── lib/        # api.ts (streaming client)
```

## License

MIT
