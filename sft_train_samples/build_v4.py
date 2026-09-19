#!/usr/bin/env python3
"""Build the v4 Homa SFT corpus: base + three external sources, cleaned + merged.

Same pipeline as build_v3.py, with one more external source added:

    combined_train.en.jsonl                 (raw base corpus, 1,905 rows)
  + external_kisanvaani.en.jsonl            (filtered KisanVaani QA, Apache-2.0)
  + external_nigeria_facts.en.jsonl         (aggregated Nigeria planting facts, MIT)
  + external_iita.en.jsonl                  (curated IITA-report QA, CC-BY / CC-BY-SA)
        |
        v  concat + exact-pair dedup
    combined_train.aug4.en.jsonl
        |
        v  clean_base_v2.py
    combined_train.aug4.clean.en.jsonl
        |
        v  build_merged_v2.py  (+ gold corrective set, oversampled x4)
    combined_train.v4.en.jsonl              <- train on this

Regenerate the external sources first:
    python build_external_kisanvaani.py --raw kisanvaani_raw.jsonl
    python build_external_nigeria_facts.py
    python build_external_iita.py
Then:
    python build_v4.py
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "combined_train.en.jsonl"
EXTERNALS = [HERE / "external_kisanvaani.en.jsonl",
             HERE / "external_nigeria_facts.en.jsonl",
             HERE / "external_iita.en.jsonl"]
AUG = HERE / "combined_train.aug4.en.jsonl"
AUG_CLEAN = HERE / "combined_train.aug4.clean.en.jsonl"
OUT = HERE / "combined_train.v4.en.jsonl"


def load(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oversample", type=int, default=4,
                    help="gold oversampling passed to build_merged_v2 (default 4)")
    args = ap.parse_args()

    rows = load(BASE)
    n_base = len(rows)
    added = {}
    for ext in EXTERNALS:
        if not ext.exists():
            raise SystemExit(f"missing external source: {ext.name} "
                             f"(run its build_external_*.py first)")
        added[ext.name] = load(ext)
        rows += added[ext.name]

    seen, deduped = set(), []
    for r in rows:
        key = (norm(r.get("instruction")), norm(r.get("response")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"instruction": r["instruction"], "response": r["response"]})
    AUG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in deduped) + "\n",
                   encoding="utf-8")

    print(f"base rows:                 {n_base}")
    for name, r in added.items():
        print(f"  + {name:34s} {len(r)}")
    print(f"augmented base (deduped):  {len(deduped)} -> {AUG.name}\n")

    py = sys.executable
    subprocess.run([py, str(HERE / "clean_base_v2.py"),
                    "--base", str(AUG), "--out", str(AUG_CLEAN)], check=True, cwd=HERE)
    print()
    subprocess.run([py, str(HERE / "build_merged_v2.py"),
                    "--base", str(AUG_CLEAN), "--out", str(OUT),
                    "--oversample", str(args.oversample)], check=True, cwd=HERE)
    print(f"\nv4 corpus ready -> {OUT.name}")


if __name__ == "__main__":
    main()
