# OMOP and multimodal source survey (2026-09-23, aggregate counts only)

Status: **observed inventory, not a source decision.** Per `docs/RESTART_PLAN.md`, raw
JDAT remains the intended source of truth. OMOP gold is a candidate convenience layer
for covariates and endpoints. Its mappings have not been validated against JDAT.
Related: `RUN_RBC_OMOP_DISCOVERY.md`, `RUN_EXISTING_OMOP_AUDIT.md`,
`CARDS_MISC_OMOP_PSM_AUDIT.md`.

## Candidate OMOP: `/mnt/raid0/rbc58/omop/gold`
Built from the CarDS_2435227 Data-2025-04-03 extract. Hive-partitioned by `year=`, with date32 dates.

| Table | Rows | Notes |
|---|---|---|
| person | 880K | `person_source_value` = MRN. This is the crosswalk to notes, ECG and echo |
| death | 103K | date only, **no cause of death** |
| observation_period | 880K | **unusable**: start ≈ birth date. Derive look-back from the first visit or event |
| visit_occurrence | 32.5M | inpatient 9201 = 1.10M (387K persons, dense 2013–2025), ED 2.4M, outpatient 29M |
| condition_occurrence | 155M | `condition_status_source_value` has the dx source and primary flag (`HOSPITAL_BILLING_DX Y` = principal). **No visit_occurrence_id**, so link to visits by person and date |
| drug_exposure | 126M | carvedilol 50K persons, metoprolol 179K, sacubitril 7.7K, lisinopril 145K, enalapril 8K |
| measurement | 410M | 83 concepts: full vitals, CBC, CMP/BMP, LFTs, lipids, A1c, TSH, INR, NT-proBNP (558K), troponins, CRP. No LVEF, no Mg |
| procedure_occurrence | 469M | 88% concept_id = 0, so **use the CPT source value**: ECG, TTE 93306, cath 93458–60, ICD/PPM |
| observation | 26M | unmapped and non-condition codes |

Gotchas:
- A stray root-owned `measurement/TROPTHS_2010_2026.csv` sits in the dataset dir. Glob `*.parquet` explicitly instead of passing the directory to `pyarrow.dataset(dir)`.
- Some dates run into 2026–27, past the extract date. Confirm before setting the administrative censoring date.
- Don't use `silver/`, which is staging.

The old extract `/mnt/raid0/bb2238/ecg_ascvd/omop_database` has no visits, no procedures, only 7 measurement codes and no observation start. It is superseded for any new work. Only the archived legacy pipeline points at it.

## Non-OMOP sources (keyed by MRN)
| Source | Path | Scale | Use |
|---|---|---|---|
| Echo (numeric EF, valve grades) | `/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet` | 661K studies, 2015–2025 | LVEF covariate / HFrEF gate |
| ECG metadata + MUSE diagnosis text | `/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet` | 5.08M ECGs, 2000–2025 | intervals + text flags |
| ECG waveforms | `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs/{fileID}.npy` | — | embeddings |
| Clinical notes (full) | `/mnt/raid0/rbc58/mosaic/mosaic5/notes_parquet/` | 8.36M notes, 482K MRNs, **2021–2026 only** | note embeddings (only for index ≥ 2021 plus a look-back) |
| Older notes | `/mnt/raid0/rbc58/mosaic6/cc_notes_{natural,vhd}` | ~9.5M, 2013–2023 (Aim_1 extract) | earlier indexes, different cohort |
| Raw Epic refresh 2026-04-15 | `/mnt/raid0/rbc58/ecg-tte/shared/source-v1-*` | not in OMOP gold | consider a gold rebuild |

## Endpoint implications
- **HF hospitalization:** a 9201 visit with an I50.* row marked `HOSPITAL_BILLING_DX Y`, matched to the visit by date window.
- **CV death:** not available. Use all-cause death as the primary endpoint, or a proxy (in-hospital death during a CV-principal admission). CV death would need a state death-index request.
