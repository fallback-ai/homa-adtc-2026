# Proof-of-Training & Model Provenance

This folder documents how `Homa-Qwen2.5-1.5B` was adapted from its base model,
so organizers can independently verify that the submission is a genuine
fine-tune (Gate 2: *Proof-of-Training* and *Model Provenance Disclosure*).

## Provenance summary

| Field | Value |
| --- | --- |
| Base model | [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) |
| Base model commit SHA | `d505c65db161245eb65b69ca18db70db545f06e3` |
| Fine-tuning method | LoRA SFT (PEFT), completion-only loss masking (TRL) |
| LoRA config | r=32, α=64, dropout=0.05, target = all linear projections (q,k,v,o,gate,up,down) |
| Training data | `sft_train_samples/combined_train_v5_clean.jsonl` (2,577 curated Nigerian agronomic Q&A rows, SHA256: `cb81966edce3df73984e992059215a7959957b1be2314923e5b2e83679529f0a`) |
| Hyperparameters | Learning rate 4e-5, cosine scheduler, 3 epochs, effective batch size 32, best eval loss 1.5598 |
| Merge | LoRA merged into base on CPU (`merge_and_unload`) → `homa-qwen15b-merged` |
| Quantization | GGUF F16 → Q4_K_M via llama.cpp (`convert_hf_to_gguf.py`, `llama-quantize`) |
| Runtime | llama.cpp / Ollama, ChatML template |

## Contents (Aligned with Official Template)

| Path | What it is | Gate 2 requirement |
| --- | --- | --- |
| [`train_sft.py`](./train_sft.py) | Exact standalone SFT training script for Gate 2 release | Training scripts / configs |
| [`training_log.txt`](./training_log.txt) | Complete step-by-step loss curve and evaluation telemetry | Loss / performance logs |
| [`dataset_info.md`](./dataset_info.md) | Dataset specifications, source URLs, and cryptographic checksums | Datasets + licensing |
| [`adapter_model.safetensors`](./adapter_model.safetensors) | Trained LoRA adapter weights (PEFT, native bfloat16, 70.48 MB) | Adapter weights |
| [`download_adapter.sh`](./download_adapter.sh) | Standalone fetch script for LoRA adapter weights | Adapter weights backup |
| [`adapter_config.json`](./adapter_config.json) | PEFT LoRA adapter configuration parameters | Adapter configuration |

> **Note on Adapter Weights & Double Safety Net:**
> - **Primary (In Repo):** [`adapter_model.safetensors`](./adapter_model.safetensors) is committed directly to the repository in native `bfloat16` format (70.48 MB, matching base model `Qwen2.5-1.5B`'s native precision) for zero-dependency offline access.
> - **Double Safety Net (FP32 on Hugging Face):** If an evaluator prefers the uncompressed 147.7 MB `float32` copy, it remains publicly hosted on Hugging Face and can be fetched via `bash provenance/download_adapter.sh`. Both formats merge identically into the base model.
| [`adapters/`](./adapters/README.md) | Detailed adapter architecture, target modules, and verification guide | Adapter documentation |
| [`logs/`](./logs/README.md) | Structured training loss logs ([`loss_logs.json`](./logs/loss_logs.json)) | Loss / performance logs |
| [`before_after_comparison.md`](./before_after_comparison.md) | Comprehensive 12-test before/after evaluation suite | Behavioral evidence |
| [`../training/homa-qwen2-5-1-5b-sft-v4.ipynb`](../training/homa-qwen2-5-1-5b-sft-v4.ipynb) | Interactive Kaggle SFT training, evaluation & quantization pipeline | Training notebooks |
| [`../training/homa-qwen2-5-1-5b-sft-v4-consolidate.ipynb`](../training/homa-qwen2-5-1-5b-sft-v4-consolidate.ipynb) | Multi-artifact consolidation and provenance export pipeline | Training notebooks |
| [`scripts/merge_and_quantize.sh`](./scripts/merge_and_quantize.sh) | Merge → F16 GGUF → Q4_K_M conversion pipeline | Merge / quantization scripts |
| [`datasets/DATA_LICENSING.md`](./datasets/DATA_LICENSING.md) | Comprehensive data licensing terms & RAG source attributions | Datasets + licensing |
| [`SHA256SUMS.txt`](./SHA256SUMS.txt) | SHA256 checksums of released model artifacts | SHA256 checksums |

## How to reproduce (organizer-facing)

```bash
# 1. Fetch the released GGUF (static URL, see ../download_model.sh)
./download_model.sh

# 2. Verify the artifact matches the published checksum
python provenance/generate_checksums.py --check

# 3. (Optional) inspect training logs or retrain:
cat provenance/logs/loss_logs.json
python training/train_sft_gate2.py
```

## Before/after behavioural evidence

See [`../REPORT.md` → "Model Provenance"](../REPORT.md) and [`before_after_comparison.md`](./before_after_comparison.md) for side-by-side
base-model vs. fine-tuned outputs on identity, actionability, and domain
grounding.
