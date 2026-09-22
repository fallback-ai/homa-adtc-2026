# Homa SFT Gate 2 Training Script
import os, math, torch, json
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, EarlyStoppingCallback
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
HOMA_SYSTEM = "You are Homa, an offline agricultural assistant for farmers in Nigeria, built by Fallback AI. You give practical, direct advice on crops, livestock, soil, pests, weather, and markets."

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16).to("cuda")

peft_cfg = LoraConfig(
    r=32, lora_alpha=64, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)
model = get_peft_model(model, peft_cfg)

with open("combined_train_v5_clean.jsonl", "r", encoding="utf-8") as f:
    raw = [json.loads(l) for l in f if l.strip()]

def to_chatml(row):
    prompt = f"<|im_start|>system\n{HOMA_SYSTEM}<|im_end|>\n<|im_start|>user\n{row['instruction'].strip()}<|im_end|>\n<|im_start|>assistant\n"
    completion = f"{row['response'].strip()}<|im_end|>\n"
    return {"prompt": prompt, "completion": completion}

dataset = Dataset.from_list(raw).map(to_chatml)
dataset = dataset.remove_columns([c for c in dataset.column_names if c not in ("prompt", "completion")])
dataset = dataset.train_test_split(test_size=0.1, seed=42)

args = SFTConfig(
    output_dir="./checkpoints", num_train_epochs=3, per_device_train_batch_size=8,
    per_device_eval_batch_size=4, gradient_accumulation_steps=4, learning_rate=4e-5,
    lr_scheduler_type="cosine", warmup_steps=6, completion_only_loss=True, logging_steps=50,
    eval_strategy="steps", eval_steps=50, save_steps=50, save_total_limit=2,
    load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
    bf16=True, gradient_checkpointing=True, max_length=1024, packing=False, report_to="none"
)

trainer = SFTTrainer(
    model=model, args=args, train_dataset=dataset["train"], eval_dataset=dataset["test"],
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
)
trainer.train()
trainer.model.save_pretrained("./lora-adapter")
tokenizer.save_pretrained("./lora-adapter")
