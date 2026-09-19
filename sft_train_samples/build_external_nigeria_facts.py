#!/usr/bin/env python3
"""Turn the electricsheepafrica Nigeria crop dataset into grounded SFT facts.

Source: https://huggingface.co/datasets/electricsheepafrica/
        africa-synth-agriculture-crop-planting-harvesting-nigeria  (MIT)
A 150k-row *tabular* synthetic dataset (farm_id, state, crop, variety,
planting_date, area_ha, expected/actual_yield_t_ha, harvest_date) parameterized
from FAO / NBS / NiMet / FMARD figures -- NOT question/answer text.

We do NOT parrot individual synthetic farm rows (that would teach the model to
invent over-specific numbers). Instead we AGGREGATE the corpus into a few
grounded facts per crop -- typical planting window, time to maturity, and yield
range -- and render them as actionable {instruction, response} pairs in the
Homa house style (see RESPONSE_STYLE.md).

Only the eight annual / root crops are templated: their aggregated planting
windows, maturity and yields line up with Nigerian extension norms. The two
perennials in the set (cocoa, oil_palm) are SKIPPED: the synthetic
planting-to-harvest interval (~3-9 months) is agronomically wrong for tree
crops that take years to mature, so surfacing it would teach false facts.

Numbers come from the data at run time; the season/region framing and the one
actionable agronomy tip per crop are curated and anchored to Nigerian practice.

Usage:
    python build_external_nigeria_facts.py            # download CSV + write jsonl
    python build_external_nigeria_facts.py --csv path/to/local.csv
"""
import argparse
import json
import pathlib

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
OUT_FILE = HERE / "external_nigeria_facts.en.jsonl"
CSV_URL = ("https://huggingface.co/datasets/electricsheepafrica/"
           "africa-synth-agriculture-crop-planting-harvesting-nigeria/"
           "resolve/main/nigerian_agriculture_crop_planting_harvesting.csv")

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

# Curated framing per crop. Numbers are filled from the data; this holds only
# the agronomic context (correct season narrative + one actionable tip). Crops
# whose empirical planting month is diffuse in the synthetic data ("flexible":
# True) get an onset-of-rains narrative instead of a spurious month list.
CROP_INFO = {
    "maize": dict(name="maize", flexible=False, two_season=True,
        region="across Nigeria, from the northern Guinea savanna to the south",
        tip=("Plant improved/hybrid seed at 75 cm x 25 cm (one plant per stand, "
             "~53,000 plants/ha). On most soils apply about 4 bags/ha (200 kg/ha) "
             "of NPK 15:15:15 at planting and top-dress with ~2 bags/ha (100 kg/ha) "
             "of urea at 5-6 weeks; adjust to your soil-test result.")),
    "rice": dict(name="rice", flexible=False, two_season=False,
        region="in the fadama and inland valleys of the north and middle belt",
        tip=("Use a certified variety such as FARO 44 or FARO 66, transplant "
             "21-day seedlings at 20 cm x 20 cm, and split nitrogen: ~3 bags/ha "
             "NPK at transplanting plus urea top-dressings at tillering and "
             "panicle initiation. Keep 3-5 cm of standing water during tillering.")),
    "sorghum": dict(name="sorghum", flexible=False, two_season=False,
        region="in the Sudan and northern Guinea savanna",
        tip=("Sow at 75 cm x 20-30 cm and apply ~2-3 bags/ha of NPK 15:15:15 at "
             "planting with a urea top-dressing at 4-5 weeks. Improved varieties "
             "(e.g. CSR-01, Samsorg lines) resist Striga and drought better.")),
    "millet": dict(name="millet", flexible=False, two_season=False,
        region="in the driest north (Sudan and Sahel savanna)",
        tip=("Sow on ridges at 75 cm x 30 cm as the rains stabilise. Millet needs "
             "little fertiliser -- ~1-2 bags/ha NPK plus a light urea top-dressing "
             "is enough on poor sandy soils. Thin to 2-3 plants per stand.")),
    "groundnut": dict(name="groundnut", flexible=False, two_season=False,
        region="in the northern and middle-belt savanna",
        tip=("Space at 45-75 cm x 10-15 cm. As a legume it fixes its own nitrogen, "
             "so skip urea; apply single super phosphate (SSP) at ~1-2 bags/ha and "
             "gypsum (~200-400 kg/ha) at flowering for good pod filling.")),
    "soybean": dict(name="soybean", flexible=True, two_season=False,
        region="in the middle belt and northern Guinea savanna",
        tip=("Inoculate the seed with rhizobium, drill at 45-75 cm rows, and skip "
             "nitrogen; apply SSP at ~1-2 bags/ha. Use a promiscuous-nodulating "
             "variety (e.g. TGx lines) if inoculant is unavailable.")),
    "cassava": dict(name="cassava", flexible=True, two_season=False,
        region="throughout the south and middle belt",
        tip=("Plant healthy stem cuttings (20-25 cm, 5-6 nodes) at 1 m x 1 m "
             "(~10,000 stands/ha). Use improved TMS varieties for higher yield and "
             "mosaic resistance; ~2-3 bags/ha NPK 15:15:15 helps on poor soils.")),
    "yam": dict(name="yam", flexible=False, two_season=False,
        region="in the yam belt of the middle belt and south-east",
        tip=("Plant setts (~200-300 g) on mounds or ridges at ~1 m spacing and "
             "stake the vines. Treat setts against rot before planting and apply "
             "~2-3 bags/ha NPK; avoid heavy nitrogen, which favours vine over tuber.")),
}


