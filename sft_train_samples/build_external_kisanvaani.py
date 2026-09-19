#!/usr/bin/env python3
"""Filter the KisanVaani agriculture-QA set into a curated Homa SFT source.

Source: https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only
        (Apache-2.0)  22,615 rows, columns `question` / `answers`.

The raw set is a scraped agricultural FAQ/quiz corpus: only ~1,190 of the 22,615
rows carry a UNIQUE question, the median answer is ~86 characters, and many
"answers" are one-line fragments ("South America", "to improve growth"). Used
wholesale it would teach Homa the terse, non-actionable style the Round-1 judges
penalised, so we keep only a small, substantive, on-topic slice:

  * substantive answer (>= MIN_CHARS chars and >= MIN_WORDS words)
  * not a sentence fragment (answer doesn't start with a lowercase continuation)
  * not a deflection / identity leak (audit_actionability heuristics)
  * not tied to a non-Nigerian locality/market (drops East-Africa-specific rows)
  * de-duplicated by question (keeping the most actionable / longest answer) and
    de-duplicated against the existing base corpus so nothing is taught twice.

Light cleanup capitalises the question/answer and adds a trailing '?'. The
downstream clean_base_v2.py pass still normalises typography and re-dedups.

Usage:
    python build_external_kisanvaani.py --raw kisanvaani_raw.jsonl   # from cache
    python build_external_kisanvaani.py                              # fetch via API
    python build_external_kisanvaani.py --max 800
"""
import argparse
import json
import pathlib
import re
import time

from audit_actionability import audit_row, RATE

HERE = pathlib.Path(__file__).resolve().parent
OUT_FILE = HERE / "external_kisanvaani.en.jsonl"
BASE_CORPUS = HERE / "combined_train.en.jsonl"

MIN_CHARS = 160
MIN_WORDS = 25
MAX_CHARS = 2000

# Foreign-locality markers: rows mentioning these are region-specific to places
# Homa does not serve, so we drop them (general agronomy rows are kept).
FOREIGN = re.compile(
    r"\b(uganda|kabale|nakasero|kampala|kenya|nairobi|tanzania|rwanda|zimbabwe|"
    r"malawi|zambia|ethiopia|india|indian|pakistan|bangladesh)\b", re.IGNORECASE)

# Temperate / non-Nigerian crops. The KisanVaani tail is heavy on apple, grape,
# wine, garlic and stone fruit -- off-distribution for a Nigerian assistant.
# Rows specific to these are dropped; generic agronomy (soil, IPM, storage) and
# Nigerian staples stay. (Potato/wheat/onion ARE grown in Nigeria -> kept.)
OFFTOPIC = re.compile(
    r"\b(apple|apples|grape|grapes|grapevine|wine|winery|wineries|garlic|"
    r"cherry|cherries|peach|peaches|plum|plums|pear|pears|kiwi|olive|olives|"
    r"apricot|almond|walnut|blueberry|blueberries|raspberry|raspberries|"
    r"strawberry|strawberries|cranberry|barley|oats|rye|hops)\b", re.IGNORECASE)

# Answer starting with one of these lowercase words is a fragment continuing the
# question ("What transmits X?" -> "is spread by whiteflies"): not standalone.
FRAGMENT_START = {"is", "are", "was", "were", "to", "by", "until", "from",
                  "and", "or", "that", "which", "as", "of", "for", "with"}

# Nigeria / staple-crop relevance keywords (used only to rank, not to exclude).
RELEVANT = re.compile(
    r"\b(nigeria|cassava|maize|yam|sorghum|millet|groundnut|cowpea|soybean|"
    r"rice|cocoa|oil palm|plantain|tomato|pepper|okra|striga|armyworm|"
    r"mosaic|whitefl|napier|savanna|harmattan)\w*", re.IGNORECASE)


