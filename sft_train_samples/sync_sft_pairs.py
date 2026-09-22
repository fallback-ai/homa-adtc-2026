#!/usr/bin/env python3
"""Sync and merge verified Homa SFT datasets:
1. homa_kg_stage5_sophisticated_sft_clean.jsonl (73 pairs from Stage 5 KG)
2. homa_direct_chunk_sft_clean.jsonl (179 pairs from Direct Chunk Synthesis)

Validates schema, strips whitespace, performs exact and near-duplicate checks,
and outputs a unified, pristine gold corpus:
- sft_train_samples/homa_corpus_sft_gold_clean.jsonl (252 unique pairs)
"""
import json
import re
import difflib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

F_KG = HERE / "homa_kg_stage5_sophisticated_sft_clean.jsonl"
F_DC_SRC = REPO_ROOT / "sft_direct_chunks" / "homa_direct_chunk_sft_clean.jsonl"
F_DC_COPY = HERE / "homa_direct_chunk_sft_clean.jsonl"
F_UNIFIED = HERE / "homa_corpus_sft_gold_clean.jsonl"

def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())

def load_clean_pairs(p: Path):
    records = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                inst = data.get("instruction", "").strip()
                resp = data.get("response", "").strip()
                if inst and resp:
                    records.append({"instruction": inst, "response": resp})
    return records

def main():
    if not F_KG.exists():
        raise SystemExit(f"Missing KG gold dataset: {F_KG}")
    if not F_DC_SRC.exists() and not F_DC_COPY.exists():
        raise SystemExit(f"Missing Direct Chunk dataset in {F_DC_SRC} or {F_DC_COPY}")

    dc_path = F_DC_SRC if F_DC_SRC.exists() else F_DC_COPY

    kg_pairs = load_clean_pairs(F_KG)
    dc_pairs = load_clean_pairs(dc_path)

    print(f"Loaded {len(kg_pairs)} pairs from KG Stage 5: {F_KG.name}")
    print(f"Loaded {len(dc_pairs)} pairs from Direct Chunk SFT: {dc_path.name}")

    # Copy direct chunk dataset to sft_train_samples for local consistency
    if F_DC_SRC.exists():
        F_DC_COPY.write_text(F_DC_SRC.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Synchronized direct chunk dataset into: {F_DC_COPY.name}")

    # Merge with exact-duplicate and near-duplicate protection
    seen_instructions = set()
    unified = []
    exact_dupes = 0

    for r in kg_pairs + dc_pairs:
        k = norm(r["instruction"])
        if k in seen_instructions:
            exact_dupes += 1
            continue
        seen_instructions.add(k)
        unified.append(r)

    print(f"Exact duplicate instructions filtered: {exact_dupes}")
    print(f"Total unified unique gold SFT pairs: {len(unified)}")

    # Near duplicate check (>0.85 similarity)
    near_dupes = []
    for i in range(len(unified)):
        ni = norm(unified[i]["instruction"])
        words_i = set(ni.split())
        for j in range(i + 1, len(unified)):
            nj = norm(unified[j]["instruction"])
            words_j = set(nj.split())
            if len(words_i & words_j) / max(1, len(words_i | words_j)) > 0.6:
                sim = difflib.SequenceMatcher(None, ni, nj).ratio()
                if sim > 0.85:
                    near_dupes.append((sim, i, j, unified[i]["instruction"], unified[j]["instruction"]))

    print(f"Near-duplicate pairs flagged (>0.85 similarity): {len(near_dupes)}")
    for sim, i, j, s1, s2 in near_dupes:
        print(f"  Sim: {sim:.3f}\n    #{i}: {s1[:70]}...\n    #{j}: {s2[:70]}...")

    # Write unified dataset
    with open(F_UNIFIED, "w", encoding="utf-8") as out:
        for r in unified:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nSUCCESS! Unified gold dataset written to: {F_UNIFIED.name} ({len(unified)} records)")

if __name__ == "__main__":
    main()
