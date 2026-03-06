"""
LoRA SFT training for Mini-ChatGPT Coding: load SFT JSONL (messages format), fine-tune Qwen2.5-Coder with PEFT/LoRA, save adapter.

Usage (from repo root or training/):
  python training/run_sft.py --dataset data/processed/code_sft.jsonl --output_dir training/output
  python training/run_sft.py --model_name Qwen/Qwen2.5-Coder-1.5B-Instruct --use_4bit --dataset data/processed/code_sft.jsonl --output_dir training/output

Requires: GPU with enough VRAM (4-bit 7B ~10GB; 1.5B full ~6GB). Install: pip install -r training/requirements.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer


# Default LoRA target modules for Qwen2 / LLaMA-like attention
DEFAULT_LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

# Default training (small dataset: few epochs, higher LR for LoRA)
DEFAULT_EPOCHS = 3
DEFAULT_BATCH_SIZE = 2
DEFAULT_GRAD_ACCUM = 4
DEFAULT_LR = 2e-4
DEFAULT_MAX_SEQ_LENGTH = 2048


def load_jsonl_messages(path: Path) -> Dataset:
    """Load a JSONL file where each line is {"messages": [{"role": "...", "content": "..."}, ...]}."""
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if "messages" in row and isinstance(row["messages"], list):
                    rows.append(row)
            except json.JSONDecodeError:
                continue
    if not rows:
        raise ValueError(f"No valid 'messages' rows in {path}")
    return Dataset.from_list(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="LoRA SFT training on Qwen2.5-Coder with messages-formatted JSONL")
    ap.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-Coder-7B-Instruct", help="Hugging Face model id")
    ap.add_argument("--dataset", type=Path, default=Path("data/processed/code_sft.jsonl"), help="Path to SFT JSONL (messages format)")
    ap.add_argument("--output_dir", type=Path, default=Path("training/output"), help="Where to save adapter and logs")
    ap.add_argument("--use_4bit", action="store_true", help="Load model in 4-bit (bitsandbytes); saves VRAM")
    ap.add_argument("--lora_r", type=int, default=32, help="LoRA rank")
    ap.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha (scaling)")
    ap.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout")
    ap.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of training epochs")
    ap.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE, help="Per-device train batch size")
    ap.add_argument("--gradient_accumulation_steps", type=int, default=DEFAULT_GRAD_ACCUM, help="Gradient accumulation steps")
    ap.add_argument("--lr", type=float, default=DEFAULT_LR, help="Peak learning rate")
    ap.add_argument("--max_seq_length", type=int, default=DEFAULT_MAX_SEQ_LENGTH, help="Max sequence length")
    ap.add_argument("--push_to_hub", type=str, default="", help="Optional: push adapter to this HF repo (e.g. USER/code-coder-7b-lora)")
    ap.add_argument("--hub_private", action="store_true", help="Push as private repo")
    args = ap.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve dataset path relative to repo root (parent of training/)
    dataset_path = args.dataset
    if not dataset_path.is_absolute():
        repo_root = Path(__file__).resolve().parent.parent
        dataset_path = repo_root / dataset_path
    train_dataset = load_jsonl_messages(dataset_path)
    print(f"Loaded {len(train_dataset)} examples from {dataset_path}", file=sys.stderr)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Convert messages to single "text" field using model's chat template (for next-token prediction)
    def format_messages_as_text(example):
        messages = example.get("messages", [])
        if not messages:
            return {"text": ""}
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    train_dataset = train_dataset.map(format_messages_as_text, remove_columns=train_dataset.column_names, num_proc=1)
    train_dataset = train_dataset.filter(lambda x: bool(x.get("text")), num_proc=1)

    model_kwargs = {"trust_remote_code": True, "torch_dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32}
    if args.use_4bit:
        try:
            from transformers import BitsAndBytesConfig
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        except ImportError:
            print("bitsandbytes not installed; run without --use_4bit or pip install bitsandbytes", file=sys.stderr)
            sys.exit(2)

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)

    if args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=DEFAULT_LORA_TARGET_MODULES,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        bf16=torch.cuda.is_available(),
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        push_to_hub=bool(args.push_to_hub),
        hub_model_id=args.push_to_hub or None,
        hub_private_repo=args.hub_private,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=False,
    )

    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Adapter and tokenizer saved to {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
