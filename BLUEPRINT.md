# Mini-ChatGPT for Coding — Project Blueprint

End-to-end plan for building a **specialized coding assistant** using a Custom Small Language Model (SLM) trained on a bespoke dataset. Based on Self-Instruct (Stanford Alpaca), OpenCodeInstruct (NVIDIA), and modern PEFT/LoRA + vLLM practices.

---

## Research Summary (Validated)

| Component | Source | Notes |
|-----------|--------|--------|
| **OpenCodeInstruct** | NVIDIA, Hugging Face `nvidia/OpenCodeInstruct` | 5M+ coding Q&A pairs; instruction + solution + tests + quality; Self-Instruct / Evol-Instruct; can reuse or mirror format. |
| **Qwen2.5-Coder** | `Qwen/Qwen2.5-Coder-7B`, `Qwen2.5-Coder-7B-Instruct` | 7.61B params, 128K context; Unsloth offers efficient LoRA; 285+ fine-tuned variants on HF. |
| **vLLM** | docs.vllm.ai | OpenAI-compatible `/v1/chat/completions`, streaming via SSE; use `stream=True` with OpenAI client. |
| **TRL SFTTrainer** | Hugging Face TRL | Supports `messages` format (user/assistant); applies chat template via tokenizer; prompt/completion or conversational. |
| **Self-Instruct / Alpaca** | Stanford, `yizhongw/self_instruct` | JSONL: instruction + output; seed instructions expanded by teacher model. |

---

## 1. Custom Dataset Creation (The "Secret Sauce")

- **Approach:** Synthetic data via Self-Instruct; data quality > model size.
- **Seed:** ~100 diverse programming problems + solutions (curated).
- **Expansion:** Teacher model (GPT-4o / Llama-3-70B via API) expands to 10k+ examples.
- **Format — Quadruplets (for deep learning):**
  - `instruction`: User prompt (e.g. "Write a Python script to...")
  - `reasoning`: Step-by-step Chain of Thought
  - `code`: Code snippet
  - `verification`: Test case or explanation
- **Tooling:** Python scripts using `datasets` to produce `.jsonl` and optionally upload to Hugging Face.

## 2. Model Selection & Fine-Tuning (AI Engine)

- **Base:** SLM that runs locally — **Qwen2.5-Coder-7B** or **DeepSeek-Coder-1.3B**.
- **Technique:** PEFT/LoRA (freeze base, train adapter); 4-bit quantization with `bitsandbytes`.
- **Stack:** `transformers`, `peft`, `trl` (SFTTrainer), `bitsandbytes`; single consumer GPU or RunPod.
- **Output:** Adapter weights (merge or push to HF).

## 3. Inference Backend (Engine Room)

- **API:** FastAPI (async).
- **Server:** vLLM (or Ollama) — PagedAttention, fast token generation.
- **Endpoints:** `POST /v1/chat/completions` (OpenAI-compatible), streaming via SSE.
- **Optional:** SQLite/PostgreSQL for chat history.

## 4. Frontend (ChatGPT-like UX)

- **Stack:** Next.js 15 (App Router), React, TailwindCSS.
- **Design:** Dark mode, glassmorphism, typing animation.
- **Features:** Sidebar (sessions), chat bubbles, code block renderer (syntax highlight + copy), expanding input (Enter send, Shift+Enter newline).

---

## Action Plan — Phases

| Phase | Focus | Deliverables |
|-------|--------|---------------|
| **1** | Dataset generation pipeline | Seed data, expansion script, quadruplet schema, `.jsonl` + HF upload |
| **2** | Training loop | LoRA fine-tuning notebook/script, export adapter |
| **3** | Inference API | FastAPI + vLLM wrapper, streaming, optional DB |
| **4** | Chat UI | Next.js app, streaming client, code renderer |

---

## Project Structure (Target)

```
mini-chatgpt-coding/
├── README.md
├── BLUEPRINT.md           # this file
├── data/
│   ├── seeds/             # ~100 seed problems (JSON/YAML)
│   ├── raw/               # expanded raw outputs from teacher
│   └── processed/         # compiled .jsonl
├── scripts/
│   ├── expand_dataset.py  # teacher API → quadruplets
│   ├── to_jsonl.py        # compile to SFT format
│   └── upload_hf.py       # push to Hugging Face
├── training/              # Phase 2
├── backend/               # Phase 3: FastAPI + vLLM
└── frontend/              # Phase 4: Next.js
```

---

*Reference: Microsoft CodeOcean, Stanford Alpaca/Self-Instruct, OpenCodeInstruct, TRL docs, vLLM OpenAI server.*
