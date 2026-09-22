# LoRA Adapter Weights & Specification

This folder documents the PEFT LoRA (Low-Rank Adaptation) weights and architecture used to adapt [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) into **Homa-Qwen2.5-1.5B** for Gate 2.

## Adapter Configuration

The official configuration is tracked locally in [`adapter_config.json`](./adapter_config.json).

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Base Model** | `Qwen/Qwen2.5-1.5B-Instruct` | Base foundation model |
| **Base Commit SHA** | `d505c65db161245eb65b69ca18db70db545f06e3` | Exact immutable Hugging Face snapshot |
| **PEFT Type** | `LORA` | Parameter-Efficient Fine-Tuning |
| **LoRA Rank ($r$)** | `32` | Rank dimension for adapter update matrices |
| **LoRA Alpha ($\alpha$)** | `64` | Scaling factor ($\alpha / r = 2.0$) |
| **LoRA Dropout** | `0.05` | Dropout probability |
| **Target Modules** | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` | All linear attention and MLP projections |
| **Task Type** | `CAUSAL_LM` | Causal language modeling with completion-only masking |

---

## Weights Distribution & Formats

1. **Primary In-Repository Weights (`bfloat16`):**
   - **Path:** [`../adapter_model.safetensors`](../adapter_model.safetensors)
   - **Size:** **70.48 MB (73,911,472 bytes)**
   - **Precision:** Native `bfloat16` (identically matches base model `Qwen/Qwen2.5-1.5B-Instruct`'s native dtype)
   - **SHA256 Checksum:** `7a73a0b49701faa1614fe1adba4425b8d1d2ef05fc75d403f9f5c6141eba259b`
   - **Benefit:** Directly committed to GitHub without external download dependencies; merges with zero conversion overhead into base model weights.

2. **Double Safety Net — Hosted Full Precision (`float32`):**
   - **Download Script:** [`../download_adapter.sh`](../download_adapter.sh)
   - **Download URL:** [`https://huggingface.co/fallback-ai/Homa-Qwen2.5-1.5B/resolve/d5af1a50c7f9c9959bf423071988a8ac36356c80/gate2_v1/adapter/adapter_model.safetensors`](https://huggingface.co/fallback-ai/Homa-Qwen2.5-1.5B/resolve/d5af1a50c7f9c9959bf423071988a8ac36356c80/gate2_v1/adapter/adapter_model.safetensors)
   - **Size:** 147.7 MB (`float32`)
   - **SHA256 Checksum:** `c75fc442877fa91b0c9744ca4224b9bbd92fa165ca99637134fabf5c4d79645e`
   - **Verification:** Both checksums are tracked in [`../SHA256SUMS.txt`](../SHA256SUMS.txt).

---

## Independent Verification (Python / Transformers)

Organizers can independently load and verify the adapter weights directly against the base model:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
BASE_REVISION = "d505c65db161245eb65b69ca18db70db545f06e3"
ADAPTER_SOURCE = "fallback-ai/Homa-Qwen2.5-1.5B"
ADAPTER_SUBFOLDER = "gate2_v1/adapter"

# 1. Load base model pinned to Gate 2 snapshot
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, revision=BASE_REVISION)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    revision=BASE_REVISION,
    torch_dtype=torch.float16,
    device_map="auto"
)

# 2. Attach Gate 2 LoRA adapter
model = PeftModel.from_pretrained(base_model, ADAPTER_SOURCE, subfolder=ADAPTER_SUBFOLDER)
print("Gate 2 LoRA adapter loaded successfully.")
```
