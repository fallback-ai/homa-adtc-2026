#!/usr/bin/env python3
"""Flag low-quality rows in a Homa SFT JSONL file.

Targets the Round-1 judge findings (see RESPONSE_STYLE.md):
  * non-actionable input advice: talks about fertilizer/spray/treatment but
    gives no product + rate (no number with a unit).
  * "consult an expert" as the whole answer (deflection instead of advice).
  * identity leaks: wrong creator, or a generic-assistant persona.

This is a heuristic triage aid, not a grader. Use it to pick rows to regenerate.

Usage:
    python audit_actionability.py [FILE.jsonl] [--out flagged.jsonl] [--show 20]
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "combined_train.en.jsonl"

# Words that promise an input/treatment the farmer must buy or apply.
INPUT_WORDS = re.compile(
    r"\b(fertiliz|fertilis|nitrogen|urea|npk|potash|potassium|phosphor|"
    r"insecticide|pesticide|fungicide|herbicide|spray|apply|dosage|dose|"
    r"vaccinat|dewormer|acaricide)\w*", re.IGNORECASE)

# A concrete rate: a number followed by (or joined to) a real unit. Units may be
# plural and may carry a "/ha", "/L", "/plant" style denominator, so answers that
# say "2 bags/ha", "1-2 tonnes/ha" or "200 micrograms/kg" count as actionable.
RATE = re.compile(
    r"\d+(\.\d+)?\s?-?\s?\d*\.?\d*\s?"
    r"(kg|g|mg|ml|l|litre|liter|tonne|ton|ha|hectare|bag|sachet|"
    r"micrograms?|mcg|%|cm|mm|ppm)s?"
    r"(\s?/\s?(ha|hectare|l|litre|plant|animal|bird|head|kg))?\b",
    re.IGNORECASE)

DEFLECTION = re.compile(
    r"(consult|contact|send .*sample|take .*sample|visit).{0,40}"
    r"(expert|extension|agronomist|specialist|research institute|office|vet)",
    re.IGNORECASE)

IDENTITY_LEAK = re.compile(
    r"(created by openai|made by openai|i am chatgpt|as an ai language model|"
    r"i am not programmed|text summarization|i cannot browse)", re.IGNORECASE)


def audit_row(row):
    """Return a list of issue tags for one {instruction, response} row."""
    resp = (row.get("response") or "")
    issues = []

    promises_input = bool(INPUT_WORDS.search(resp))
    has_rate = bool(RATE.search(resp))
    if promises_input and not has_rate:
        issues.append("no-rate")

    # Deflection dominates when the response is short and mostly "ask an expert".
    if DEFLECTION.search(resp) and (len(resp) < 400 or not has_rate):
        issues.append("deflection")

    if IDENTITY_LEAK.search(resp):
        issues.append("identity-leak")

    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", nargs="?", default=str(DEFAULT_FILE))
    ap.add_argument("--out", help="write flagged rows (+issues) to this JSONL")
    ap.add_argument("--show", type=int, default=10,
                    help="print this many flagged examples")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[error] file not found: {path}")
        return 1

    total = 0
    flagged = []
    counts = {"no-rate": 0, "deflection": 0, "identity-leak": 0}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        total += 1
        row = json.loads(line)
        issues = audit_row(row)
        if issues:
            for tag in issues:
                counts[tag] += 1
            flagged.append({**row, "_issues": issues})

    print(f"Audited {total} rows from {path.name}")
    print(f"  flagged:       {len(flagged)} ({100*len(flagged)/max(total,1):.1f}%)")
    print(f"  no-rate:       {counts['no-rate']}  (input advice with no product+rate)")
    print(f"  deflection:    {counts['deflection']}  (mostly 'ask an expert')")
    print(f"  identity-leak: {counts['identity-leak']}")

    if args.out and flagged:
        Path(args.out).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in flagged) + "\n",
            encoding="utf-8")
        print(f"  wrote flagged rows -> {args.out}")

    for r in flagged[:args.show]:
        q = r["instruction"][:90].replace("\n", " ")
        print(f"\n  [{','.join(r['_issues'])}] {q}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
