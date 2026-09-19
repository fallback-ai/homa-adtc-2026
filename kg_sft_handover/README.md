# Homa Knowledge Graph (KG) to SFT Synthesis — Team Handover & Guide

**Target Branch:** `semifinal`  
**Artifact Directory:** [`kg_pipeline_checkpoints/`](../kg_pipeline_checkpoints/)  
**Status:** Knowledge Graph constructed and traversed. Stage 4 paths available for SFT synthesis.

---

## 1. Executive Summary & What Was Just Completed

We have successfully extracted, canonicalized, and traversed an authoritative **Agricultural Knowledge Graph** across our entire Nigerian agricultural corpus (110+ authoritative PDFs across crops, veterinary medicine, aquaculture, poultry, postharvest value-addition, and agribusiness surveys).

The resulting files have been committed and pushed to `semifinal` under [`kg_pipeline_checkpoints/`](../kg_pipeline_checkpoints/):

| File | Records / Nodes | Description |
| :--- | :--- | :--- |
| **`stage1_corpus_chunks.jsonl`** | 2,935 chunks | Context-preserving ~3,000 char chunks with category taxonomy metadata. |
| **`stage2_extracted_triples.jsonl`** | 2,774 extractions | Triples extracted using `Qwen/Qwen2.5-7B-Instruct` (fp16, dual T4 GPUs) under a strict 21-entity, 21-predicate ontology with verbatim source sentences. |
| **`stage3_resolved_graph.json`** | **25,635 nodes, 40,078 edges** | Multi-directed Knowledge Graph resolved using canonical entity matching (`difflib` similarity @ 0.85). |
| **`stage4_traversed_paths.jsonl`** | **221 decision paths** | Complete multi-hop agronomic decision paths across 4 domains, fully grounded with source sentences and document citations. |

---

## 2. Why This Is Critical for Homa's Accuracy & Evaluation

In real smallholder agricultural advisory, a farmer rarely asks a simple single-fact question. Real queries are **multi-hop diagnostic & decision workflows**:

$$\text{Host} \longrightarrow \text{Symptom/Sign} \longrightarrow \text{Stressor/Pathogen} \longrightarrow \text{Intervention} \longrightarrow \text{Dosage Rate} \longrightarrow \text{Timing} \longrightarrow \text{Withdrawal Period}$$

### The Failure of Naive Text RAG
When a model is trained on ungrounded or unstructured text chunks:
1. **Dosage & Rate Hallucination:** Models confuse spray volumes (e.g. recommending 4 L/ha of a chemical meant for 200 ml/ha, or recommending cattle dosages for poultry).
2. **Missing Boundary Defense:** Models answer off-topic queries (e.g. writing resignation letters or betting tips) instead of staying anchored in agronomy.
3. **Lack of Look-alike Disambiguation:** Models fail to warn farmers when symptoms of Fall Armyworm resemble Stem Borer, or Cassava Mosaic resembles nutrient deficiency.

### How Traversed KG Paths Fix This
Every record in `stage4_traversed_paths.jsonl` binds together:
- The exact host, symptoms, and causal agent.
- The chemical or cultural control.
- Quantitative rates (kg/ha, ml/L, mg/kg), application timings, and withdrawal periods.
- Look-alike confusable stressors.
- **Verbatim source grounding sentences** and document paths that support every single link in the chain.

By synthesizing SFT training pairs directly from these paths, Homa learns **grounded relational reasoning** that cannot hallucinate dosages or invert steps.

---

## 3. What I Am Running From My End (Kaggle: Cells 10 & 11)

On my end, I am running **Stage 5** inside the Kaggle notebook via dual-T4 offline `vLLM`:

- **Model:** `Qwen/Qwen2.5-7B-Instruct` (fp16, `tensor_parallel_size=2`).
- **Structured Output:** Pydantic schema enforcing `{"instruction": "...", "response": "..."}`.
- **Sophisticated Diversity Engine (Anti-Repetition):**
  - **8 Smallholder Inquiry Archetypes:**
    1. *Visual Symptom Inquiry:* Physical signs described in field terms without technical jargon; asks for field confirmation & diagnosis.
    2. *Emergency Outbreak:* Sudden urgent infestation/mortality; demands fast knockdown rescue chemical, rates, and PHI/withdrawal.
    3. *Low-Cost Cultural & Organic Control:* Smallholder cash constraints; prioritizes sanitation, neem/ash, resistant seed, and threshold management.
    4. *Dosage Calibration & Measures:* Smallholder metric/local conversions (bottle caps, matchboxes, 15L/16L/20L knapsacks) and WAP timing.
    5. *Seasonal Planning & Agronomy:* Pre-planting guidance across Nigerian agroecological zones (Sudan, Guinea, Rainforest, Fadama).
    6. *Postharvest Preservation & Storage:* Curing, safe moisture (<12-14%), PICS hermetic bags, aflatoxin/cyanide reduction.
    7. *Livestock & Aquaculture Husbandry:* Balanced rations, water quality (pH, DO), ventilation, NVRI Vom vaccines (I-2), withdrawal periods.
    8. *Adversarial Boundary Defense (~10%):* Legit agricultural question paired with realistic off-topic distractions; answers farming thoroughly first, politely deflects distraction in authentic Homa voice.
  - **Enforced Response Actionability (`RESPONSE_STYLE.md`):** Product (concrete commercial/generic name), Rate (kg/ha, ml/L, or smallholder units), Timing (WAP / stage), Method (band placement, foliar spray wetting undersides), Safety (PPE and PHI).
  - **Look-alike Disambiguation & Quick Field Tests:** Clarifying confusable diseases (e.g. Whitefly/TYLCV vs Aphids, Brown Spot vs Blast vs BLB) with 30-second field confirmation tests.
  - **Automated Grounding Audit:** Regex extraction of numerical claims confirming evidence backing; ungrounded claims diverted to audit file.
  - **Bucketed Near-Duplicate Detection:** Pairwise similarity checks within domain/crop buckets to flag responses with $>85\%$ similarity.
  - **Clean Export & Idempotent GitHub Push (Cell 12):** Automatically stages, computes checksums, commits, and pushes clean SFT datasets into `sft_train_samples/` (`homa_kg_stage5_sophisticated_sft.jsonl`, `homa_kg_stage5_sophisticated_sft_clean.jsonl`, etc.) on branch `semifinal`.

