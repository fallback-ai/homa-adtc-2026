# LoRA Adapter Weights

Place the trained LoRA adapter here so organizers can verify the fine-tune
independently of the merged/quantized release:

- `adapter_model.safetensors` — the LoRA delta weights
- `adapter_config.json` — the PEFT config (r=32, α=64, target modules, base model)

These come from `training/train_qwen15b.py`. When `FULL_FT = False` (the default),
save the adapter before merging, e.g.:

```python
trainer.model.save_pretrained("homa-qwen15b-lora")   # adapter only
```

then copy `adapter_model.safetensors` and `adapter_config.json` into this folder.

A 1.5B r=32 all-linear adapter is small enough to commit (tens of MB). If it
exceeds a size you want in git, host it on the team HF repo and record its
SHA256 in `../SHA256SUMS.txt` and the URL in `../README.md` instead.

After adding the files, run:

```bash
python provenance/generate_checksums.py
```
