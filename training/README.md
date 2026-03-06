# Phase 2: LoRA SFT Training

Fine-tune **Qwen2.5-Coder** (7B or 1.5B) on the SFT dataset (messages → chat format) using **PEFT/LoRA** and **TRL SFTTrainer**. Saves adapter weights to `training/output` (or `--output_dir`).

## Requirements

- **GPU** with enough VRAM:
  - **7B in 4-bit:** ~10–12 GB (use `--use_4bit`)
  - **1.5B full:** ~6 GB
  - **7B full:** ~16+ GB
- Python 3.10+, CUDA if using GPU.

## Setup

From the **repo root** (or from `training/`):

```bash
cd mini-chatgpt-coding
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r training/requirements.txt
```

## Prepare dataset

Ensure you have a SFT JSONL in messages format (from Phase 1):

```bash
python3 scripts/to_jsonl.py --raw data/raw/expanded_sample.jsonl --out data/processed/code_sft.jsonl
# Or use your full expanded.jsonl after running expand_dataset.py.
```

## Run training

**Default (7B-Instruct, no quantization):**

```bash
python3 training/run_sft.py \
  --dataset data/processed/code_sft.jsonl \
  --output_dir training/output
```

**Low VRAM: 4-bit quantization + 1.5B model**

```bash
python3 training/run_sft.py \
  --model_name Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --use_4bit \
  --dataset data/processed/code_sft.jsonl \
  --output_dir training/output
```

**Push adapter to Hugging Face after training**

```bash
python3 training/run_sft.py \
  --dataset data/processed/code_sft.jsonl \
  --output_dir training/output \
  --push_to_hub YOUR_USERNAME/code-coder-7b-lora
```

## Output

- `training/output/` (or your `--output_dir`):
  - Adapter weights (PEFT/LoRA)
  - Tokenizer (same as base model)
- Training logs and checkpoints (by epoch, `save_total_limit=2`).

## Using the trained model

Load base model + adapter for inference (e.g. in Phase 3 backend or a notebook):

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-7B-Instruct", trust_remote_code=True)
model = PeftModel.from_pretrained(base, "training/output")
tokenizer = AutoTokenizer.from_pretrained("training/output")
```

For vLLM, merge the adapter into the base model and save, then point vLLM at the merged model (or use vLLM’s Peft support if available).

## Options (run_sft.py)

| Flag | Default | Description |
|------|--------|-------------|
| `--model_name` | Qwen/Qwen2.5-Coder-7B-Instruct | Hugging Face model id |
| `--dataset` | data/processed/code_sft.jsonl | SFT JSONL path |
| `--output_dir` | training/output | Save directory |
| `--use_4bit` | false | Use 4-bit quantization (bitsandbytes) |
| `--lora_r` | 32 | LoRA rank |
| `--lora_alpha` | 16 | LoRA alpha |
| `--epochs` | 3 | Training epochs |
| `--batch_size` | 2 | Per-device batch size |
| `--gradient_accumulation_steps` | 4 | Gradient accumulation |
| `--lr` | 2e-4 | Peak learning rate |
| `--max_seq_length` | 2048 | Max sequence length |
| `--push_to_hub` | (none) | HF repo id to push adapter |
| `--hub_private` | false | Push as private |
