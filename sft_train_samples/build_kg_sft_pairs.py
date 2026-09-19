#!/usr/bin/env python3
"""Synthesize grounded SFT pairs from the KG stage-4 evidence bundles (Method B).

This is the teammate "AI-assistant synthesis" run described in
kg_sft_handover/README.md (Section 4, Method B). Instead of calling an external
LLM API (Method A), the pairs here were authored by Claude directly from the
curated evidence bundles produced by build_kg_bundles.py -- so they can be
cross-audited against the Kaggle Qwen2.5-7B run before merging.

Pipeline:
    kg_pipeline_checkpoints/stage4_traversed_paths.jsonl   (221 KG paths)
      -> build_kg_bundles.py   -> kg_bundles.jsonl   (106 curated bundles)
      -> build_kg_sft_pairs.py -> sft_pairs_kg_claude.jsonl   (this file)

Grounding discipline (protects the Round-1 non-actionability finding):
  * Every pair is written from ONE host's grounding evidence.
  * Every NUMBER that appears in a response must appear verbatim in the KG
    evidence pool (checked automatically at build time -- see audit below).
    Where the evidence gives a mechanism/practice but no farmer-facing chemical
    rate, the response names the input class and defers to the product label /
    local extension for the exact rate rather than inventing false precision
    (same convention as RESPONSE_STYLE.md and build_external_iita.py).
  * Style is varied across conversational / short_steps / comprehensive and
    queries are framed in real Nigerian states, per the handover's diversity
    injection. Only {"instruction","response"} is exported.

Junk tail deliberately excluded: reference-citation "sources", survey-table
fragments ("procured and distributed", "500 seedlings"), variety-pedigree codes
(SAMNUT/ICGV), and recipe snippets from a fish-cookery PDF.

Run:
    python build_kg_bundles.py
    python build_kg_sft_pairs.py            # writes + self-audits
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLES = HERE / "kg_bundles.jsonl"
OUT = HERE / "sft_pairs_kg_claude.jsonl"

# Each pair: host (for grounding audit), style (documentation only),
# instruction, response. Numbers in `response` must exist in the host's KG
# evidence (or the global evidence pool, for grounded cross-crop advice).
PAIRS = [
    # ---------------- CASSAVA ----------------
    dict(host="cassava", style="comprehensive",
         instruction="I'm planting cassava in Benue and I've never used fertiliser on it before. How much should I apply and how do I put it?",
         response=(
             "A cassava crop removes a lot of nutrients: an average harvest of 10 tonnes of roots removes 23 kg N, 4 kg P and 30 kg K from your soil, so you have to put some back or yields fall over the years.\n\n"
             "As a working guide, for every 1 tonne of fresh roots you expect to harvest, apply about 20 kg N, 1.8 kg P and 13.8 kg K. These figures are deliberately about double what the plant needs, because only about half of the fertiliser you apply is actually taken up by the crop.\n\n"
             "How to place it: put the fertiliser in a half-moon shaped furrow about 20 cm from the base of the plant, then cover it with soil. Don't dump it against the stem. Cassava does best at a soil pH of 5.5 to 6.5, with 2 to 3 percent organic matter and at least 1000 mm of rain a year, so add manure or compost if your soil is poor. Always check the exact rate on your fertiliser bag and against local extension advice."
         )),
    dict(host="cassava", style="short_steps",
         instruction="How should I select and space my cassava cuttings?",
         response=(
             "Pick your planting material and spacing carefully:\n"
             "1. Use cuttings that are free of any sign of disease, freshly harvested, at least 2 cm in diameter and 20-25 cm long, clean-cut, and taken from the bottom end of the stem.\n"
             "2. For root production, space cuttings at 1 m x 1 m, which gives about 10,000 plants per hectare.\n"
             "3. Varieties that grow upright without branching can be planted closer, at 1 m x 0.5 m or 1 m x 0.75 m.\n"
             "4. If you are growing to multiply stems rather than roots, you can use 0.5 m x 0.5 m."
         )),
    dict(host="cassava", style="conversational",
         instruction="My cassava leaves look pale and yellowish and the canopy is thin. What does that mean?",
         response=(
             "Watch the canopy closely, because it tells you about nitrogen. If the canopy is sparse and a pale yellowish colour, the crop is short of nitrogen: increase the urea and apply it as soon as you see those symptoms. As a working guide for cassava, apply about 20 kg N for every 1 tonne of fresh roots you expect to harvest, placed in a half-moon furrow about 20 cm from the base of the plant and covered with soil. If instead the canopy is a lush dark green and dense, the plant has enough nitrogen and you should reduce or even stop it, otherwise you waste money and push leaf at the expense of roots. One more thing: if you have intercropped your cassava with vegetables, that combination needs more nitrogen than cassava grown on its own, so plan for a bit extra."
         )),
    dict(host="cassava", style="short_steps",
         instruction="How do I store fresh cassava tubers for a few weeks without them rotting?",
         response=(
             "Fresh cassava spoils within days, so handle it gently and store it moist:\n"
             "1. Only store undamaged tubers. This method works only for roots with no mechanical damage, so harvest carefully and set aside any that are cut or bruised for immediate use.\n"
             "2. Pack them in moist sawdust (for example in cartons or boxes).\n"
             "3. Inspect the cartons every 3 days to make sure the sawdust is still moist, and re-moisten it if it has dried out.\n"
             "For anything longer, process the roots into gari, flour or chips."
         )),
    dict(host="cassava", style="conversational",
         instruction="What yield can I realistically expect from cassava, and how do I protect it from mosaic disease?",
         response=(
             "With reasonable management you can expect about 10 to 15 tonnes of fresh tubers per hectare, and more with good fertiliser and improved varieties. The biggest threat to that yield is cassava mosaic disease (CMD), and you should also watch for cassava brown streak disease (CBSD). Most of the traditional varieties that farmers grow widely are susceptible to mosaic, so your best defence is to plant an improved, resistant variety and to take your cuttings only from healthy, disease-free plants. Rogue out and destroy any plant showing the yellow mosaic patterning so it does not spread through your cuttings next season."
         )),
    # ---------------- COWPEA ----------------
    dict(host="cowpea", style="comprehensive",
         instruction="My cowpea grain gets destroyed by weevils in storage every year in Kano. How do I stop this?",
         response=(
             "Storage weevils (bruchids) are the main cause of cowpea losses, and the fix is proper drying plus airtight fumigation:\n\n"
             "1. Dry the grain well first. Get it below 12 percent moisture before storage to avoid mould, and clean your granary or store before filling it with the new grain.\n"
             "2. Fumigate in an airtight container, sack or room, otherwise the tablets do not work. Use Phostoxin (aluminium phosphide): about 1 tablet to one bag of shelled grain, or 1-2 tablets per 100 kg sack, with the tablet wrapped in tissue paper and placed in the middle of the sack.\n"
             "3. For large bag stacks or pyramids, use 4-6 tablets or pellets per tonne (wrapped in newspaper) placed among the bags and cover the whole stack with a tarpaulin.\n"
             "4. Do not disturb the storage frequently, so the gas stays effective.\n\n"
             "Phostoxin is a poison gas, so follow the label exactly, keep it away from people and animals, and observe the waiting period before the grain is eaten or sold."
         )),
    # ---------------- ONION ----------------
    dict(host="onion", style="comprehensive",
         instruction="What soil and weather does onion need to do well?",
         response=(
             "Onion is not too fussy about soil type, but it does best on well-drained, medium-textured soils with a pH between 6.0 and 7.0 (the optimum range is 6.0 to 6.8). For temperature, aim for a growing season with day temperatures of 18 to 24 degrees C and night temperatures of 10 to 15 degrees C. It needs well-distributed rainfall of between 350 and 650 mm during the growing period, but crucially a dry spell at maturity: harvesting must be done in dry weather. If heavy rain falls near harvest it thickens the neck of the bulb so it cannot dry out properly, and bulbs with a thick neck will not store. Onion can be grown up to about 2,200 m above sea level."
         )),
    dict(host="onion", style="short_steps",
         instruction="How do I raise onion seedlings in the nursery and what seed rate do I need?",
         response=(
             "Raise them on a nursery seedbed, then transplant:\n"
             "1. Use certified seed of a good variety.\n"
             "2. Sow at a density of about 1,500 to 2,500 seeds per square metre, which is roughly 7 g of seed per square metre on the seedbed.\n"
             "3. Drill the seed in rows made 15 cm apart, cover lightly with soil, and mulch (for example with straw).\n"
             "4. Plan your total seed for the field at 3.0-4.0 kg/ha for hybrid varieties and 6.5-7.5 kg/ha for open-pollinated varieties."
         )),
    dict(host="onion", style="conversational",
         instruction="How do I dry onion seed (umbels) after harvesting them?",
         response=(
             "Once you have cut the seed heads, dry the harvested umbels gently rather than in harsh sun. Spread the umbels on canvas and keep them under shade, or expose them only to the mild morning or late-afternoon sun, for a few days until they are dry. Then you can thresh out the seed. Drying too hard in the hot midday sun damages seed viability, so keep it slow and shaded."
         )),
    # ---------------- RICE ----------------
    dict(host="rice", style="comprehensive",
         instruction="How much yield should I expect from rice, and how do I protect the paddy in storage?",
         response=(
             "Yields depend on your system. Farmers' yields typically range between 1,200 and 3,000 kg/ha (about 16 to 40 bags) for swamp rice, and 1,000 to 1,500 kg/ha (about 13 to 20 bags) for upland rice.\n\n"
             "To protect stored paddy from insect pests you have two grounded options:\n"
             "1. Dusting: use 1 matchbox full of Coopex 2.5 to dust about 25 kg of paddy.\n"
             "2. Fumigation in airtight containers or rooms: use phostoxin at one tablet per jute bag (100 kg paddy), or 10 to 15 tablets per tonne of paddy.\n"
             "Store the treated paddy in cool, dry, rodent-proof conditions. Follow the product label and keep fumigants away from people and animals."
         )),
    dict(host="rice", style="conversational",
         instruction="My rice in Kogi has brown spots on the leaves and the plants look stunted. What is it and what do I do?",
         response=(
             "Brown spots on the leaves together with stunting point most likely to Brown Leaf Spot, a fungal disease tied to potassium- and nutrient-poor soil, and it is a real yield-robber. Don't confuse it with blast, which shows diamond-shaped lesions, or bacterial leaf blight, which gives water-soaked streaks from the leaf tip. The first fix is to correct the soil: brown spot thrives where the crop is starved, so restore fertility, especially potassium. On top of that you can spray a protectant fungicide at the label rate, and use resistant varieties. In the surveys, rice blast and brown leaf spot were causing moderate damage with yield losses around 12 to 40 percent in affected states, so it is worth acting early rather than waiting."
         )),
    dict(host="rice", style="short_steps",
         instruction="How do I prime and pre-germinate rice seed before sowing?",
         response=(
             "Priming gives you faster, more even germination:\n"
             "1. Soak the seeds in cold water for 12 hours (overnight), then drain them.\n"
             "2. To go further and pre-germinate, soak the seeds in water for 24 hours.\n"
             "3. Spread them on the floor and incubate by covering with polyethylene bags for 48 hours until the seeds sprout.\n"
             "4. For direct seeding, air-dry the seeds for about two hours and then sow into wet soil."
         )),
    # ---------------- SORGHUM ----------------
    dict(host="sorghum", style="comprehensive",
         instruction="How do I plant sorghum and place the basal fertiliser correctly?",
         response=(
             "Set up your rows and place fertiliser below the seed so the young roots reach it:\n\n"
             "1. Make a furrow 5 to 7 cm deep. You will use this same furrow to plant.\n"
             "2. Apply the basal fertiliser: about 2 heaped beer bottle caps per basin, which is equivalent to 200 kg/ha of NPK 11:22:21+5%S+0.7%Zn+0.5%B.\n"
             "3. Cover the fertiliser with a layer of soil 1 to 2 cm thick before you drop the seed, so the seed does not sit directly on the fertiliser.\n"
             "4. Sow seeds at 2 to 4 cm depth. Establish about 3 seedlings per hole and thin to 2 per hole.\n"
             "5. Spacing in sole crop: between rows 40 to 90 cm and within the row 15 to 40 cm (the wider the row spacing, the closer the plants within the row). In conventional tillage you can plough, harrow and make ridges at 75 cm row spacing.\n"
             "Sorghum likes well-drained soils with a pH of 6.0 to 7.5."
         )),
    dict(host="sorghum", style="short_steps",
         instruction="When should I top-dress nitrogen on my sorghum, and how much urea does one split need?",
         response=(
             "Timing matters more than most farmers think:\n"
             "1. Apply nitrogen as a top-dressing before the panicles (flowers) emerge. A common and costly mistake is to apply N when the grain is already filling out, which is too late to help.\n"
             "2. Place the top-dressing 5 to 10 cm away from the plant and keep the fertiliser off the plant itself to avoid fertiliser burn.\n"
             "3. For one split of 20 kg N, you need about 44 kg of urea (20 x 100/46), which is roughly one 50 kg bag per hectare.\n"
             "Even a small dose pays: microdosing can lift a crop from around 600 kg/ha with no fertiliser to about 1200 kg/ha."
         )),
    dict(host="sorghum", style="conversational",
         instruction="Is it really worth spending money on fertiliser for my sorghum? How do I know?",
         response=(
             "Yes, if the extra grain is worth more than the fertiliser, and you can check that with the value-cost ratio (VCR). The VCR is the extra value of the crop from fertiliser divided by the cost of the fertiliser. For an investment to be worthwhile you want a VCR of 2 or more; a VCR of 1 is just breakeven, and below 1 you lose money. In one worked sorghum example the extra grain was worth 449 dollars against a fertiliser cost of 120 dollars, giving a VCR of 2.74, meaning the farmer got 2.74 dollars back for every 1 dollar spent and made an additional 329 dollars per hectare. So start with a small, well-placed dose, weigh the extra grain against the cost, and scale up only while the VCR stays above 2."
         )),
    # ---------------- MILLET ----------------
    dict(host="millet", style="comprehensive",
         instruction="What fertiliser does pearl millet need and when should I apply the nitrogen?",
         response=(
             "Millet responds well to a modest, well-timed dose. A common target is to supply about 40 kg N and 20 kg P per hectare at around 10,000 stands per hectare. For nitrogen timing, apply it as a top-dressing before the panicles (flowers) emerge; applying N once the grain is filling is too late. For one split of 20 kg N you need about 44 kg of urea (about one 50 kg bag) per hectare. Even microdosing pays: a crop can rise from around 350 kg/ha with no fertiliser to about 850 kg/ha with a small applied dose. On very light sandy soils that suit millet, also apply lime at about 2 tonnes per hectare every 5 years to correct acidity."
         )),
    # ---------------- SWEET POTATO ----------------
    dict(host="sweet potato", style="short_steps",
         instruction="How do I propagate sweet potato and keep the weevil out?",
         response=(
             "Sweet potato is grown from vine cuttings, not seed:\n"
             "1. Propagate by planting vine cuttings.\n"
             "2. Plant on ridges. Ridge planting combined with vine propagation is the recommended way to control the ridge-planting weevil, which is a common pest.\n"
             "3. Choose well-drained, sandy loam soil with a pH of 5.5 to 6.5.\n"
             "4. Take cuttings from healthy vines so you don't carry the weevil or disease into the new field."
         )),
    dict(host="sweet potato", style="comprehensive",
         instruction="How do I cure and store sweet potato roots so they last?",
         response=(
             "Curing before storage is what makes sweet potato keep. It heals the harvest wounds by forming a protective skin, which slows rot and weight loss.\n\n"
             "1. Right after harvest, cure the roots at 29 to 33 degrees C and 85 to 90 percent relative humidity, with good ventilation, for 4 to 7 days.\n"
             "2. Then store the cured roots at 13 to 15 degrees C and 85 to 95 percent relative humidity; well-cured roots stay marketable for up to 12 months.\n"
             "3. Keep the store cool but not cold: once temperatures go above 16 degrees C the roots start to sprout, which raises respiration and weight loss, while temperatures below 10 degrees C cause chilling injury.\n"
             "4. Don't leave harvested roots in bright sun for more than 30 minutes, or you get sun-scald on the skin, which is both a cosmetic fault and an entry point for rot.\n"
             "Uncured roots simply will not store, so never skip the curing step."
         )),
    # ---------------- GARLIC ----------------
    dict(host="garlic", style="conversational",
         instruction="What kind of land should I pick for garlic under irrigation?",
         response=(
             "Choose your site carefully, because garlic bulbs are shaped by the soil. Pick a well-drained, fertile loamy soil that is free of stones and gravel, rich in organic matter, and keep the pH at 6.0 to 7.5. Avoid heavy soils: on heavy or poorly drained land the bulbs come out deformed and discoloured, and they are hard to lift at harvest. The site should also be close to a reliable source of irrigation water. After you pulverise and level the land, form your basins to a size of about 2 m x 1.5 m, or whatever suits your soil type, slope and irrigation stream."
         )),
    # ---------------- MAIZE ----------------
    dict(host="maize", style="short_steps",
         instruction="How much nitrogen does maize need and how do I split it, and what yield should I aim for?",
         response=(
             "Split the nitrogen so the crop gets it when it needs it:\n"
             "1. Apply a total of 60 to 90 kg of N per hectare.\n"
             "2. Put it on in 3 equal splits, at 2, 4 and 6 weeks after planting.\n"
             "3. As a guide, one 20 kg N split needs about 44 kg of urea (about one 50 kg bag) per hectare.\n"
             "With good management, maize gives about 1,500 to 2,500 kg of dry grain per hectare. Check the exact rate against your soil test and local extension advice."
         )),
    # ---------------- SOYBEAN ----------------
    dict(host="soybean", style="conversational",
         instruction="Do I need to put nitrogen fertiliser on my soybean?",
         response=(
             "Usually not much. Soybean is a legume, so once it nodulates properly it fixes its own nitrogen from the air, and it will even leave some nitrogen in the soil for the next crop such as maize. Until nodulation happens, the young plant depends on the nitrogen already in your soil, so a healthy soil matters early on. The nutrient to focus on is phosphorus, which is often the most deficient: apply an optimal phosphorus fertiliser for a good yield. Only add nitrogen and potassium fertiliser if the plants show obvious deficiency. So spend your money on phosphorus first, not on blanket nitrogen."
         )),
    dict(host="soybean", style="conversational",
         instruction="I have a bad Striga (witchweed) problem in my maize field. Can soybean help?",
         response=(
             "Yes, soybean is a useful weapon against Striga hermonthica, the parasitic weed that attacks maize. When you grow soybean in rotation with maize it acts as a catch-crop: it triggers the Striga seed in the soil to germinate even though there is no maize root to attach to, so those seeds die off (suicidal germination) and the reservoir in your soil shrinks. On top of that, soybean improves soil fertility and fixes nitrogen for the maize that follows. So rotate soybean into that field for a season or two, and you knock back both the Striga and the fertility problem at once. You can also plant two rows of soybean between rows of cassava to make use of the space."
         )),
    # ---------------- PEPPER ----------------
    dict(host="pepper", style="conversational",
         instruction="When should I plant pepper in northern Nigeria and what yield can I get?",
         response=(
             "In northern Nigeria you can plant pepper towards the end of the rains, around September, so the crop makes use of the residual moisture in the soil at that time, and then supplement with irrigation water during flowering or once the rains cease. Pepper needs careful handling in both the nursery beds and the field. If the climate and soil are favourable and you follow the production stages properly, pepper (Capsicum annuum) can yield up to 15 t/ha. Watch weed control in the seedbed, since a thick stand of pepper makes it hard to pull broad-leaved weeds and grasses, and avoid repeatedly walking on and transplanting from wet clay or silty soil, which packs it down."
         )),
    # ---------------- GROUNDNUT ----------------
    dict(host="groundnut", style="conversational",
         instruction="What is the best way to control groundnut diseases, and should I worry about aflatoxin?",
         response=(
             "The most effective, economical and sustainable way to control groundnut disease is to plant host-resistant varieties, so start there rather than relying on sprays. Aflatoxin is a serious separate worry: it builds up in poorly dried or damaged groundnut, and its effect on people is cumulative. You cannot cook it out, because aflatoxin is not destroyed by cooking, and the body does not break it down or get rid of it. So dry your pods quickly and fully after harvest, discard shrivelled or mouldy nuts, and store dry, to keep aflatoxin from forming in the first place."
         )),
    # ---------------- COTTON ----------------
    dict(host="cotton", style="conversational",
         instruction="Is cotton a good crop for my dry area, and what yield is normal?",
         response=(
             "Cotton is a good fit for dry areas: it is a drought-tolerant crop grown in arid and semi-arid lands. Average yields in Nigeria are modest, around 0.78 to 0.80 tonnes per hectare, so plan your economics around that rather than expecting a heavy crop. Katsina is the largest producer, turning out roughly 40,000 to 45,000 metric tonnes a year, which shows the northern dry belt suits it well. If your rainfall is low and unreliable, cotton is a sensible choice compared with thirstier crops."
         )),
    # ---------------- RUBBER ----------------
    dict(host="rubber", style="short_steps",
         instruction="What soil and drainage does a rubber plantation need?",
         response=(
             "Rubber needs deep, freely draining land for its roots:\n"
             "1. Choose a well-drained, sandy loam soil with a well-aerated, permeable subsoil the root system can grow down into.\n"
             "2. Make sure the land is drained to at least 1.2 m depth, which is adequate for rubber.\n"
             "3. Soils rich in nitrogen are preferred, but phosphorus and potassium must also be available, along with trace elements, so correct these from a soil test."
         )),
    # ---------------- FISH ----------------
    dict(host="fish", style="conversational",
         instruction="How does fertilising a fish pond actually feed the fish?",
         response=(
             "Fertiliser feeds the fish indirectly, through the food chain in the water. When you apply fertiliser to the pond it acts as nutrients that make phytoplankton (tiny plants) multiply. As the phytoplankton multiply they are eaten directly by some fish, and by tiny animals called zooplankton, which in turn are eaten by larger animals and by fish. So by fertilising you are really growing the natural food that your fish feed on. A fish pond is simply an enclosure, earthen or concrete, built to hold water so you can feed, breed, grow and harvest the fish in a well-planned way and stop them escaping."
         )),
    dict(host="fish", style="short_steps",
         instruction="What can I use to lime my fish pond?",
         response=(
             "Liming corrects acidity and helps productivity. Common materials you can use are:\n"
             "1. Agricultural lime / limestone (calcium carbonate, CaCO3).\n"
             "2. Caustic, slaked or hydrated lime (calcium hydroxide, Ca(OH)2).\n"
             "Apply it to the pond bottom, and follow the rate advised for your water and soil test. Also check the water level regularly with a graduated stick so you can replace water lost to evaporation or seepage."
         )),
    # ---------------- TOMATO (postharvest) ----------------
    dict(host="tomato", style="short_steps",
         instruction="How do I dry tomatoes to preserve them for sale in Kano?",
         response=(
             "Drying removes the water that spoilage organisms need, so it is a good way to preserve a glut:\n"
             "1. Slice the tomatoes and sun-dry them by spreading the slices on clean wooden, plastic, chromed or non-stick coated drying trays on a raised platform.\n"
             "2. Do not use galvanized screening or trays, because the zinc reacts with the acid in the tomatoes.\n"
             "3. Where you can, use a solar dryer for a better-quality product, and keep the redness after drying.\n"
             "4. For commercial quantities, a hot-air dryer gives the most consistent result.\n"
             "Dried and preserved tomatoes work for both home use and for income."
         )),
    # ---------------- SMALL RUMINANTS / LIVESTOCK ----------------
    dict(host="small ruminants", style="conversational",
         instruction="My goats and sheep keep getting worms. How do I manage that?",
         response=(
             "Internal worms are managed by regular de-worming rather than waiting until the animals are visibly sick. Set up a routine deworming schedule with an anthelmintic from an agrovet or animal-health worker, and dose to the animal's body weight following the product label. Tapeworms in particular hide in the tissues, organs and intestines and can stay in the body with no outward sign, and lambs are the most affected, so treat the young stock too. Pair the drenching with clean water, rotating grazing off heavily used paddocks, and good hygiene to cut the worm burden on your land."
         )),
    dict(host="turkey", style="conversational",
         instruction="I keep chickens and want to add turkeys and ducks. Any disease risk in mixing them?",
         response=(
             "Yes, be careful mixing poultry species. Other birds such as ducks, geese, turkeys and guinea fowl can carry disease pathogens without showing any signs themselves, and then pass them on to your chickens. So don't assume a healthy-looking bird is safe. House the different species separately, avoid sharing feeders and drinkers across them, quarantine any new birds before they join the flock, and keep wild birds out. Good separation and biosecurity are cheaper than losing a flock."
         )),
]


def norm_num_text(t):
    # normalize for number matching: drop thousands commas, collapse spaces, lower
    t = t.lower().replace(",", "")
    t = re.sub(r"\s+", " ", t)
    return t


NUMTOKEN = re.compile(r"\d+(?:\.\d+)?")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any response number is ungrounded")
    args = ap.parse_args()

    bundles = [json.loads(l) for l in BUNDLES.read_text(encoding="utf-8").splitlines() if l.strip()]
    per_host, global_pool = {}, []
    for b in bundles:
        txt = " ".join(b["evidence"])
        per_host.setdefault(b["host"], []).append(txt)
        global_pool.append(txt)
    per_host = {h: norm_num_text(" ".join(v)) for h, v in per_host.items()}
    pool = norm_num_text(" ".join(global_pool))

    # numeric grounding audit
    ungrounded = []
    for i, p in enumerate(PAIRS):
        host_ev = per_host.get(p["host"], "")
        resp = norm_num_text(p["response"])
        for n in set(NUMTOKEN.findall(resp)):
            # ignore trivially small list markers 1-9 that are step numbers only
            in_host = n in host_ev
            in_pool = n in pool
            if not in_pool:
                ungrounded.append((i, p["host"], n))
            elif not in_host:
                # grounded, but in another host's evidence (cross-crop advice)
                pass

    hosts = sorted(set(p["host"] for p in PAIRS))
    OUT_P = Path(args.out)
    OUT_P.write_text(
        "\n".join(json.dumps({"instruction": p["instruction"], "response": p["response"]},
                             ensure_ascii=False) for p in PAIRS) + "\n",
        encoding="utf-8")

    print(f"pairs written:   {len(PAIRS)} -> {OUT_P.name}")
    print(f"distinct hosts:  {len(hosts)} ({', '.join(hosts)})")
    if ungrounded:
        print(f"\nUNGROUNDED NUMBERS ({len(ungrounded)}) -- not found verbatim in KG evidence:")
        for i, h, n in ungrounded:
            print(f"  pair[{i}] host={h}: {n}")
        if args.strict:
            raise SystemExit(1)
    else:
        print("numeric grounding: OK (every response number appears in the KG evidence)")


if __name__ == "__main__":
    main()
