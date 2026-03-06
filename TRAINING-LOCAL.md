# Train on your repo code (no API key)

Use **only** code in your workspace to train the model. No API keys, no external services.

## 1. Build dataset from repo

From `mini-chatgpt-coding` (or GitTime root):

```bash
cd mini-chatgpt-coding
python3 scripts/build_dataset_from_repo.py --root /path/to/your/workspace --out data/processed/repo_code_sft.jsonl
```

- **`--root`**: Directory to scan (default: parent of mini-chatgpt-coding, i.e. GitTime).
- **`--out`**: Output JSONL path (default: `data/processed/repo_code_sft.jsonl`).

The script collects code files (`.py`, `.ts`, `.tsx`, `.js`, `.html`, `.css`, `.md`, etc.) and skips `node_modules`, `.git`, `venv`, `.next`, etc. Each file becomes one user/assistant example.

## 2. Train locally (LoRA, no API key)

```bash
pip install -r training/requirements.txt
python3 training/run_sft.py --dataset data/processed/repo_code_sft.jsonl --output_dir training/output
```

Use `--use_4bit` and/or `--model_name Qwen/Qwen2.5-Coder-1.5B-Instruct` if you have limited VRAM.

No API key is used anywhere: dataset is built from local files, training uses Hugging Face models (download only).

## 3. Use the trained model

Point vLLM at the merged adapter (or load with PEFT as in training/README.md), then use the chat UI as usual.
