# Training Dataset Information (Gate 2)

This document provides dataset names, sources, record counts, and cryptographic checksums used for fine-tuning **Homa-Qwen2.5-1.5B** for Gate 2, as required by the ADTC 2026 submission specifications.

---

## Primary Fine-Tuning Dataset

| Attribute | Specification |
| :--- | :--- |
| **Dataset Name** | `combined_train_v5_clean.jsonl` |
| **File Location** | [`sft_train_samples/combined_train_v5_clean.jsonl`](../sft_train_samples/combined_train_v5_clean.jsonl) |
| **Record Count** | **2,577** curated instruction–response pairs |
| **Language Scope** | English (`en`), tailored to Nigerian smallholder agriculture |
| **Format** | JSON Lines (`{"instruction": str, "response": str}`) |
| **SHA256 (LF Normalized)** | `cb81966edce3df73984e992059215a7959957b1be2314923e5b2e83679529f0a` |
| **Online Source URL** | [`https://github.com/fallback-ai/homa-adtc-2026/blob/semifinal/sft_train_samples/combined_train_v5_clean.jsonl`](https://github.com/fallback-ai/homa-adtc-2026/blob/semifinal/sft_train_samples/combined_train_v5_clean.jsonl) |

---

## Dataset Composition & Provenance

The 2,577 clean records in `combined_train_v5_clean.jsonl` are composed of:

1. **Cleaned Agronomic Base (v4 Baseline):** 2,264 rows curated from KisanVaani QA (Apache-2.0), electricsheepafrica Nigeria facts (MIT), and IITA Open Access extension reports (CC-BY-4.0).
2. **Knowledge Graph Decision Paths:** 252 clean, multi-hop agronomic decision paths extracted from 110+ Nigerian agricultural extension manuals across crops, livestock, poultry, and aquaculture.
3. **Corrective Gold Benchmarks:** 61 hand-authored gold pairs enforcing strict out-of-domain safety boundaries, Nigerian agroecological grounding, and offline assistant identity.

---

## Detailed Licensing & Source Attribution

For complete terms of use, generator disclosures, and RAG document licensing, see [`datasets/DATA_LICENSING.md`](./datasets/DATA_LICENSING.md).