def norm(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def clean_question(q):
    q = re.sub(r"\s+", " ", (q or "").strip())
    if not q:
        return q
    q = q[0].upper() + q[1:]
    if q[-1] not in "?.!":
        q += "?"
    return q


def clean_answer(a):
    a = re.sub(r"[ \t]+", " ", (a or "").strip())
    if not a:
        return a
    return a[0].upper() + a[1:]


def load_rows(args):
    if args.raw:
        path = pathlib.Path(args.raw)
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Fetch via the HF datasets-server rows API (paced; it rate-limits).
    import requests
    api = "https://datasets-server.huggingface.co/rows"
    base = {"dataset": "KisanVaani/agriculture-qa-english-only",
            "config": "default", "split": "train"}
    rows, off, total = [], 0, None
    while total is None or off < total:
        d = None
        for attempt in range(6):
            r = requests.get(api, params={**base, "offset": off, "length": 100}, timeout=60)
            if r.status_code == 429:
                time.sleep(min(5 * (attempt + 1), 40)); continue
            r.raise_for_status(); d = r.json(); break
        if d is None:
            raise SystemExit("datasets-server fetch failed")
        total = d["num_rows_total"]
        batch = d.get("rows", [])
        if not batch:
            break
        rows.extend(x["row"] for x in batch)
        off += len(batch)
        time.sleep(0.6)
    return rows


def score(instr, resp):
    actionable = 1 if RATE.search(resp) else 0
    relevance = len(RELEVANT.findall(instr + " " + resp))
    return (actionable, relevance, len(resp))


def build():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", help="local raw JSONL (question/answers) to filter; "
                                  "omit to fetch from the HF datasets-server API")
    ap.add_argument("--max", type=int, default=800, help="cap on kept rows (default 800)")
    ap.add_argument("--out", default=str(OUT_FILE))
    args = ap.parse_args()

    rows = load_rows(args)
    stats = dict(total=len(rows), short=0, fragment=0, foreign=0, offtopic=0,
                 garbled=0, flagged=0, toolong=0, dup_q=0, dup_base=0, kept=0)

    # existing base questions, so we never duplicate what the corpus already has
    base_q = set()
    if BASE_CORPUS.exists():
        for l in BASE_CORPUS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                base_q.add(norm(json.loads(l).get("instruction")))

    best = {}      # normalized question -> {instruction, response, _score}
    for r in rows:
        q_raw = r.get("question") or ""
        a_raw = r.get("answers") or r.get("answer") or ""
        a_strip = a_raw.strip()

        if len(a_strip) < MIN_CHARS or len(a_strip.split()) < MIN_WORDS:
            stats["short"] += 1; continue
        if len(a_strip) > MAX_CHARS:
            stats["toolong"] += 1; continue
        first = a_strip.split()[0].lower().strip(".,;:")
        if a_strip[0].islower() and first in FRAGMENT_START:
            stats["fragment"] += 1; continue
        blob = q_raw + " " + a_raw
        if "�" in blob:
            stats["garbled"] += 1; continue
        if FOREIGN.search(blob):
            stats["foreign"] += 1; continue
        if OFFTOPIC.search(blob):
            stats["offtopic"] += 1; continue

        instr = clean_question(q_raw)
        resp = clean_answer(a_raw)
        if len(instr) < 15:
            stats["short"] += 1; continue
        if audit_row({"instruction": instr, "response": resp}):
            stats["flagged"] += 1; continue

        key = norm(instr)
        if key in base_q:
            stats["dup_base"] += 1; continue

        s = score(instr, resp)
        if key not in best:
            best[key] = {"instruction": instr, "response": resp, "_score": s}
        else:
            stats["dup_q"] += 1
            if s > best[key]["_score"]:
                best[key] = {"instruction": instr, "response": resp, "_score": s}

    kept = sorted(best.values(), key=lambda x: x["_score"], reverse=True)
    if len(kept) > args.max:
        kept = kept[:args.max]
    stats["kept"] = len(kept)

    out = pathlib.Path(args.out)
    with open(out, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps({"instruction": r["instruction"],
                                "response": r["response"]}, ensure_ascii=False) + "\n")

    print(f"raw rows:                 {stats['total']}")
    print(f"  dropped short/thin:     {stats['short']}")
    print(f"  dropped fragment start: {stats['fragment']}")
    print(f"  dropped over {MAX_CHARS}c:     {stats['toolong']}")
    print(f"  dropped foreign-region: {stats['foreign']}")
    print(f"  dropped off-topic crop: {stats['offtopic']}")
    print(f"  dropped garbled text:   {stats['garbled']}")
    print(f"  dropped deflect/ident:  {stats['flagged']}")
    print(f"  duplicate questions:    {stats['dup_q']}")
    print(f"  already in base corpus: {stats['dup_base']}")
    n_action = sum(1 for r in kept if r["_score"][0])
    print(f"KEPT:                     {stats['kept']}  ({n_action} with a product/rate)")
    print(f"Wrote -> {out.name}")


if __name__ == "__main__":
    build()
