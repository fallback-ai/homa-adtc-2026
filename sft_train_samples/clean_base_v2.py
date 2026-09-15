#!/usr/bin/env python3
"""Tier-1 hygiene pass over the base English SFT corpus.

Deterministic, no API. Fixes four issues found in combined_train.en.jsonl:

  1. Decontaminate RAG-format rows: instructions shaped as
     "Retrieved Passages: ... Passage N: ... Question: <q>" are reduced to just
     <q>. The response is already clean. This matters because the model is
     SCORED STANDALONE (no RAG), so passage scaffolding in the input is off-
     distribution and trains the "Passage N" leakage that clean_response() has
     to strip at runtime.
  2. Reformat fragment instructions ("Wilting of cassava leaves") into natural
     farmer questions.
  3. Normalize typography (em/en dashes, curly quotes -> ASCII). Keeps
     meaningful symbols (degree, naira, division, approx).
  4. Instruction-level dedup: collapse rows that share a question (after 1-3),
     keeping the single most actionable answer. Resolves contradictory
     same-question/different-answer rows.

Output: combined_train.clean.en.jsonl, ready for:
    python build_merged_v2.py --base combined_train.clean.en.jsonl

Usage:
    python clean_base_v2.py                 # write cleaned base + report
    python clean_base_v2.py --no-reform     # skip fragment reformatting
"""
import argparse
import json
import re
from pathlib import Path

from audit_actionability import audit_row

HERE = Path(__file__).resolve().parent
BASE_FILE = HERE / "combined_train.en.jsonl"
OUT_FILE = HERE / "combined_train.clean.en.jsonl"

# ---- 1. decontamination -----------------------------------------------------
_QUESTION_RE = re.compile(r"Question:\s*(.+)\Z", re.S)
_RAG_RE = re.compile(r"Retrieved Passages:|Passage \d+:")


def decontaminate(instruction):
    if not _RAG_RE.search(instruction):
        return instruction, False
    m = _QUESTION_RE.search(instruction)
    if m:
        return m.group(1).strip(), True
    # No Question marker: strip the passage scaffolding lines defensively.
    cleaned = _RAG_RE.sub("", instruction).strip()
    return cleaned, True


# ---- 2. fragment reformatting ----------------------------------------------
_GERUND = {"choosing": "choose", "identifying": "identify", "applying": "apply",
           "determining": "determine", "protecting": "protect", "managing": "manage",
           "improving": "improve", "estimating": "estimate", "controlling": "control",
           "preventing": "prevent", "treating": "treat", "storing": "store",
           "selecting": "select", "feeding": "feed"}
_IMPERATIVE = {"determine", "identify", "choose", "apply", "protect", "manage",
               "improve", "estimate", "control", "prevent", "treat", "store",
               "select", "feed"}
_ASK = {"describe", "explain", "list", "name"}


def reform_fragment(instruction):
    """Turn a title/topic fragment into a natural question. Returns (text, changed)."""
    s = instruction.strip()
    if "?" in s or len(s.split()) >= 7:
        return instruction, False
    s = s.rstrip(".")
    words = s.split()
    if not words:
        return instruction, False
    first = words[0].lower()
    rest = " ".join(words[1:]).lower()
    if first in _GERUND and rest:
        return f"How do I {_GERUND[first]} {rest}?", True
    if first in _ASK and rest:
        return f"Can you {first} {rest}?", True
    if first in _IMPERATIVE and rest:
        return f"How do I {first} {rest}?", True
    return f"What should I know about {s.lower()} on my farm?", True


# ---- 3. typography ----------------------------------------------------------
_TYPO = {
    "—": "-", "–": "-",          # em / en dash
    "’": "'", "‘": "'",          # curly single quotes
    "“": '"', "”": '"',          # curly double quotes
    "…": "...", " ": " ",        # ellipsis, nbsp
}
_TYPO_RE = re.compile("|".join(map(re.escape, _TYPO)))


def normalize_typography(text):
    if not _TYPO_RE.search(text):
        return text, False
    return _TYPO_RE.sub(lambda m: _TYPO[m.group()], text), True


# ---- 4. dedup selection -----------------------------------------------------
def _norm(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def answer_score(response):
    """Higher is better: actionable (has a rate) first, then longer."""
    actionable = 0 if "no-rate" in audit_row({"instruction": "x", "response": response}) else 1
    return (actionable, len(response or ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-reform", action="store_true",
                    help="skip fragment reformatting (step 2)")
    ap.add_argument("--out", default=str(OUT_FILE))
    args = ap.parse_args()

    base = [json.loads(l) for l in BASE_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    stats = dict(decontaminated=0, reformed=0, typo_rows=0)
    processed = []
    for row in base:
        instr = row["instruction"]
        resp = row.get("response", "")

        instr, dc = decontaminate(instr)
        if dc:
            stats["decontaminated"] += 1
        if not args.no_reform:
            instr, rf = reform_fragment(instr)
            if rf:
                stats["reformed"] += 1

        instr, t1 = normalize_typography(instr)
        resp, t2 = normalize_typography(resp)
        if t1 or t2:
            stats["typo_rows"] += 1

        processed.append({"instruction": instr, "response": resp})

    # Instruction-level dedup, keeping the best answer, preserving first-seen order.
    order = []
    best = {}
    for row in processed:
        key = _norm(row["instruction"])
        if key not in best:
            best[key] = row
            order.append(key)
        else:
            if answer_score(row["response"]) > answer_score(best[key]["response"]):
                best[key] = row

    collapsed = len(processed) - len(best)
    cleaned = [best[k] for k in order]

    Path(args.out).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in cleaned) + "\n",
        encoding="utf-8")

    print(f"Base rows read:            {len(base)}")
    print(f"  RAG rows decontaminated: {stats['decontaminated']}")
    print(f"  fragments reformatted:   {stats['reformed']}")
    print(f"  rows typography-fixed:   {stats['typo_rows']}")
    print(f"  duplicate rows collapsed:{collapsed}  (kept most actionable answer)")
    print(f"Cleaned unique rows:       {len(cleaned)}")
    print(f"Wrote -> {Path(args.out).name}")
    print("\nNext:  python build_merged_v2.py --base "
          f"{Path(args.out).name}")


if __name__ == "__main__":
    main()
