#!/usr/bin/env python3
"""Homa v2 gold batch 2: persona (eval-format) + meta/technical examples.

Two coverage gaps found in the base corpus:
  * PERSONA - only ~3% of base rows use the first-person, location-specific,
    multi-part format the judges actually test ("I am a <crop> farmer in <State>,
    Nigeria. <symptoms>. What is the cause, how do I confirm it, treat it, and
    prevent it?"). These cover crops/pests NOT already in build_gold_v2.py.
  * META - 0 base rows cover the edge-AI / offline-architecture questions used as
    hidden test prompts. Answered on-brand and offline-first (never "use the
    cloud"), matching how Homa is actually built.

Agronomy follows RESPONSE_STYLE.md: correct diagnosis, then product + rate +
timing + method + a label/pre-harvest-interval safety note; realistic ranges,
defer to the label/extension for exact figures.

Usage:
    python build_gold_persona.py                 # writes homa_gold_persona.en.jsonl
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "homa_gold_persona.en.jsonl"

PERSONA = [
    # Groundnut rosette + leaf spot (Jigawa)
    (
        "I am a groundnut farmer in Jigawa State, Nigeria. My plants are stunted "
        "and bunched with yellow, mottled leaves, and there are small dark "
        "insects on the young shoots. What is the cause, how do I confirm it, and "
        "how do I treat and prevent it?",
        "The stunting, bunching and yellow mottling, together with the dark "
        "insects, point to groundnut rosette disease. It is a virus spread by "
        "groundnut aphids (Aphis craccivora) - the small dark insects on your "
        "shoots.\n\n"
        "Confirm it: look for stunted, bushy plants with pale or green rosetted "
        "leaves, worse in patches, and aphid colonies on the growing tips.\n\n"
        "Treatment:\n"
        "1. The virus has no cure, so control the aphids and remove sources. "
        "Uproot and destroy badly rosetted plants early.\n"
        "2. Control aphids: neem at 5 ml/L on the shoots, or a registered "
        "insecticide such as imidacloprid (seed dressing at planting, or foliar "
        "at the label rate) - start early, when aphids first appear.\n\n"
        "Prevention:\n"
        "1. Plant early and at a dense, recommended spacing (about 75,000 plants/ha) "
        "- close stands slow aphid spread and cut rosette sharply.\n"
        "2. Use rosette-resistant varieties (e.g. improved SAMNUT lines).\n"
        "Watch also for leaf spot (dark spots on leaves): if it appears, spray "
        "mancozeb at ~2.5 g/L every 2-3 weeks and follow the pre-harvest interval.",
    ),
    # Cocoa black pod + capsids (Ondo)
    (
        "I am a cocoa farmer in Ondo State, Nigeria. Some of my pods have "
        "spreading brown-black rot and there is white growth on them. What is it, "
        "how do I confirm it, and what do I do?",
        "Spreading chocolate-brown to black rot with white fungal growth on the "
        "pods is black pod disease, caused by the fungus Phytophthora palmivora. "
        "It spreads fast in the wet season through rain splash and infected pods.\n\n"
        "Confirm it: a brown spot that enlarges quickly to cover the whole pod, "
        "firm rot inside, and white spore growth on the surface.\n\n"
        "Treatment and prevention:\n"
        "1. Sanitation weekly: remove and bury or burn all infected pods and "
        "mummified pods - they are the main source. Harvest ripe pods promptly.\n"
        "2. Prune to open the canopy and improve airflow, and drain wet spots; the "
        "fungus loves damp, shaded, humid conditions.\n"
        "3. Spray a copper fungicide (copper hydroxide/oxide, e.g. Kocide) or a "
        "metalaxyl+copper product at the label rate, every 3-4 weeks through the "
        "wet season, covering the pods.\n"
        "4. Watch for capsids/mirids (they cause sunken lesions and dieback on "
        "pods and shoots): apply a recommended insecticide such as imidacloprid or "
        "bifenthrin at the label rate 2-4 times a year if present.\n"
        "Follow the label rate and pre-harvest interval on all products.",
    ),
    # Irish potato late blight (Plateau/Jos)
    (
        "I am an Irish potato farmer on the Jos Plateau in Plateau State, "
        "Nigeria. In the cool, wet weather my plants suddenly developed dark "
        "water-soaked patches on the leaves and are collapsing. What is this and "
        "how do I control it?",
        "Dark, water-soaked leaf patches that spread fast and collapse the plant "
        "in cool, wet weather is late blight (Phytophthora infestans) - the most "
        "serious potato disease, and the Jos climate favours it.\n\n"
        "Confirm it: brown-black lesions with a pale, water-soaked edge, often "
        "with white mould on the leaf underside in the morning, and a rotten "
        "smell as plants collapse.\n\n"
        "Control - act fast, it can destroy a field in days:\n"
        "1. Start with a protectant fungicide: mancozeb (Dithane M-45) at ~2.5 g/L "
        "before or at first sign, every 7 days in wet weather.\n"
        "2. Under heavy pressure switch to a systemic: metalaxyl + mancozeb "
        "(Ridomil Gold) at the label rate.\n"
        "3. Remove and destroy infected plants and any volunteer/self-sown "
        "potatoes; earth up (ridge) well so spores do not reach the tubers.\n"
        "4. Harvest in dry weather and cure tubers before storage.\n\n"
        "Prevention: plant certified disease-free seed tubers and blight-tolerant "
        "varieties, space for airflow, and avoid overhead irrigation late in the "
        "day. Follow the label rate and pre-harvest interval.",
    ),
    # Sorghum striga + midge (Sokoto)
    (
        "I am a sorghum farmer in Sokoto State, Nigeria. Small purple-flowered "
        "weeds are growing around my sorghum and the crop is stunted and yellow. "
        "What is happening and how do I deal with it?",
        "The small purple-flowered weeds attached near your sorghum roots are "
        "Striga (witchweed, Striga hermonthica), a parasitic weed that drains the "
        "crop - which is why the sorghum is stunted and yellow. By the time you "
        "see the purple flowers, the striga has already been feeding underground.\n\n"
        "Confirm it: slender weeds with small purple flowers emerging in patches "
        "beside stunted, yellow sorghum, usually on poor soils.\n\n"
        "Management (a multi-year job):\n"
        "1. Hand-pull and destroy striga before it flowers and sets seed - one "
        "plant makes tens of thousands of seeds, so stop the seed bank now.\n"
        "2. Improve soil fertility: apply nitrogen (urea top-dress, ~65 kg/ha) and "
        "organic manure - well-fed, well-nourished soil strongly suppresses "
        "striga.\n"
        "3. Rotate or intercrop with a legume 'trap crop' such as cowpea or "
        "groundnut, which makes striga seeds germinate and die with no host.\n"
        "4. Plant striga-tolerant/resistant sorghum varieties and use clean, "
        "striga-free seed.\n\n"
        "Also scout at flowering for sorghum midge (tiny orange larvae in the "
        "florets cause blasted, empty grain): plant early and uniformly, and if "
        "present spray a recommended insecticide at flowering at the label rate.",
    ),
    # Cowpea Maruca pod borer complex (Kano)
    (
        "I am a cowpea (beans) farmer in Kano State, Nigeria. My plants flower "
        "well but the flowers and young pods are webbed together with small "
        "caterpillars inside, and I am losing most of the pods. What is the cause "
        "and how do I control it?",
        "Webbed flowers and pods with caterpillars boring inside is the legume pod "
        "borer, Maruca (Maruca vitrata) - the number-one cowpea pest in the "
        "north. It attacks exactly at flowering, which is why your pod set is "
        "failing.\n\n"
        "Confirm it: flowers and young pods webbed together, small caterpillars "
        "with dark spots inside the webbing, and boreholes with frass in pods.\n\n"
        "Control - the flowering window is critical:\n"
        "1. Start spraying at bud/early-flower stage, not after the pods are "
        "damaged. Use a registered insecticide such as lambda-cyhalothrin, or "
        "emamectin benzoate for the borer, at the label rate; give 2-3 sprays 7-10 "
        "days apart during flowering and podding.\n"
        "2. Rotate insecticide groups to avoid resistance, and spray in the "
        "evening to protect bees.\n"
        "3. Neem at 5 ml/L helps against the aphids and flower thrips that often "
        "come with Maruca.\n\n"
        "Prevention: scout flowers twice a week with a sweep, plant early and with "
        "your neighbours, and use improved/PBR (pod-borer-resistant) cowpea where "
        "available. Follow the label rate and pre-harvest interval.",
    ),
    # Cassava mealybug - biocontrol (Oyo)
    (
        "I am a cassava farmer in Oyo State, Nigeria. The tips of my cassava have "
        "white cottony insects and the top leaves are bunched and distorted like a "
        "candle. What is it and how do I treat it?",
        "The white cottony insects on the shoot tips, with bunched 'candle-tip' "
        "distortion and stunting, are cassava mealybug (Phenacoccus manihoti). "
        "They suck the growing point and stunt the plant, mostly in the dry "
        "season.\n\n"
        "Confirm it: white, waxy, cottony masses clustered on the growing tips, "
        "and shortened, bunched top leaves.\n\n"
        "Treatment - biological control is the proven fix here:\n"
        "1. The parasitoid wasp Anagyrus lopezi, introduced across Africa by "
        "IITA, controls cassava mealybug very effectively. The most important "
        "thing you can do is NOT spray broad-spectrum insecticides, which kill "
        "this helpful wasp and make the problem worse.\n"
        "2. Cut off and destroy heavily infested tips; for a small patch, spot-"
        "treat with neem at 5 ml/L rather than a blanket spray.\n\n"
        "Prevention:\n"
        "1. Plant clean, healthy cuttings from unaffected plants, and use "
        "improved/tolerant varieties.\n"
        "2. Plant at the onset of the rains - vigorous, well-watered plants "
        "outgrow the pest, which peaks in the dry season.",
    ),
    # Catfish pond water quality (aquaculture)
    (
        "I am a catfish farmer in Ogun State, Nigeria. My fish are gathering at "
        "the surface gasping, are off feed, and some are dying, even though there "
        "are no visible wounds. What is wrong and what should I do?",
        "Fish gasping at the surface (especially early morning), off feed, and "
        "dying with no wounds is almost always a water-quality problem - usually "
        "low dissolved oxygen and/or a build-up of ammonia from uneaten feed and "
        "waste, not an infection.\n\n"
        "Confirm it: fish crowding at the surface and at the inlet at dawn (low "
        "oxygen), dark or foul-smelling water, and a water-test kit showing high "
        "ammonia (above ~0.5 mg/L is stressful) or low oxygen.\n\n"
        "What to do now:\n"
        "1. Exchange 20-30% of the pond water with clean, aged water immediately, "
        "and repeat if fish keep gasping.\n"
        "2. Increase aeration - a splash/paddle, an aerator, or even pouring water "
        "to break the surface.\n"
        "3. Stop feeding for 1-2 days; uneaten feed is the main source of ammonia. "
        "Remove dead fish.\n"
        "4. Apply agricultural lime to stabilise pH if it is swinging (about "
        "50-100 kg/ha, per guidance).\n\n"
        "Prevent it: feed only what the fish clear in a few minutes (about 3-5% of "
        "body weight per day), do regular partial water changes, and avoid "
        "overstocking.",
    ),
    # Cattle lumpy skin disease (Sokoto, pastoral)
    (
        "I am a cattle herder in Sokoto State, Nigeria. Several of my cattle have "
        "developed firm lumps all over the skin, with fever and reduced milk. What "
        "is this disease and what should I do?",
        "Firm, raised skin nodules over much of the body, with fever and a drop in "
        "milk, is Lumpy Skin Disease (LSD), a viral disease of cattle spread "
        "mainly by biting insects (flies, mosquitoes) and ticks.\n\n"
        "Confirm it: many circular, firm skin nodules (often 2-5 cm), fever, "
        "watery eyes/nose, enlarged lymph nodes, and swollen legs in some "
        "animals.\n\n"
        "What to do - there is no cure for the virus, so treat supportively and "
        "stop the spread:\n"
        "1. Isolate affected cattle from the rest of the herd immediately.\n"
        "2. Clean the skin nodules/wounds with antiseptic; a vet may give an "
        "antibiotic for secondary bacterial infection and an anti-inflammatory for "
        "the fever and pain. Keep the animals well fed and watered.\n"
        "3. Control the biting insects and ticks that spread it (pour-on/spray "
        "insecticide or repellent at the label rate).\n"
        "4. Report it - LSD is a notifiable disease in many areas.\n\n"
        "Prevention: vaccinate the whole herd before the biting-fly season. "
        "Because the disease has a long incubation, newly bought or recently "
        "exposed animals can still break down after vaccination, so vaccinate "
        "early and quarantine new stock.",
    ),
    # Tomato tuta absoluta (dry-season, Kano)
    (
        "I am a dry-season tomato farmer in Kano State, Nigeria. My tomato leaves "
        "have winding, blister-like tunnels and the fruits have small boreholes. "
        "What is causing this and how do I stop it?",
        "The winding, blister-like tunnels (mines) in the leaves and the small "
        "boreholes in the fruit are caused by Tuta absoluta, the tomato leaf "
        "miner (sometimes called 'tomato ebola'). It is a severe dry-season pest "
        "in the north and builds resistance to chemicals quickly.\n\n"
        "Confirm it: irregular, translucent leaf mines with dark frass inside, "
        "pinhole entries in fruit, and tiny caterpillars within the mines.\n\n"
        "Control:\n"
        "1. Hang Tuta absoluta pheromone traps to monitor and mass-trap the male "
        "moths; water-pan traps with a light at night also catch many.\n"
        "2. Remove and destroy mined leaves and infested fruit - do not leave them "
        "in the field.\n"
        "3. Spray at first mines with Bt or spinosad, or emamectin benzoate / "
        "chlorantraniliprole at the label rate. Rotate between different chemical "
        "groups every application - resistance is a serious problem with this "
        "pest.\n\n"
        "Prevention: raise seedlings under insect-proof nets, keep strict field "
        "sanitation, rotate away from tomato/pepper/eggplant, and do not plant "
        "next to an old, infested crop. Follow the label rate and pre-harvest "
        "interval.",
    ),
    # Rice bacterial leaf blight (Kebbi)
    (
        "I am a rice farmer in Kebbi State, Nigeria. My rice leaves are drying "
        "from the tips and edges with yellow, water-soaked streaks turning "
        "straw-white. Is this brown spot, and what should I do?",
        "No - drying from the leaf tips and margins with yellow, water-soaked "
        "streaks that turn straw-white is Bacterial Leaf Blight (Xanthomonas "
        "oryzae), a bacterium, not brown spot (which makes small round brown "
        "'sesame-seed' spots).\n\n"
        "Confirm it: lesions that start at the leaf tip or edge and run down with "
        "wavy yellow margins, and - if you cut an infected leaf and put it in "
        "clear water - a milky bacterial ooze.\n\n"
        "What to do (there is no strong chemical cure, so manage it):\n"
        "1. Cut back nitrogen - excess or late urea makes bacterial blight much "
        "worse. Split your nitrogen and do not over-apply.\n"
        "2. Improve drainage and avoid deep, stagnant flooding and leaf injury, "
        "which spread the bacteria.\n"
        "3. Remove weed hosts on the bunds and use clean seed.\n"
        "4. A copper-based bactericide at the label rate can give limited help "
        "early, but it will not rescue a severe case.\n\n"
        "Prevention is the real answer: plant resistant varieties, use balanced "
        "fertilizer, and keep the field clean. For next season choose a "
        "blight-resistant variety and certified seed.",
    ),
    # Maize streak virus (Benue)
    (
        "I am a maize farmer in Benue State, Nigeria. Some plants have fine broken "
        "yellow streaks running along the leaves and are badly stunted. What is "
        "this and how do I manage it?",
        "Fine, broken yellow streaks running parallel to the veins, with stunting, "
        "is Maize Streak Virus (MSV). It is spread by leafhoppers, not by seed, "
        "and shows up in patches across the field.\n\n"
        "Confirm it: pale yellow dashes/streaks along the leaf length (not the "
        "even yellowing of nitrogen shortage), worst on young plants, which stay "
        "stunted and may not produce a cob.\n\n"
        "Management - there is no cure for the virus, so prevent it:\n"
        "1. Plant MSV-resistant/tolerant varieties - this is the single most "
        "effective control, and good tolerant hybrids are available.\n"
        "2. Plant early and at the same time as your neighbours to escape the peak "
        "leafhopper flights that carry the virus.\n"
        "3. Control leafhoppers early: an imidacloprid seed treatment, or a foliar "
        "insecticide at the label rate when leafhoppers are seen on young "
        "plants.\n"
        "4. Rogue (pull out) badly infected young plants and control grassy weeds "
        "around the field, which host leafhoppers and the virus.",
    ),
    # Pepper anthracnose (Kaduna)
    (
        "I am a pepper farmer in Kaduna State, Nigeria. My ripening pepper fruits "
        "have sunken dark circular spots with rings, and some rot on the plant. "
        "What is it and how do I treat it?",
        "Sunken, dark, circular spots with concentric rings on ripening pepper "
        "fruit is anthracnose (the fungus Colletotrichum), which rots the fruit "
        "before and after harvest, worse in wet, humid weather.\n\n"
        "Confirm it: round, sunken lesions on ripening/ripe fruit, often with "
        "concentric rings and small dark or pink spore masses in the centre.\n\n"
        "Treatment:\n"
        "1. Remove and destroy infected fruit promptly - do not leave them in the "
        "field to spread spores.\n"
        "2. Spray mancozeb (Dithane M-45) at ~2.5 g/L or chlorothalonil at the "
        "label rate, every 7-10 days from fruit set through ripening, especially "
        "in wet weather.\n"
        "3. Stake and space plants for airflow and avoid overhead watering late in "
        "the day.\n\n"
        "Prevention: use clean or fungicide-treated certified seed, rotate away "
        "from pepper/tomato for 2-3 seasons, mulch to stop soil splash, and "
        "harvest ripe fruit promptly and dry it well. Follow the label rate and "
        "pre-harvest interval.",
    ),
    # Broiler heat stress (management, northern dry season)
    (
        "I am a poultry farmer in Maiduguri, Borno State, Nigeria. In the "
        "afternoon heat my broilers pant, spread their wings, crowd around the "
        "drinkers, stop eating, and a few have died. What is happening and what "
        "should I do?",
        "Panting, spread wings, crowding at the drinkers, going off feed and "
        "afternoon deaths are classic heat stress, not an infection - broilers "
        "struggle in the northern dry-season heat because they cannot sweat.\n\n"
        "Confirm it: the signs appear in the hottest part of the day and ease in "
        "the cool evening, and the birds are otherwise normal (no twisted necks, "
        "no bloody droppings).\n\n"
        "What to do now:\n"
        "1. Give unlimited cool, clean water and add vitamin C or an electrolyte/"
        "anti-stress mix (about 1 g/L) to the water during hot hours.\n"
        "2. Improve airflow: open the house sides, add fans, and reduce stocking "
        "density to cut crowding and body heat.\n"
        "3. Feed in the cool early morning and evening; withdraw feed during peak "
        "heat (digestion raises body heat).\n"
        "4. Cool the house: wet the roof, hang wet sacks/curtains, and ensure "
        "shade.\n\n"
        "Prevent it: orient and insulate the roof, give enough drinker space, "
        "raise heat-tolerant stock where possible, and keep birds calm - avoid "
        "handling or transporting them in the heat of the day.",
    ),
    # Goat mastitis (dairy, Fulani)
    (
        "I am a goat farmer in Adamawa State, Nigeria. One of my nanny goats has a "
        "hot, swollen udder and the milk is watery with clots. She is off feed. "
        "What is wrong and how do I treat her?",
        "A hot, hard, swollen udder with abnormal (watery, clotted, or bloody) "
        "milk and a goat off feed is mastitis - an infection and inflammation of "
        "the udder, usually bacterial.\n\n"
        "Confirm it: swelling, heat and pain in one or both halves of the udder, "
        "milk that is watery, clotted, discoloured or foul, and sometimes fever.\n\n"
        "Treatment:\n"
        "1. Strip out (milk out) the affected half completely and often - several "
        "times a day - to remove infected milk.\n"
        "2. Use an intramammary antibiotic tube after milking, and for a goat that "
        "is feverish or off feed, a systemic antibiotic plus an anti-inflammatory - "
        "get these from a vet, who will choose the right drug and dose.\n"
        "3. Observe the milk and meat withdrawal period on any drug before the "
        "milk is used or the animal sold.\n"
        "4. Discard the abnormal milk; do not feed it to kids or people.\n\n"
        "Prevention: wash hands and the udder before milking, dip or disinfect "
        "teats after milking, keep clean dry bedding, milk infected animals last, "
        "and cull goats with repeated chronic mastitis.",
    ),
]

META = [
    # Hidden P3: compressing knowledge for low-cost hardware
    (
        "Propose a method for compressing local agricultural knowledge datasets to "
        "fit within the memory constraints of low-cost hardware while maintaining "
        "high predictive accuracy for localized planting schedule optimizations.",
        "The key is to compress the model and to stop trying to memorize every "
        "fact in its weights - keep facts in a small retrieval store instead. All "
        "of this runs on the device, with no cloud:\n\n"
        "1. Quantize the model: convert the weights to 4-bit GGUF (for example "
        "Q4_K_M). This cuts memory roughly four times with very little accuracy "
        "loss, so a 1-2 billion parameter model fits in under 2 GB of RAM.\n"
        "2. Distil and prune: train a small model to imitate a larger one, and "
        "remove redundant parameters, so the useful knowledge is kept in a much "
        "smaller footprint.\n"
        "3. Curate and deduplicate the training data: quality beats quantity - a "
        "clean, deduplicated set prevents the model wasting capacity memorizing "
        "noise and improves accuracy per megabyte.\n"
        "4. Use retrieval (RAG) for the specific, changing facts - planting "
        "calendars, local variety notes, prices. Store them as plain text in a "
        "small on-device vector database (a few megabytes) with a lightweight "
        "INT8 embedding model, and fetch the relevant passage at question time.\n\n"
        "This split - a small quantized model for reasoning plus a compact local "
        "knowledge store for facts - is how Homa fits useful agricultural "
        "intelligence onto a budget laptop while staying accurate and fully "
        "offline.",
    ),
    # Hidden P1 variant: staying accurate offline over time
    (
        "How can an offline on-device agricultural assistant stay accurate and up "
        "to date when the device has little or no internet connectivity?",
        "By separating slow-changing knowledge from fast-changing knowledge, and "
        "treating any connection as an optional bonus:\n\n"
        "1. Bake stable agronomy into the model weights: crop biology, disease "
        "diagnosis, and treatment principles change slowly, so they can live in "
        "the model and need no updates to stay correct.\n"
        "2. Keep fast-changing or local information - new pest advisories, seasonal "
        "calendars, market prices - in an on-device knowledge base the assistant "
        "retrieves from. This is far easier to refresh than retraining a model.\n"
        "3. Update opportunistically, never as a requirement: refresh the "
        "knowledge base during a brief connection when one is available, or by "
        "copying an updated file from a USB drive handed out at an extension "
        "office (sneakernet). Between updates the assistant is fully functional.\n"
        "4. Be honest about limits: for anything time-sensitive it does not know, "
        "the assistant should say so and point the farmer to local extension.\n\n"
        "The design principle is offline-first: the system must give reliable help "
        "with zero network, and only get better when a connection happens to be "
        "there.",
    ),
    # Running an LLM on 8GB / CPU
    (
        "What does it take to run a useful AI language model on a low-cost laptop "
        "with 8 GB of RAM and no graphics card?",
        "It is very achievable with the right choices - this is exactly the target "
        "Homa is built for:\n\n"
        "1. Use a small model: 1-2 billion parameters is enough for a focused "
        "domain like farming advice, and it leaves room for the operating system.\n"
        "2. Quantize it to 4-bit GGUF (e.g. Q4_K_M) so the weights take under 2 GB "
        "of RAM instead of 6-8 GB at full precision.\n"
        "3. Run it on the CPU with llama.cpp, which is optimized for CPU "
        "inference and needs no graphics card. Pin it to the available cores "
        "(for example 4 threads) to avoid contention.\n"
        "4. Keep the context window modest (for example 4096 tokens) - longer "
        "context uses more RAM - and use memory-mapped weights so the model loads "
        "quickly and shares memory.\n"
        "5. Don't load two large models at once; use a small INT8 embedding model "
        "for any retrieval.\n\n"
        "With these choices a budget laptop can reach usable speed (Homa runs at "
        "over 20 tokens/second) inside the 8 GB memory limit, entirely offline.",
    ),
    # Image diagnosis offline (complements hidden P2)
    (
        "How can a farmer get a crop problem diagnosed from a phone photo when "
        "there is no internet and no cloud image service?",
        "By running a small image model on the phone itself and combining it with "
        "simple visual rules, so nothing leaves the device:\n\n"
        "1. Put a compact, quantized image classifier (for example a MobileNet "
        "converted to TensorFlow Lite or ONNX) on the phone, trained on locally "
        "collected, labelled photos of the common local problems.\n"
        "2. Use clear visual cues to separate causes: an even colour change spread "
        "smoothly over the leaf usually means a nutrient problem (for example even "
        "yellowing for nitrogen), while irregular damage - holes, chewed edges, "
        "winding mines, webbing, or spots with sharp borders - usually means a "
        "pest or disease.\n"
        "3. Help the low-quality camera: photograph a single leaf, close up, in "
        "natural light, and take a few shots.\n"
        "4. When the model is not confident, ask the farmer one or two guided "
        "questions ('are there insects or holes, or just colour change?') to "
        "confirm.\n\n"
        "Paired with a text assistant like Homa, this gives an offline "
        "photo-to-advice path with no cloud vision API.",
    ),
    # Safety / reliability guardrails offline
    (
        "How do you make sure an offline farming AI gives safe, reliable advice "
        "when there is no human expert checking each answer?",
        "Safety has to be built into the data and the behaviour, since no one is "
        "reviewing each reply:\n\n"
        "1. Train only on curated, expert-checked agronomy, and deduplicate it so "
        "the model learns correct, consistent answers rather than noise.\n"
        "2. Make chemical advice safe by design: give realistic rate ranges, and "
        "always tell the farmer to follow the product label for the exact rate and "
        "the pre-harvest interval, and to rotate chemical groups to avoid "
        "resistance.\n"
        "3. Defer where a mistake is costly: for uncertain diagnoses, dangerous "
        "dosages, or human medical issues (like a snakebite), point the farmer to "
        "local extension or a clinic instead of guessing.\n"
        "4. Refuse unsafe or out-of-domain requests in character - for example, "
        "spraying a veterinary dewormer on vegetables, or off-topic tasks.\n"
        "5. Ground answers in a local knowledge base where possible, and be honest "
        "about uncertainty - ask a clarifying question rather than inventing "
        "detail.\n\n"
        "These are the principles Homa follows so that offline advice stays "
        "trustworthy.",
    ),
    # Farmer data privacy on-device
    (
        "Is my farm information private if I use an on-device offline AI "
        "assistant?",
        "Yes - that is one of the main benefits of running fully on your own "
        "device. Because the assistant does all its work locally and makes no "
        "cloud calls, your questions, photos, and farm details never leave the "
        "device: nothing is uploaded, nothing is logged on a remote server, and "
        "nothing is shared with anyone.\n\n"
        "This matters in two ways:\n"
        "1. Privacy: your farm's problems, yields, and locations stay yours.\n"
        "2. It works anywhere, even with untrusted or no connectivity, because it "
        "never depends on sending your data out.\n\n"
        "Any updates flow one way only - new knowledge comes in (through an "
        "occasional connection or a USB update) - while your personal information "
        "stays on the device. Homa is designed this way on purpose.",
    ),
    # The small-model + RAG engineering tradeoff
    (
        "Why use a small quantized model with a local knowledge base instead of a "
        "large, more capable model for an offline farming assistant?",
        "Because on the hardware real farmers have, reliability and deployability "
        "matter more than raw model size:\n\n"
        "1. A large model will not fit in the memory of a $150-500 laptop with 8 "
        "GB of RAM, or will run so slowly and hot that it is unusable - and if it "
        "exceeds the memory limit it simply fails. The best model on paper is "
        "useless if it cannot run.\n"
        "2. A small model quantized to 4-bit fits comfortably and runs fast on a "
        "plain CPU, so a farmer gets an answer in seconds, offline.\n"
        "3. Grounding that small model in a local knowledge base (retrieval) gives "
        "it accurate, specific facts without needing billions more parameters - "
        "the knowledge lives in a few megabytes of text, not in the weights.\n\n"
        "So the engineering choice is deliberate: a small, efficient, grounded "
        "system that reliably runs on the target device beats a larger one that "
        "does not. That trade-off - efficiency and deployability first - is the "
        "core of how Homa was designed.",
    ),
    # Designing for intermittent power/connectivity
    (
        "How should an AI assistant for rural farmers be designed for places with "
        "intermittent electricity and little connectivity?",
        "Design it offline-first and low-power, so it works in the hardest "
        "conditions and only improves when resources are available:\n\n"
        "1. Full function with zero network: every core feature - advice, "
        "diagnosis, retrieval - must run with no internet at all. Connectivity is "
        "treated as an optional bonus for occasional updates, never a "
        "requirement.\n"
        "2. Low energy draw: a small quantized model on the CPU uses far less "
        "power than a large model needing a graphics card, so it suits laptops run "
        "off limited mains or solar power, and drains the battery slowly.\n"
        "3. Fast start and low memory: memory-mapped 4-bit weights load quickly "
        "and fit in 8 GB, so the assistant is ready even on modest, older "
        "machines.\n"
        "4. Graceful updates: knowledge-base refreshes can arrive by a brief "
        "connection or a USB drive, and are applied without interrupting offline "
        "use.\n\n"
        "The result is an assistant that is dependable exactly where "
        "infrastructure is weakest - which is the whole point of Homa.",
    ),
]

GOLD_PERSONA = PERSONA + META


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    with open(args.out, "w", encoding="utf-8") as f:
        for instruction, response in GOLD_PERSONA:
            f.write(json.dumps({"instruction": instruction, "response": response},
                               ensure_ascii=False) + "\n")
    print(f"Wrote {len(GOLD_PERSONA)} rows "
          f"({len(PERSONA)} persona + {len(META)} meta) -> {Path(args.out).name}")


if __name__ == "__main__":
    main()
