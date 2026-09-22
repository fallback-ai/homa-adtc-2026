#!/usr/bin/env python3
"""Regenerate the flagged (non-actionable) base SFT rows into the v2 style.

Pipeline:
  1. emit   -> select flagged rows and write the regeneration prompts (offline;
               use this to feed your own Gemini/Claude batch pipeline).
  2. run    -> call Claude to rewrite each flagged row (Anthropic Batch API by
               default; --sync for one call at a time). Resumable. Each rewrite
               is re-checked with the actionability audit.
  3. apply  -> splice the rewrites back over the flagged rows and write
               combined_train.regen.en.jsonl, then rebuild the merged set:
                   python build_merged_v2.py --base combined_train.regen.en.jsonl

custom_id is "r<line-index>" into combined_train.en.jsonl, so rewrites map back
to the exact source row.

Examples:
    python regenerate_flagged.py emit                       # -> regen_prompts.jsonl
    python regenerate_flagged.py run                        # Batch API, opus-5
    python regenerate_flagged.py run --sync --model claude-sonnet-5
    python regenerate_flagged.py run --batch-id msgbatch_123  # resume ingest
    python regenerate_flagged.py apply
"""
import argparse
import json
import sys
import time
from pathlib import Path

from audit_actionability import audit_row

HERE = Path(__file__).resolve().parent
BASE_FILE = HERE / "combined_train.en.jsonl"
STYLE_FILE = HERE / "RESPONSE_STYLE.md"
PROMPTS_FILE = HERE / "regen_prompts.jsonl"
REGEN_OUT = HERE / "regen_out.jsonl"
REGEN_BASE = HERE / "combined_train.regen.en.jsonl"

DEFAULT_MODEL = "claude-opus-5"     # per Anthropic guidance; override with --model
MAX_TOKENS = 1024

SYS_INSTRUCTIONS = """You are rewriting one training answer for Homa, an offline \
agricultural assistant for farmers in Nigeria. You are given a farmer's question \
and a weak existing answer. Rewrite ONLY the answer so it follows Homa's response \
style below. Keep the diagnosis correct; if the existing answer's diagnosis is \
wrong, fix it. Make treatment advice actionable: name a concrete product, a real \
rate (kg/ha, g or ml per litre, bags/ha, or per-plant/animal), the timing, the \
method, and a safety note to follow the label and pre-harvest interval. Do not \
invent false precision -- give realistic ranges and defer to the label/extension \
for the exact figure. Reply with the rewritten answer text ONLY -- no preamble, \
no headings like "Answer:", no restating the question.

--- HOMA RESPONSE STYLE ---
{style}
"""


def load_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def flagged_rows():
    """Return [(custom_id, index, row, issues)] for each flagged base row."""
    base = load_jsonl(BASE_FILE)
    out = []
    for i, row in enumerate(base):
        issues = audit_row(row)
        if issues:
            out.append((f"r{i}", i, row, issues))
    return out


def build_system():
    style = STYLE_FILE.read_text(encoding="utf-8")
    return SYS_INSTRUCTIONS.format(style=style)


def user_content(row):
    return (f"Farmer's question:\n{row['instruction']}\n\n"
            f"Weak existing answer to replace:\n{row.get('response', '')}")


# ----------------------------------------------------------------------------
def cmd_emit(args):
    system = build_system()
    flagged = flagged_rows()
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        for cid, idx, row, issues in flagged:
            f.write(json.dumps({
                "custom_id": cid,
                "index": idx,
                "issues": issues,
                "instruction": row["instruction"],
                "original_response": row.get("response", ""),
                "system": system,
                "user": user_content(row),
            }, ensure_ascii=False) + "\n")
    print(f"Wrote {len(flagged)} regeneration prompts -> {PROMPTS_FILE.name}")
    print("Feed these to your LLM pipeline, or run:  python regenerate_flagged.py run")


# ----------------------------------------------------------------------------
def _write_result(fh, cid, index, instruction, response):
    still = audit_row({"instruction": instruction, "response": response})
    fh.write(json.dumps({
        "custom_id": cid,
        "index": index,
        "instruction": instruction,
        "response": response.strip(),
        "still_flagged": still,
    }, ensure_ascii=False) + "\n")
    fh.flush()
    return still


def _done_ids():
    if not REGEN_OUT.exists():
        return set()
    return {json.loads(l)["custom_id"]
            for l in REGEN_OUT.read_text(encoding="utf-8").splitlines() if l.strip()}


def cmd_run(args):
    try:
        import anthropic
    except ImportError:
        print("[error] pip install anthropic  (needed for `run`; `emit` works without it)")
        return 1

    client = anthropic.Anthropic()
    system = build_system()
    flagged = flagged_rows()
    by_id = {cid: (idx, row) for cid, idx, row, _ in flagged}

    if args.sync:
        return _run_sync(client, args, system, flagged)
    return _run_batch(client, args, system, flagged, by_id)