---

## 4. How You (Teammates) Can Generate SFT Pairs from Your End

You don't need to touch Stages 1–3 or re-build the graph. You can pull the `semifinal` branch and run your own SFT synthesis directly on:

📂 **`kg_pipeline_checkpoints/stage4_traversed_paths.jsonl`**

Having multiple synthesis runs (e.g. Kaggle Qwen2.5 vs. your API/Assistant run) allows us to **compare, cross-audit, and assemble a much stronger, more diverse training dataset**.

### Method A (Recommended): LLM API Script (OpenAI / Claude / Gemini / Together / Groq)

You can run a fast Python synthesis script over the 221 paths using any commercial LLM API. 

Here is a ready-to-run script template:

```python
"""
save as: run_sft_api_synthesis.py
run: python run_sft_api_synthesis.py
"""
import json
import os
import random
from openai import OpenAI  # Or google-genai, anthropic

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

INPUT_PATHS = "kg_pipeline_checkpoints/stage4_traversed_paths.jsonl"
OUTPUT_FILE = "sft_train_samples/sft_pairs_teammate_api.jsonl"

NIGERIAN_STATES = ["Kaduna", "Kano", "Benue", "Oyo", "Plateau", "Nasarawa", "Niger", "Taraba", "Kebbi", "Ondo"]
STYLES = ["conversational", "short_steps", "comprehensive"]

def synthesize_pair(path_record):
    ptype = path_record.get("path_type")
    evidence = "\n".join(f"- {s}" for s in path_record.get("grounding_sentences", []))
    state = random.choice(NIGERIAN_STATES)
    style = random.choice(STYLES)
    
    prompt = f"""You are synthesizing an agricultural training pair for 'Homa', an AI assistant for Nigerian farmers.
GROUNDING EVIDENCE (STRICT: DO NOT INVENT NUMBERS OUTSIDE THIS TEXT):
{evidence}

KNOWLEDGE GRAPH DATA:
Host: {path_record.get('host')}
Type: {ptype}
Details: {json.dumps(path_record)}

REQUIREMENTS:
1. Instruction: Natural farmer query based in {state} State.
2. Response: Grounded response ({style} style). Lead with direct actionable advice.
3. NEVER hallucinate dosage rates or numbers not in the evidence.

Return ONLY a JSON object with keys: "instruction" and "response"."""

    response = client.chat.completions.create(
        model="gpt-4o",  # or claude-3-5-sonnet, gemini-2.0-flash
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return json.loads(response.choices[0].message.content)

# Run batch
with open(INPUT_PATHS, "r", encoding="utf-8") as fin, open(OUTPUT_FILE, "a", encoding="utf-8") as fout:
    for idx, line in enumerate(fin):
        if not line.strip(): continue
        rec = json.loads(line)
        try:
            pair = synthesize_pair(rec)
            fout.write(json.dumps(pair, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"Synthesized {idx + 1}/221")
        except Exception as e:
            print(f"Error on {rec.get('path_key')}: {e}")
```

### Method B: Using an AI Coding Assistant (Antigravity / Cursor / Claude Desktop)
If you prefer not using API keys directly:
1. Open [`kg_pipeline_checkpoints/stage4_traversed_paths.jsonl`](../kg_pipeline_checkpoints/stage4_traversed_paths.jsonl).
2. Feed slices of paths (e.g., 20 at a time) to your assistant with the prompt template above.
3. Ask the assistant to output pure JSONL matching `{"instruction": "...", "response": "..."}`.
4. Save the generated lines into a new file in `sft_train_samples/`.

---

## 5. Next Steps & Merging Plan

```
[Kaggle Qwen2.5-7B Run] ──► stage5_sft_pairs_clean.jsonl ──┐
                                                           ├──► [Deduplication & Grounding Audit]
[Teammate API/Assistant Run] ──► sft_pairs_teammate.jsonl  ──┘                 │
                                                                               ▼
[Somto's Clean Baseline: combined_train.v2.en.jsonl] ────────► [FINAL MERGED SFT DATASET]
                                                                               │
                                                                               ▼
                                                            [Run Training: train_qwen15b.py]
```

1. **Comparison:** When both runs finish, we compare response quality, tone, and formatting consistency.
2. **Deduplication:** Run a pairwise sequence matcher across both datasets to remove duplicate questions.
3. **Merge:** Combine the high-confidence KG pairs directly into Somto's baseline (`sft_train_samples/combined_train.v2.en.jsonl`).
4. **Fine-Tuning:** Kick off our SFT run (`training/train_qwen15b.py`) with complete multi-hop reasoning baked in!
