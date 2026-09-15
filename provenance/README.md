# Proof-of-Training & Model Provenance

This folder documents how `Homa-Qwen2.5-1.5B` was adapted from its base model,
so organizers can independently verify that the submission is a genuine
fine-tune (Gate 2: *Proof-of-Training* and *Model Provenance Disclosure*).

## Provenance summary

| Field | Value |
| --- | --- |
| Base model | [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) |
| Base model commit SHA | `<FILL: git rev-parse of the HF snapshot used>` |
| Fine-tuning method | LoRA SFT (PEFT), completion-only loss masking (TRL) |
| LoRA config | r=32, α=64, dropout=0.05, target = all linear projections (q,k,v,o,gate,up,down) |
| Training data | `sft_train_samples/combined_train.en.jsonl` (English agronomic instruction/response) |
| Merge | LoRA merged into base on CPU (`merge_and_unload`) → `homa-qwen15b-merged` |
| Quantization | GGUF F16 → Q4_K_M via llama.cpp (`convert_hf_to_gguf.py`, `llama-quantize`) |
| Runtime | llama.cpp / Ollama, ChatML template |

> Replace every `<FILL: ...>` placeholder before submission. Do not leave
> placeholders in the final Gate 2 package.

## Contents

| Path | What it is | Gate 2 requirement |
| --- | --- | --- |
| `adapters/` | LoRA adapter weights (`adapter_model.safetensors`, `adapter_config.json`) | Adapter weights |
| `../training/train_qwen15b.py` | The exact SFT + merge script used (submission model) | Training scripts / configs |
| `../training/train_gemma1b.py` | Earlier research-track training script | Training scripts / configs |
| `scripts/merge_and_quantize.sh` | Merge → F16 GGUF → Q4_K_M conversion pipeline | Merge / quantization scripts |
| `logs/` | Training loss / eval logs exported from the run | Loss / performance logs |
| `datasets/DATA_LICENSING.md` | Dataset sources, generation method, and licensing | Datasets + licensing |
| `datasets/samples/` | Small representative samples of the training data | Dataset samples |
| `SHA256SUMS.txt` | SHA256 checksums of released model artifacts | SHA256 checksums |
| `generate_checksums.py` | Regenerates `SHA256SUMS.txt` from `model/` + `adapters/` | (reproducibility helper) |

## How to reproduce (organizer-facing)

```bash
# 1. Fetch the released GGUF (static URL, see ../download_model.sh)
./download_model.sh

# 2. Verify the artifact matches the published checksum
python provenance/generate_checksums.py --check

# 3. (Optional) rebuild from source: retrain, merge, and quantize
python training/train_qwen15b.py          # produces ./homa-qwen15b-merged
bash provenance/scripts/merge_and_quantize.sh homa-qwen15b-merged
```

## Before/after behavioural evidence

See [`../REPORT.md` → "Model Provenance"](../REPORT.md) for side-by-side
base-model vs. fine-tuned outputs on identity, actionability, and domain
grounding.
