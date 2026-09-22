#!/usr/bin/env bash
#
# Reproducible conversion pipeline for Homa-Qwen2.5-1.5B.
#
# The LoRA merge itself happens at the end of training/train_qwen15b.py
# (`merge_and_unload()` on CPU -> ./homa-qwen15b-merged). This script takes that
# merged HF model directory and produces the two released GGUF artifacts:
#
#     homa-qwen15b-f16.gguf   (F16 source)
#     homa-qwen15b-q4.gguf    (Q4_K_M, the submission candidate)
#
# Requirements: a local llama.cpp checkout (for convert_hf_to_gguf.py and the
# llama-quantize binary). Set LLAMA_CPP to its path, or place it at ../llama.cpp.
#
# Usage:
#   bash provenance/scripts/merge_and_quantize.sh [MERGED_DIR] [OUT_DIR]
#
set -euo pipefail

MERGED_DIR="${1:-homa-qwen15b-merged}"
OUT_DIR="${2:-model}"
LLAMA_CPP="${LLAMA_CPP:-../llama.cpp}"

F16="$OUT_DIR/homa-qwen15b-f16.gguf"
Q4="$OUT_DIR/homa-qwen15b-q4.gguf"

if [[ ! -d "$MERGED_DIR" ]]; then
  echo "error: merged model dir not found: $MERGED_DIR" >&2
  echo "       run training/train_qwen15b.py first (it writes ./homa-qwen15b-merged)." >&2
  exit 1
fi
if [[ ! -d "$LLAMA_CPP" ]]; then
  echo "error: llama.cpp not found at '$LLAMA_CPP'. Set LLAMA_CPP=/path/to/llama.cpp" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "Step 1/2: convert merged HF model -> F16 GGUF"
python "$LLAMA_CPP/convert_hf_to_gguf.py" "$MERGED_DIR" \
  --outfile "$F16" \
  --outtype f16

echo "Step 2/2: quantize F16 GGUF -> Q4_K_M"
# Prefer an installed binary; fall back to the build tree.
if command -v llama-quantize >/dev/null 2>&1; then
  llama-quantize "$F16" "$Q4" Q4_K_M
else
  "$LLAMA_CPP/build/bin/llama-quantize" "$F16" "$Q4" Q4_K_M
fi

echo "done:"
echo "  $F16"
echo "  $Q4"
echo
echo "Next: refresh checksums ->  python provenance/generate_checksums.py"
