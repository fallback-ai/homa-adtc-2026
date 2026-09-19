# Training Data — Sources, Generation & Licensing

Gate 2 requires that datasets used for fine-tuning are documented with their
licensing. This file covers the data behind `Homa-Qwen2.5-1.5B`.

## Submission training set

- **File:** `sft_train_samples/combined_train.v4.en.jsonl` (2,532 rows). Built by
  `build_v4.py`, which augments the raw corpus `combined_train.en.jsonl` (1,905
  rows) with three external open sources and then reruns the v2 clean + merge
  passes:
  1. **Assemble augmented base** (`combined_train.aug4.en.jsonl`, 2,317 rows):
     raw base (1,905) + filtered KisanVaani QA (692) + aggregated Nigeria
     planting facts (32) + curated IITA-report QA (18), de-duplicated on exact
     (instruction, response).
  2. `clean_base_v2.py --base combined_train.aug4.en.jsonl` →
     `combined_train.aug4.clean.en.jsonl` (2,284 rows): removes RAG-format
     scaffolding, reformats fragment instructions, normalizes typography, and
     collapses duplicates (keeping the most actionable answer).
  3. `build_merged_v2.py --base combined_train.aug4.clean.en.jsonl`: 2,264 base
     rows kept (20 superseded by corrected gold answers) + the hand-authored
     gold set (67 unique examples, oversampled ×4 = 268).
- The additions kept actionability strong: the share of rows flagged
  non-actionable by `audit_actionability.py` fell from 25.6% (v2) to 18.4% (v4).
- **Prior versions:** `combined_train.v3.en.jsonl` (2,514 rows) was base +
  KisanVaani + Nigeria facts + gold; `combined_train.v2.en.jsonl` (1,790 rows)
  was base + gold only. Both retained for comparison.

### External sources (added in v3 / v4)

All are open-licensed and filtered/transformed/paraphrased by team-owned scripts
— no verbatim redistribution of large portions; only a curated, transformed
subset is used for fine-tuning.

- **KisanVaani/agriculture-qa-english-only** (Hugging Face) — **Apache-2.0**.
  22,615-row scraped agriculture Q&A. `build_external_kisanvaani.py` keeps only
  substantive answers (≥160 chars / ≥25 words), drops sentence fragments,
  foreign-locality rows (Uganda/Kenya/India/…), temperate/non-Nigerian crops
  (apple, grape, garlic, …), garbled text, deflections/identity leaks and
  input-advice-without-a-rate, then de-duplicates within the set and against the
  base corpus → **692 rows** (`external_kisanvaani.en.jsonl`).
- **electricsheepafrica/africa-synth-agriculture-crop-planting-harvesting-nigeria**
  (Hugging Face) — **MIT**. 150,000-row *synthetic tabular* dataset
  (state/crop/planting & harvest dates/yields), parameterized from FAO / NBS /
  NiMet / FMARD figures. `build_external_nigeria_facts.py` does **not** parrot
  individual rows; it aggregates per-crop planting windows, time-to-maturity and
  yield ranges into **32** actionable Q&A rows (`external_nigeria_facts.en.jsonl`)
  for the eight annual/root crops. The two perennials (cocoa, oil_palm) are
  excluded because the synthetic planting-to-harvest interval is agronomically
  wrong for tree crops.
- **IITA Reports & Documents** (CGSpace, Hugging-Face-independent) — added in
  **v4**. The collection is institutional/academic prose, so
  `build_external_iita.py` holds **18 hand-authored** rows
  (`external_iita.en.jsonl`) that paraphrase *facts* (not text) from a
  hand-picked set of Open-Access reports into Homa's actionable style, with
  deferral to product labels / soil tests where the report gives the mechanism
  but not a farmer rate. Facts are not copyrightable and no report text is
  reproduced verbatim. Sources (all Open Access):
  - `hdl.handle.net/10568/107315` AgResults Nigeria Aflasafe Challenge 2019
    (**CC-BY-4.0**) — aflatoxin risk & Aflasafe biocontrol.
  - `hdl.handle.net/10568/132851` Soil quality assessment & management plans,
    IITA farms Nigeria (**CC-BY-4.0**) — soil organic matter, acidity, fertility.
  - `hdl.handle.net/10568/180497` Biofortified cassava validation report
    (**CC-BY-4.0**) — vitamin-A (yellow) cassava.
  - `hdl.handle.net/10568/174445` Nutrient Expert (NE) lite (**CC-BY-4.0**) and
    `hdl.handle.net/10568/172781` Agronomy solution profile (**CC-BY-SA-4.0**) —
    site-specific nutrient management.
