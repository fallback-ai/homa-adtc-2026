# Gate 2 Training & Loss Logs

This directory contains the training telemetry and loss logs recorded during the Supervised Fine-Tuning (SFT) run of **Homa-Qwen2.5-1.5B** on the Gate 2 dataset (`combined_train_v5_clean.jsonl`).

## Telemetry Summary

The training metrics are tracked in [`loss_logs.json`](./loss_logs.json).

| Metric | Value |
| :--- | :--- |
| **Total Training Steps** | 219 steps |
| **Epochs** | 3 epochs |
| **Effective Batch Size** | 32 (batch size 2 × 4 gradient accumulation steps × 4 devices/grad sync) |
| **Peak Learning Rate** | $4 \times 10^{-5}$ |
| **LR Scheduler** | Cosine with linear warmup |
| **Initial Training Loss** | ~2.18 |
| **Final Validation Loss** | **1.5598** |
| **Final Token Accuracy** | **61.47%** |

---

## Checkpoint Progression

Below is the step-by-step evaluation progression exported directly from the trainer:

| Step | Epoch Equivalent | Training Loss | Validation Loss | Token Accuracy |
| :---: | :---: | :---: | :---: | :---: |
| **50** | ~0.68 | 1.7352 | 1.6711 | 59.37% |
| **100** | ~1.37 | 1.5471 | 1.6031 | 60.71% |
| **150** | ~2.05 | 1.4740 | 1.5667 | 61.24% |
| **200** | ~2.74 | 1.3899 | 1.5603 | 61.42% |
| **219** (Final) | 3.00 | **1.3899** | **1.5598** | **61.47%** |

---

## Log Traceability

To verify or plot the loss curves directly in Python:

```python
import json

with open("provenance/logs/loss_logs.json") as f:
    logs = json.load(f)

print(f"Best Eval Loss: {logs['best_eval_loss']}")
for entry in logs["log_history"]:
    print(f"Step {entry['step']:3d} | Train: {entry['training_loss']:.4f} | Val: {entry['validation_loss']:.4f} | Acc: {entry['mean_token_accuracy']:.2%}")
```
