#!/usr/bin/env bash
# Download Gate 2 LoRA adapter weights (adapter_model.safetensors, ~147.7 MB)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_FILE="$HERE/adapter_model.safetensors"
URL="https://huggingface.co/fallback-ai/Homa-Qwen2.5-1.5B/resolve/d5af1a50c7f9c9959bf423071988a8ac36356c80/gate2_v1/adapter/adapter_model.safetensors"

if [[ -f "$TARGET_FILE" ]]; then
  echo "Adapter already present at $TARGET_FILE"
  exit 0
fi

echo "Downloading Gate 2 LoRA adapter weights from Hugging Face..."
if command -v curl > /dev/null 2>&1; then
  curl -L --fail --progress-bar -o "$TARGET_FILE" "$URL"
elif command -v wget > /dev/null 2>&1; then
  wget --show-progress -O "$TARGET_FILE" "$URL"
else
  echo "Error: neither curl nor wget found" >&2
  exit 1
fi

echo "Done: $TARGET_FILE"
