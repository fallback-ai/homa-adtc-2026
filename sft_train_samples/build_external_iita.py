#!/usr/bin/env python3
"""Curated Homa SFT rows grounded in open-access IITA reports (CGSpace).

The IITA "Reports and Documents" collection is institutional/academic prose, not
farmer-facing Q&A, so these rows are HAND-AUTHORED from the facts stated in a
small hand-picked set of open-access (CC-BY / CC-BY-SA) reports, paraphrased
into Homa's actionable house style (see RESPONSE_STYLE.md). Facts are not
copyrightable and no report text is reproduced verbatim; sources are attributed
below. Where a report states the mechanism but not an exact farmer rate, the
answer gives the established extension figure and defers to the product label /
a soil test, matching the gold-set convention.

Sources (all Open Access, on CGSpace, https://hdl.handle.net/<handle>):
  * 10568/107315  AgResults Nigeria Aflasafe Challenge Project 2019 (CC-BY-4.0)
                  -> aflatoxin risk, Aflasafe biocontrol
  * 10568/132851  Soil quality assessment & management plans, IITA farms Nigeria
                  (CC-BY-4.0) -> soil organic matter, acidity/liming, fertility
  * 10568/180497  Biofortified cassava validation report (CC-BY-4.0)
                  -> vitamin-A (yellow) cassava
  * 10568/172781  Agronomy solution profile, digital toolkit (CC-BY-SA-4.0)
  * 10568/174445  Nutrient Expert (NE) lite digital tool (CC-BY-4.0)
                  -> site-specific nutrient management

Usage:
    python build_external_iita.py                 # writes external_iita.en.jsonl
    python build_external_iita.py --oversample 2  # repeat each row N times
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "external_iita.en.jsonl"

# (instruction, response) grounded in the reports above.
PAIRS = [
    # ---- Aflatoxin / Aflasafe (10568/107315) --------------------------------
    ("What is aflatoxin and why should I worry about it on my farm?",
     "Aflatoxins are poisons produced by Aspergillus flavus, a mould that grows "
     "on maize, groundnut and several other crops, especially when they are "
     "stored damp or damaged. They are dangerous because regular intake is "
     "linked to liver cancer in people and animals, weakens the immune system, "
     "and stunts growth in children; very high levels can be fatal. The mould "
     "and its poison are invisible and tasteless, so grain can look fine and "
     "still be contaminated. In Nigeria an estimated 40-60% of maize can carry "
     "unacceptably high aflatoxin levels, so it is worth managing deliberately."),
    ("Which crops are most affected by aflatoxin?",
     "Maize and groundnut are the most affected, but the Aspergillus mould that "
     "produces aflatoxin also attacks other crops such as sorghum, rice, "
     "cottonseed and tree nuts. Worldwide, up to about a quarter of the maize and "
     "groundnut harvest can become contaminated. The risk is highest when crops "
     "are stressed in the field (drought, insect damage) and when the harvest is "
     "dried slowly or stored while still moist."),
    ("How can I reduce aflatoxin in my maize and groundnut?",
     "Attack it at every stage:\n"
     "- In the field: plant on time, control insect pests and Striga, and avoid "
     "drought stress where you can. Consider a biocontrol product like Aflasafe "
     "(see below).\n"
     "- At harvest: harvest promptly when mature; do not leave the crop lying in "
     "the field.\n"
     "- Drying: dry to a safe moisture fast - about 13% or below for maize grain "
     "- on tarpaulins or racks, not bare soil.\n"
     "- Sorting: discard mouldy, discoloured, shrivelled or insect-bored grains "
     "and pods before storage.\n"
     "- Storage: store dry grain in clean, dry, well-ventilated stores or "
     "hermetic (airtight) bags, and control storage insects."),
    ("What is Aflasafe and how does it work?",
     "Aflasafe is a biocontrol product developed for Nigeria that contains four "
     "harmless (atoxigenic, i.e. non-poison-producing) strains of Aspergillus "
     "flavus that are native to Nigeria. Spread in the field, these friendly "
     "strains out-compete and crowd out the toxin-producing strains, so far less "
     "aflatoxin ends up in the grain - field tests in Nigeria have shown "
     "reductions of more than 80%. Nigeria was the first African country to "
     "register such a product. It is carried on sorghum grain; a few days after "
     "you apply it you can see the beneficial mould growing on the carrier."),
    ("When and how do I apply Aflasafe to my maize?",
     "Apply Aflasafe once, on the soil surface, 2-3 weeks before the crop "
     "flowers (before tasselling in maize), so the good strains establish before "
     "the toxic ones colonise the grain. The usual rate is about 10 kg/ha, "
     "broadcast by hand across the field, ideally onto moist soil or just before "
     "rain. You should see the beneficial mould growing on the sorghum carrier "
     "within about 5-15 days. Always follow the rate, timing and pre-harvest "
     "instructions printed on the Aflasafe label for your product."),
    ("Can I see or taste whether my grain has aflatoxin?",
     "No - aflatoxin is invisible, has no smell and no taste, and the grain can "
     "look perfectly good while carrying dangerous levels. Heavy mould, caking or "
     "a musty smell are warning signs that contamination is likely, but their "
     "absence does not prove the grain is safe. The only way to know the actual "
     "level is a laboratory test. Because you cannot judge it by eye, prevention "
     "- fast drying, good sorting, dry storage, and biocontrol - matters more "
     "than inspection."),

    # ---- Soil organic matter, acidity, fertility (10568/132851) -------------
    ("How do I build up the organic matter in my soil?",
     "There is really only one practical way: keep adding organic material and "
     "keep the soil covered. Use well-rotted manure or compost, return crop "
     "residues instead of burning them, grow and plough in legume cover crops, "
     "and rotate with legumes. Building organic matter takes bulk and patience - "
     "raising the organic carbon of the topsoil noticeably can need on the order "
     "of 20-25 tonnes of organic matter per hectare, added in stages over "
     "several seasons rather than all at once. The payoff is soil that holds more "
     "water and nutrients and grows stronger crops."),
    ("My poultry manure - how much do I need to improve the soil?",
     "It depends on how rich the manure is and how much you want to raise soil "
     "organic matter. As a rough guide, poultry manure that is about 30% organic "
     "carbon would need to be applied at roughly 40 tonnes per hectare to make a "
     "large change in topsoil organic carbon - so manure alone is bulky and is "
     "best combined with compost, crop residues and cover crops. Apply it "
     "well-rotted, work it into the topsoil, and split large amounts across "
     "seasons. A soil test helps you match the amount to what your field needs."),
    ("My soil is acidic. What should I do?",
     "Acidic soils (low pH) lock up phosphorus and can release aluminium that "
     "harms roots, so yields drop. Correct it with agricultural lime or dolomite, "
     "worked into the topsoil a few weeks to a couple of months before planting; "
     "dolomitic lime also adds magnesium. Sandy, low-CEC soils turn acidic "
     "quickly and need liming more often than heavier soils. Get a soil test to "
     "set the lime rate to your actual pH, and keep adding organic matter, which "
     "buffers the soil against becoming acidic again."),
    ("What does soil pH tell me and what range should I aim for?",
     "Soil pH tells you how acidic or alkaline your soil is, which controls how "
     "well nutrients are available to the crop. Most staple crops do best in "
     "slightly acidic to near-neutral soil, roughly pH 5.5-6.5. Below about pH "
     "5.5 the soil is getting too acidic - phosphorus is tied up and aluminium "
     "toxicity can set in - and you should think about liming. A simple soil test "
     "gives you the number so you are not guessing."),
    ("Why is soil organic matter so important?",
     "Organic matter is the engine of a healthy soil. It holds water so crops "
     "cope better with dry spells, stores and slowly releases nutrients, feeds "
     "the soil life that makes nutrients available, improves structure so roots "
     "and water move freely, and reduces erosion and crusting. Soils low in "
     "organic matter are hard, droughty and hungry. This is why returning "
     "residues, adding manure or compost, and growing cover crops pay off season "
     "after season."),
    ("Should I burn my crop residues after harvest?",
     "No - burning throws away one of your cheapest soil improvers. Crop residues "
     "left or worked into the field add organic matter, feed soil life, protect "
     "the surface from erosion and crusting, and recycle nutrients back to the "
     "soil. Burning also drives off nitrogen and can damage beneficial organisms. "
     "Instead, spread the residues as a mulch, plough them in, or compost them. "
     "The main exception is residue carrying a serious disease or pest, which is "
     "better removed."),

    # ---- Biofortified / vitamin-A cassava (10568/180497) --------------------
    ("What is vitamin A cassava (yellow cassava)?",
     "Vitamin A cassava, also called yellow or biofortified cassava, is cassava "
     "bred to be rich in provitamin A (beta-carotene), which gives the roots "
     "their yellow colour. It was developed for Nigeria by IITA with partners "
     "such as HarvestPlus and IFPRI. Unlike ordinary white cassava, which mainly "
     "supplies energy, the yellow types also deliver vitamin A when eaten - so "
     "the same staple food helps fight vitamin A deficiency, which harms "
     "eyesight and immunity, especially in children and pregnant women."),
    ("Is yellow cassava as productive as ordinary cassava?",
     "Yes. The improved vitamin A cassava varieties released in Nigeria are bred "
     "to be competitive and high-yielding, not just nutritious - the newer waves "
     "(the third was released in 2022) match good white varieties on yield while "
     "adding provitamin A. You grow them the same way as ordinary cassava. The "
     "main practical hurdle farmers report is getting enough clean planting stems "
     "of the improved varieties, so source stems early from a reliable multiplier "
     "or extension programme."),
    ("Where can I get planting material for vitamin A cassava?",
     "Get stems of the released vitamin A varieties from a trusted source - an "
     "IITA or HarvestPlus programme, a registered seed/stem multiplier, ADP or "
     "extension office, or a neighbour already growing certified material. Access "
     "to good stems is the biggest bottleneck farmers mention, so ask early and "
     "plan ahead. Choose healthy, mature stems free of disease symptoms, and once "
     "you are growing them you can multiply your own clean stems for the next "
     "season."),
    ("Does cooking destroy the vitamin A in yellow cassava?",
     "Some is lost, but a worthwhile amount remains. Provitamin A (beta-carotene) "
     "is reduced by long exposure to heat, light and air, so processing methods "
     "that are quick and not overly hot keep more of it. Even after normal "
     "processing into gari, fufu or flour, biofortified cassava still delivers "
     "meaningfully more vitamin A than white cassava, which has essentially none. "
     "To keep the most, avoid very long frying/roasting and store the products "
     "away from bright light."),

    # ---- Site-specific nutrient management (10568/174445, 172781) -----------
    ("Should I use the same fertilizer rate as my neighbour?",
     "Not necessarily. The right rate depends on your own soil's fertility, the "
     "crop, your target yield and what nutrients are already limiting in your "
     "field - blanket rates often waste fertilizer on one nutrient while another "
     "stays short. This is the idea behind site-specific nutrient management and "
     "tools like Nutrient Expert: match the fertilizer to the field. The "
     "practical version for you is a soil test plus local extension advice, then "
     "adjust based on how the crop responds season to season."),
    ("How can I get the most grain per bag of fertilizer I buy?",
     "Aim for agronomic efficiency - the most grain per unit of nutrient - rather "
     "than just piling on fertilizer:\n"
     "- Match the rate to your soil and yield goal (a soil test or a tool like "
     "Nutrient Expert helps); don't over-apply one nutrient while another limits "
     "the crop.\n"
     "- Split nitrogen into two or more doses so less is lost.\n"
     "- Place fertilizer near the plant (band or spot), not broadcast on bare "
     "soil, and apply just before rain or light irrigation.\n"
     "- Fix the basics first: right variety, spacing, weeding, soil organic "
     "matter and pH - fertilizer works far better on an otherwise healthy crop."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oversample", type=int, default=1,
                    help="repeat each row N times (default 1)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    rows = [{"instruction": i, "response": r} for i, r in PAIRS] * args.oversample
    Path(args.out).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8")
    print(f"unique rows: {len(PAIRS)}  (x{args.oversample} = {len(rows)})")
    print(f"Wrote -> {Path(args.out).name}")


if __name__ == "__main__":
    main()