def _run_sync(client, args, system, flagged):
    done = _done_ids()
    todo = [(c, i, r) for c, i, r, _ in flagged if c not in done]
    print(f"Sync run: {len(todo)} to do, {len(done)} already done, model={args.model}")
    still_count = 0
    with open(REGEN_OUT, "a", encoding="utf-8") as fh:
        for n, (cid, idx, row) in enumerate(todo, 1):
            try:
                msg = client.messages.create(
                    model=args.model,
                    max_tokens=MAX_TOKENS,
                    output_config={"effort": "low"},
                    system=system,
                    messages=[{"role": "user", "content": user_content(row)}],
                )
                text = "".join(b.text for b in msg.content if b.type == "text")
            except Exception as e:
                print(f"  [warn] {cid} failed: {e}")
                continue
            if _write_result(fh, cid, idx, row["instruction"], text):
                still_count += 1
            if n % 25 == 0:
                print(f"  {n}/{len(todo)} done")
    print(f"Done. {still_count} rewrites still look non-actionable (still_flagged) "
          f"-> review before applying.")
    return 0


def _run_batch(client, args, system, flagged, by_id):
    # Resume ingest of an existing batch.
    if args.batch_id:
        return _ingest_batch(client, args.batch_id, by_id)

    requests = [{
        "custom_id": cid,
        "params": {
            "model": args.model,
            "max_tokens": MAX_TOKENS,
            "output_config": {"effort": "low"},
            "system": system,
            "messages": [{"role": "user", "content": user_content(row)}],
        },
    } for cid, idx, row, _ in flagged]

    batch = client.messages.batches.create(requests=requests)
    print(f"Created batch {batch.id} with {len(requests)} requests (model={args.model}).")
    print("Polling until it ends (Ctrl-C is safe; resume with "
          f"--batch-id {batch.id})...")
    while True:
        b = client.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        counts = getattr(b, "request_counts", None)
        print(f"  status={b.processing_status} {counts}")
        time.sleep(args.poll)
    return _ingest_batch(client, batch.id, by_id)


def _ingest_batch(client, batch_id, by_id):
    print(f"Ingesting results for {batch_id} ...")
    written = still = errors = 0
    with open(REGEN_OUT, "w", encoding="utf-8") as fh:
        for result in client.messages.batches.results(batch_id):
            cid = result.custom_id
            idx, row = by_id.get(cid, (None, None))
            if idx is None:
                continue
            if result.result.type != "succeeded":
                errors += 1
                continue
            text = "".join(b.text for b in result.result.message.content
                           if b.type == "text")
            if _write_result(fh, cid, idx, row["instruction"], text):
                still += 1
            written += 1
    print(f"Wrote {written} rewrites -> {REGEN_OUT.name} "
          f"({errors} errored, {still} still look non-actionable).")
    print("Next:  python regenerate_flagged.py apply")
    return 0


# ----------------------------------------------------------------------------
def cmd_apply(args):
    if not REGEN_OUT.exists():
        print(f"[error] {REGEN_OUT.name} not found; run `run` (or emit+your pipeline) first.")
        return 1
    base = load_jsonl(BASE_FILE)
    regen = {json.loads(l)["custom_id"]: json.loads(l)
             for l in REGEN_OUT.read_text(encoding="utf-8").splitlines() if l.strip()}

    replaced = skipped_flagged = 0
    for cid, r in regen.items():
        idx = r["index"]
        if not r.get("response"):
            continue
        if r.get("still_flagged") and not args.include_flagged:
            skipped_flagged += 1
            continue
        base[idx]["response"] = r["response"]
        replaced += 1

    with open(REGEN_BASE, "w", encoding="utf-8") as f:
        for row in base:
            f.write(json.dumps({"instruction": row["instruction"],
                                "response": row["response"]},
                               ensure_ascii=False) + "\n")
    print(f"Replaced {replaced} rows with regenerated answers"
          + (f" (skipped {skipped_flagged} that still looked non-actionable; "
             f"--include-flagged to keep them)" if skipped_flagged else "")
          + f".\nWrote {REGEN_BASE.name} ({len(base)} rows).")
    print("Now rebuild the merged training set:")
    print(f"    python build_merged_v2.py --base {REGEN_BASE.name}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("emit", help="write regeneration prompts (offline)")

    pr = sub.add_parser("run", help="call Claude to rewrite flagged rows")
    pr.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"model id (default {DEFAULT_MODEL}; "
                         "claude-sonnet-5 / claude-haiku-4-5 are cheaper for bulk)")
    pr.add_argument("--sync", action="store_true",
                    help="one Messages call at a time (resumable) instead of Batch API")
    pr.add_argument("--batch-id", help="resume ingest of an existing batch id")
    pr.add_argument("--poll", type=int, default=30, help="batch poll interval (s)")

    pa = sub.add_parser("apply", help="splice rewrites back and write regen base")
    pa.add_argument("--include-flagged", action="store_true",
                    help="also apply rewrites that still failed the audit")

    args = ap.parse_args()
    return {"emit": cmd_emit, "run": cmd_run, "apply": cmd_apply}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
