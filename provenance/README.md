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

## Contents

| Path | What it is | Gate 2 requirement |
| --- | --- | --- |
| [`adapters/`](./adapters/README.md) | LoRA adapter specification (`adapter_config.json`) & weights on HF | Adapter weights |
| [`../training/train_sft_gate2.py`](../training/train_sft_gate2.py) | The exact SFT training script used for Gate 2 release | Training scripts / configs |
| [`../training/train_qwen15b.py`](../training/train_qwen15b.py) | Standalone SFT + merge pipeline script | Training scripts / configs |
| [`../training/train_gemma1b.py`](../training/train_gemma1b.py) | Earlier research-track training script | Training scripts / configs |
| [`scripts/merge_and_quantize.sh`](./scripts/merge_and_quantize.sh) | Merge → F16 GGUF → Q4_K_M conversion pipeline | Merge / quantization scripts |
| [`logs/`](./logs/README.md) | Training loss / eval telemetry exported from run ([`loss_logs.json`](./logs/loss_logs.json)) | Loss / performance logs |
| [`before_after_comparison.md`](./before_after_comparison.md) | Comprehensive 12-test before/after evaluation suite | Behavioral evidence |
| [`datasets/DATA_LICENSING.md`](./datasets/DATA_LICENSING.md) | Dataset sources, generation method, and licensing | Datasets + licensing |
| [`datasets/samples/`](./datasets/samples/) | Small representative samples of the training data | Dataset samples |
| [`SHA256SUMS.txt`](./SHA256SUMS.txt) | SHA256 checksums of released model artifacts | SHA256 checksums |
| [`generate_checksums.py`](./generate_checksums.py) | Regenerates `SHA256SUMS.txt` from `model/` + `adapters/` | (reproducibility helper) |

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