def load(csv_path):
    if csv_path:
        return pd.read_csv(csv_path, parse_dates=["planting_date", "harvest_date"])
    print(f"downloading CSV from HF ...")
    df = pd.read_csv(CSV_URL, parse_dates=["planting_date", "harvest_date"])
    return df


def month_window(series):
    """Return a human planting window from a month-number Series (concentrated)."""
    freq = series.value_counts(normalize=True)
    keep = sorted(m for m, f in freq.items() if f >= 0.08)
    # split into contiguous runs
    runs, run = [], [keep[0]]
    for m in keep[1:]:
        if m == run[-1] + 1:
            run.append(m)
        else:
            runs.append(run); run = [m]
    runs.append(run)
    parts = []
    for r in runs:
        parts.append(MONTHS[r[0]] if len(r) == 1
                     else f"{MONTHS[r[0]]}-{MONTHS[r[-1]]}")
    return runs, parts


def maturity_phrase(days_med):
    months = days_med / 30.4
    if months < 5:
        return f"about {round(months*4)/4:.2f}".rstrip("0").rstrip(".") + \
               f" months (~{int(round(days_med/7))} weeks)"
    return f"about {round(months)} months (~{int(days_med)} days)"


def build():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", help="local CSV path (default: download from HF)")
    ap.add_argument("--out", default=str(OUT_FILE))
    args = ap.parse_args()

    df = load(args.csv)
    df["pmonth"] = df["planting_date"].dt.month
    df["days"] = (df["harvest_date"] - df["planting_date"]).dt.days

    rows = []
    audit = []
    for crop, info in CROP_INFO.items():
        g = df[df["crop"] == crop]
        if g.empty:
            continue
        days_med = g["days"].median()
        ylo, ymed, yhi = (g["actual_yield_t_ha"].quantile(q) for q in (.10, .50, .90))
        maturity = maturity_phrase(days_med)
        yield_range = f"{ylo:.1f}-{yhi:.1f} t/ha (typically around {ymed:.1f} t/ha)"

        # planting window
        if info["flexible"]:
            window_sentence = (
                f"{info['name'].capitalize()} is flexible on timing and is planted "
                f"across much of the year, but establish it at the onset of the "
                f"rains (around March-April in the south) so it grows into the wet "
                f"season.")
            window_short = "at the onset of the rains"
        elif info["two_season"]:
            window_sentence = (
                f"There are two windows: an early-season crop planted around "
                f"April-June with the first rains, and a late-season crop around "
                f"October-November where a second rainy period allows it.")
            window_short = "April-June (early season) or October-November (late season)"
        else:
            runs, parts = month_window(g["pmonth"])
            joined = " or ".join(parts)
            window_sentence = (
                f"Plant {info['name']} around {joined}, once the rains have "
                f"settled in.")
            window_short = joined

        cap = info["name"].capitalize()
        n = f"{info['name']}"

        # 1) when to plant
        rows.append((
            f"When is the best time to plant {n} in Nigeria?",
            f"{window_sentence} {cap} is grown {info['region']}.\n\n"
            f"To get the most from the season: {info['tip']}"))
        # 2) maturity / time to harvest
        rows.append((
            f"How long does {n} take to be ready for harvest after planting?",
            f"{cap} takes {maturity} from planting to harvest in Nigerian "
            f"conditions. Plan your planting date so this maturity period falls "
            f"within the rains and the crop matures before the dry season sets in."))
        # 3) expected yield
        rows.append((
            f"What yield can I expect from {n} on my farm in Nigeria?",
            f"Typical {n} yields in Nigeria run about {yield_range}. Where farmers "
            f"fall short it is usually seed quality, spacing or soil fertility. "
            f"To push toward the upper end: {info['tip']}"))
        # 4) combined planting-to-harvest guide (varied phrasing)
        rows.append((
            f"Give me a quick planting-to-harvest guide for {n} in Nigeria.",
            f"- When to plant: {window_short}.\n"
            f"- Where it does well: grown {info['region']}.\n"
            f"- Time to harvest: {maturity} after planting.\n"
            f"- Typical yield: {yield_range}.\n"
            f"- Key step: {info['tip']}"))

        audit.append(dict(crop=crop, n=int(len(g)), days_median=float(days_med),
                          yield_p10=round(float(ylo), 2), yield_p50=round(float(ymed), 2),
                          yield_p90=round(float(yhi), 2), window=window_short))

    out = pathlib.Path(args.out)
    with open(out, "w", encoding="utf-8") as f:
        for instr, resp in rows:
            f.write(json.dumps({"instruction": instr, "response": resp},
                               ensure_ascii=False) + "\n")

    print(f"crops templated: {len(audit)}  (skipped perennials: cocoa, oil_palm)")
    for a in audit:
        print(f"  {a['crop']:9s} n={a['n']:6d} yield {a['yield_p10']}-{a['yield_p90']} "
              f"t/ha  window={a['window']}")
    print(f"rows written: {len(rows)} -> {out.name}")


if __name__ == "__main__":
    build()
