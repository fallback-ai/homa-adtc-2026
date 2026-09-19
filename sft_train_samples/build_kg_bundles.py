#!/usr/bin/env python3
"""Curate KG stage-4 paths into grounded evidence bundles for SFT synthesis.

Input:  ../kg_pipeline_checkpoints/stage4_traversed_paths.jsonl  (221 paths)
Output: kg_bundles.jsonl  (one clean, groundable bundle per usable path)

The stage-4 file is the KG-traversal artifact from the semifinal handover
(kg_sft_handover/README.md). Its structured fields (soil_requirements,
fertilizers, agroecological_zones, ...) are extremely noisy -- massively
duplicated and full of junk tokens ("not_too_saline" x6, "favorable" x50,
"not_explicitly_stated" x140). The trustworthy signal is:

  * grounding_sentences : verbatim source text (this is the evidence)
  * host                : the crop / animal / product the path is about
  * path_type           : agronomic_practice | postharvest_processing |
                          livestock_husbandry
  * source_docs         : provenance

So this script IGNORES the noisy structured fields and keeps only the verbatim
grounding sentences, then applies a strict curation filter so that downstream
synthesis (build via an LLM or a coding assistant, per the handover's Method A /
Method B) starts from clean, actionable, on-topic evidence rather than the raw
noise. This directly protects against the Round-1 non-actionability finding.

Curation rules
--------------
1. DROP paths with zero grounding sentences (nothing to ground on). 34 of 221
   -- almost all livestock_husbandry paths -- are empty.
2. DROP junk hosts: author names ("Aliyu, S.U."), institutions ("NAERLS
   management", "Ahmadu Bello University"), countries/agro-zones ("Kenya",
   "Sahel savanna"), and abstract nouns ("supportive policies", "Crop XYZ",
   "Interventions & Rates"). Keep only hosts that are a real crop, animal or
   farm product a Nigerian farmer would ask about (HOST_CANON allow-list).
3. Canonicalize host case/variants (Sorghum/sorghum -> sorghum,
   Soya-beans/soybean -> soybean, groundnut varieties -> groundnut).
4. Dedup grounding sentences (exact, after whitespace normalization); drop
   fragments (< 6 words) and near-duplicate prefixes (one sentence that is a
   strict prefix of a longer kept one). Sort ACTIONABLE sentences first
   (those carrying a number/unit or an imperative verb), cap at MAX_EVID.
5. For postharvest paths, carry the processing_step (2nd path_key segment) so
   the question can be framed around the specific process.

The bundle is NOT training data -- it is the synthesis input. See
build ... -> sft_pairs_kg_claude.jsonl for the synthesized pairs.
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "kg_pipeline_checkpoints" / "stage4_traversed_paths.jsonl"
OUT = HERE / "kg_bundles.jsonl"

# Real crop/animal/product hosts -> canonical display name. Everything not in
# here (authors, institutions, countries, abstractions, agribusiness stats) is
# dropped. Keys are matched case-insensitively against the raw host string;
# the first key that is a whole-token match wins.
HOST_CANON = {
    # field / tree crops
    "cassava": "cassava", "sorghum": "sorghum", "cowpea": "cowpea",
    "onion": "onion", "rice": "rice", "tomato": "tomato", "tomatoes": "tomato",
    "sweet_potato": "sweet potato", "sweet potato": "sweet potato",
    "okra": "okra", "millet": "millet", "pearl millet": "millet",
    "cocoa": "cocoa", "cotton": "cotton", "garlic": "garlic",
    "groundnut": "groundnut", "groundnuts": "groundnut", "peanuts": "groundnut",
    "pepper": "pepper", "yam": "yam", "maize": "maize", "wheat": "wheat",
    "soybean": "soybean", "soya-beans": "soybean", "soya beans": "soybean",
    "pigeonpeas": "pigeon pea", "pigeon pea": "pigeon pea",
    "pumpkin": "pumpkin", "spinach": "spinach", "beans": "beans",
    "citrus": "citrus", "mango": "mango", "para rubber plant": "rubber",
    "creeping sorghum": "sorghum", "cereals": "cereals",
    "green leafy vegetables": "leafy vegetables", "vegetables": "vegetables",
    "seeds": "seed", "seed umbels": "seed", "umbels": "seed",
    # livestock (only a handful carry grounding)
    "bulls": "cattle", "cattle, sheep and goat": "small ruminants",
    "rams": "sheep", "lambs": "sheep", "sheep or goat": "small ruminants",
    "sheep and goats": "small ruminants", "bucks": "goats", "swine": "pigs",
    "piglets": "pigs", "fish": "fish", "turkeys": "turkey",
    "guinea fowls": "guinea fowl",
}
# groundnut-variety hosts (SAMNUT/ICGV codes) fold into groundnut
VARIETY_RE = re.compile(r"\b(samnut|icgv)\b", re.I)

MAX_EVID = 14
MIN_WORDS = 6
NUM_RE = re.compile(r"\d")
UNIT_RE = re.compile(r"\b(kg|g|mg|ml|l|litre|liter|cm|mm|m|ha|hectare|"
                     r"tonne|ton|t/ha|wap|was|week|day|month|%|percent|"
                     r"bag|seed|plant|row|degree|pH)\b", re.I)
IMPER_RE = re.compile(r"\b(apply|spray|plant|sow|use|mix|add|store|dry|treat|"
                      r"harvest|weed|space|dip|soak|dust|feed|control|remove|"
                      r"select|dry|keep|avoid|ensure|place|cover|thin|"
                      r"transplant|prune|ridge|band|drench|vaccinate)\b", re.I)


def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip())


def canon_host(raw):
    r = norm(raw).lower().rstrip(".")
    if VARIETY_RE.search(r):
        return "groundnut"
    # whole-token match against the allow-list keys
    for key, disp in HOST_CANON.items():
        if re.search(rf"(^|\W){re.escape(key)}($|\W)", r):
            return disp
    return None


def clean_evidence(sentences):
    seen, kept = set(), []
    for s in sentences:
        s = norm(s)
        if not s or len(s.split()) < MIN_WORDS:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        kept.append(s)
    # drop sentences that are a strict prefix of a longer kept one
    kept.sort(key=len)
    pruned = []
    for i, s in enumerate(kept):
        if any(other.lower().startswith(s.lower()) for other in kept[i + 1:]):
            continue
        pruned.append(s)
    # actionable first: has a number+unit, or an imperative verb
    def score(s):
        return ((1 if NUM_RE.search(s) and UNIT_RE.search(s) else 0)
                + (1 if IMPER_RE.search(s) else 0))
    pruned.sort(key=score, reverse=True)
    return pruned[:MAX_EVID]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    rows = [json.loads(l) for l in Path(args.src).read_text(encoding="utf-8").splitlines() if l.strip()]
    bundles, dropped_empty, dropped_host = [], 0, 0
    for r in rows:
        gs = r.get("grounding_sentences") or []
        if not gs:
            dropped_empty += 1
            continue
        host = canon_host(r.get("host"))
        if not host:
            dropped_host += 1
            continue
        evid = clean_evidence(gs)
        if not evid:
            dropped_empty += 1
            continue
        pk = r.get("path_key", "")
        step = pk.split("|", 2)[2] if r.get("path_type") == "postharvest_processing" and pk.count("|") >= 2 else None
        src = (r.get("source_docs") or [None])[0]
        bundles.append({
            "path_key": pk,
            "host": host,
            "path_type": r.get("path_type"),
            "processing_step": step,
            "n_evidence": len(evid),
            "evidence": evid,
            "source_doc": Path(src).name if src else None,
        })

    # richest bundles first (more evidence -> can synthesize more/better pairs)
    bundles.sort(key=lambda b: (-b["n_evidence"], b["host"]))
    Path(args.out).write_text(
        "\n".join(json.dumps(b, ensure_ascii=False) for b in bundles) + "\n",
        encoding="utf-8")

    print(f"input paths:            {len(rows)}")
    print(f"  dropped (no grounding): {dropped_empty}")
    print(f"  dropped (junk host):    {dropped_host}")
    print(f"usable bundles:         {len(bundles)} -> {Path(args.out).name}")
    import collections
    by_type = collections.Counter(b["path_type"] for b in bundles)
    for k, v in by_type.most_common():
        print(f"    {k:24s} {v}")
    print(f"  distinct hosts: {len(set(b['host'] for b in bundles))}")


if __name__ == "__main__":
    main()