- **Gold set (67 unique), authored to RESPONSE_STYLE.md:**
  - `build_gold_v2.py` — 45 corrective examples fixing Round-1 judge findings
    (non-actionable advice, wrong diagnoses, identity/OOD/adversarial handling).
  - `build_gold_persona.py` — 14 persona/eval-format examples (first-person,
    location-specific, multi-part; crops/pests not otherwise covered) + 8
    meta/technical examples (offline-architecture questions answered offline-first)
    to cover the hidden-prompt style absent from the base corpus.
- **Schema:** `{"instruction": str, "response": str}`
- **Task:** agronomic advice (crop disease, IPM, fertilizer math, planting) for
  the Nigerian / West-African context.
- **Samples:** see `provenance/datasets/samples/` for a representative excerpt.

### Candidate source: Knowledge-Graph paths (not yet in the submission set)

`sft_train_samples/sft_pairs_kg_claude.jsonl` (**31 pairs**) is a standalone
candidate set, held out of `combined_train.v4.en.jsonl` pending team
cross-audit against the Kaggle Qwen2.5-7B synthesis run (see
`kg_sft_handover/README.md`). It is synthesized by
`build_kg_sft_pairs.py` from the KG stage-4 decision paths
(`kg_pipeline_checkpoints/stage4_traversed_paths.jsonl`), first curated into
grounded evidence bundles by `build_kg_bundles.py` (221 paths → 106 usable
bundles; author/institution/country/abstract hosts and ungrounded paths
dropped). Every number in a response is verified to appear verbatim in the KG
grounding sentences (build-time audit). The underlying knowledge graph was
built over the `knowledge_base/` PDF corpus, so these pairs inherit those
documents' licences — see the RAG corpus table below (to be completed before
any merge into the training set).

## How the data was produced

| Component | Method | Licensing / terms |
| --- | --- | --- |
| Synthetic instruction/response pairs | Generated with Google Gemini and Anthropic Claude, then human review + regeneration passes | Model-generated content. Generated under and used in accordance with each provider's usage terms. No provider ToS prohibiting downstream fine-tuning was violated; `<FILL: confirm current terms at submission time>`. |
| Agronomic grounding facts | Curated by the team from public extension material (IITA, CIMMYT, NVRI, Nigerian wet-season surveys) | Public agronomic guidance. Facts (not verbatim text) were paraphrased into instruction/response form. Source documents: see `knowledge_base/` and `<FILL: list source doc licenses / public-domain status>`. |
| KisanVaani agriculture Q&A (filtered subset) | Downloaded from Hugging Face, filtered/curated by `build_external_kisanvaani.py` | Source **Apache-2.0**; derivative/redistribution permitted. |
| Nigeria crop planting/harvesting facts | Synthetic tabular dataset from Hugging Face, aggregated into Q&A by `build_external_nigeria_facts.py` | Source **MIT**; derivative/redistribution permitted. |
| IITA-report agronomic facts (v4) | Open-Access IITA reports (CGSpace), facts paraphrased into hand-authored Q&A by `build_external_iita.py` | Sources **CC-BY-4.0 / CC-BY-SA-4.0**; facts paraphrased with attribution, no verbatim text. |
| Deduplication / OOD calibration | Team-authored curation scripts | Team-owned. |

> **Action items before submission**
> - Fill row counts and confirm each generator's current terms of use.
> - For every PDF under `knowledge_base/`, record its license or public-domain
>   status in the table below. Remove or replace any source whose license does
>   not permit derivative/redistribution use.

## Knowledge-base source documents (RAG corpus)

The RAG demo indexes PDFs under `knowledge_base/`. These are **not** part of the
model's training data, but are listed here for completeness since the RAG
pairing is described in REPORT.md.

| Source / publisher | Documents | License / status |
| --- | --- | --- |
| IITA | `<FILL>` | `<FILL>` |
| CIMMYT | `<FILL>` | `<FILL>` |
| NVRI | `<FILL>` | `<FILL>` |
| Other | `<FILL>` | `<FILL>` |

## Multilingual data (not shipped in this model)

`sft_train_samples/` also contains Hausa/Igbo/Yoruba datasets from the earlier
multilingual track. They are **not** used by the English-only submission model
and are retained only as research artifacts.
