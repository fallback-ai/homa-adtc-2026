# Training Data — Sources, Generation & Licensing

Gate 2 requires that datasets used for fine-tuning are documented with their
licensing. This file covers the data behind `Homa-Qwen2.5-1.5B`.

## Submission training set

- **File:** `sft_train_samples/combined_train.v2.en.jsonl` (1,790 rows). Built in
  two deterministic passes from the raw corpus `combined_train.en.jsonl` (1,905
  rows):
  1. `clean_base_v2.py` → `combined_train.clean.en.jsonl` (1,542 rows): removes
     RAG-format scaffolding from 299 instructions, reformats 136 fragment
     instructions into natural questions, normalizes typography, and collapses
     363 duplicate rows (keeping the most actionable answer).
  2. `build_merged_v2.py --base combined_train.clean.en.jsonl`: 1,522 base rows
     kept (20 superseded by corrected gold answers) + the hand-authored gold set
     (67 unique examples, oversampled ×4 = 268).
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

## How the data was produced

| Component | Method | Licensing / terms |
| --- | --- | --- |
| Synthetic instruction/response pairs | Generated with Google Gemini and Anthropic Claude, then human review + regeneration passes | Model-generated content. Generated under and used in accordance with each provider's usage terms. No provider ToS prohibiting downstream fine-tuning was violated; `<FILL: confirm current terms at submission time>`. |
| Agronomic grounding facts | Curated by the team from public extension material (IITA, CIMMYT, NVRI, Nigerian wet-season surveys) | Public agronomic guidance. Facts (not verbatim text) were paraphrased into instruction/response form. Source documents: see `knowledge_base/` and `<FILL: list source doc licenses / public-domain status>`. |
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
