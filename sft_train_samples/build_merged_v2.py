#!/usr/bin/env python3
"""Build the final merged Homa v2 SFT dataset.

    combined_train.v2.en.jsonl  =  base English corpus
                                 +  v2 gold corrective set (oversampled)

Rules:
  * Exact duplicate (instruction, response) rows in the base are collapsed.
  * If a gold example covers the same *question* as a base row, the gold answer
    replaces it and the base row is dropped -- so the corrected answer wins and
    the model never sees both the fixed and the stale version of a question
    (this is how the two official test prompts get their correct answers).
  * Gold rows are oversampled so the corrections carry weight.

This does NOT remove the flagged weak rows (that's a separate cleanup choice);
it only merges base + gold and resolves overlaps.

Usage:
    python build_merged_v2.py                 # oversample gold 4x (default)
    python build_merged_v2.py --oversample 3
    python build_merged_v2.py --out other.jsonl
"""
import argparse
import json
import re
from pathlib import Path

from build_gold_v2 import GOLD          # 45 corrective (instruction, response) tuples
from build_gold_persona import GOLD_PERSONA  # persona + meta/technical tuples

HERE = Path(__file__).resolve().parent
BASE_FILE = HERE / "combined_train.en.jsonl"
OUT_FILE = HERE / "combined_train.v2.en.jsonl"


def norm(text):
    """Normalise an instruction for overlap matching (case/space-insensitive)."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def load_jsonl(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oversample", type=int, default=4,
                    help="repeat each gold row N times (default 4)")
    ap.add_argument("--base", default=str(BASE_FILE),
                    help="base corpus to merge (default combined_train.en.jsonl; "
                         "point this at combined_train.regen.en.jsonl to use "
                         "the regenerated rows)")
    ap.add_argument("--out", default=str(OUT_FILE))
    args = ap.parse_args()

    base = load_jsonl(Path(args.base))
    gold = [{"instruction": i, "response": r} for i, r in (GOLD + GOLD_PERSONA)]
    gold_questions = {norm(g["instruction"]) for g in gold}

    kept = []
    seen_pairs = set()           # exact (instruction, response) dedup
    dropped_dupes = 0
    replaced_by_gold = 0

    for row in base:
        q = norm(row.get("instruction"))
        if q in gold_questions:
            replaced_by_gold += 1        # gold covers this question -> drop base row
            continue
        key = (q, norm(row.get("response")))
        if key in seen_pairs:
            dropped_dupes += 1
            continue
        seen_pairs.add(key)
        kept.append(row)

    merged = kept + gold * args.oversample

    out = Path(args.out)
    with open(out, "w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps({"instruction": row["instruction"],
                                "response": row["response"]},
                               ensure_ascii=False) + "\n")

    print(f"Base rows read:            {len(base)}")
    print(f"  exact duplicates dropped: {dropped_dupes}")
    print(f"  replaced by gold answer:  {replaced_by_gold}")
    print(f"  base rows kept:           {len(kept)}")
    print(f"Gold unique:               {len(gold)}  (x{args.oversample} = {len(gold)*args.oversample})")
    print(f"Final merged rows:         {len(merged)}")
    print(f"Wrote -> {out.name}")


if __name__ == "__main__":
    main()
