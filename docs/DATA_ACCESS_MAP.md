# Data access map

Last updated 2026-10-01. This map lists every dataset this project can use, where it lives, and how it may be used. It contains no credentials or patient-level data. Detailed inventories are in the linked documents.

## Access rules (all agents)
- **Write only under `/mnt/raid0/rbc58`**, plus code and docs in this repository. **Everything else is read-only:** NFS mounts, other users' `/mnt/raid0` folders and all S3 buckets (see `CLAUDE.md`).
- Report aggregates only, suppress counts of 1–10, and never commit restricted files.
- PhysioNet (MIMIC) and dbGaP agreements restrict sharing data with third parties. The PI authorised agent read and aggregate checks of MIMIC and UKB on 2026-09-30.

## 1. Yale New Haven Health System (primary cohort)

| Source | Location | Notes |
|---|---|---|
| OMOP CDM (in-house mapping, "gold") | `/mnt/raid0/rbc58/omop/gold` | 880K persons; visits, conditions, drugs, measurements, procedures. Details in [DATA_SOURCES.md](DATA_SOURCES.md) |
| Raw Epic refresh (2026-04-15) | `/mnt/raid0/rbc58/ecg-tte/shared/source-v1-*` | Not yet in OMOP gold |
| Echo structured reports | `/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet`; NFS `/mnt/nfs_yale_echo` | 661K studies, 2015–2025 |
| ECG metadata + MUSE text | `/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet` | 5.08M ECGs, 2000–2025 |
| ECG waveforms | `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs/`; NFS `/mnt/nfs_yale_ecg`, `/mnt/nfs_yale_ecg_signals` | Input to the BCL encoder |
| Clinical notes | `/mnt/raid0/rbc58/mosaic/mosaic5/notes_parquet/` (2021–2026); `/mnt/raid0/rbc58/mosaic6/` (2013–2023) | Not used in this project |
| Model weights | NFS `/mnt/nfs_model_saves` | BCL encoder (see [ECG_MODEL.md](ECG_MODEL.md)) |
| Death and cause of death | Linked state vital statistics, as used by the v1.3+ pipeline | Path to be recorded |
| Echo DICOM backup (S3, mounted) | `~/mnt/backup_echo` (profile `backup_echo`) | Also holds MIMIC-IV-ECHO DICOMs |

## 2. MIMIC-IV (external validation in the manuscript)
Full inventory: [v20/MIMIC_FEASIBILITY.md](v20/MIMIC_FEASIBILITY.md). Results: [v20/MIMIC_REPLICATION.md](v20/MIMIC_REPLICATION.md).

| Module | Location | Licence |
|---|---|---|
| MIMIC-IV 3.1 (hosp, icu) | `/mnt/raid0/rbc58/physionet.org/files/mimiciv/3.1/` (own copy); also `/mnt/raid0/bb2238/physionet/…` | PhysioNet credentialed |
| MIMIC-IV-ECG 1.0 (800k ECGs, 161k subjects) | `/mnt/raid0/bb2238/physionet/physionet.org/files/mimic-iv-ecg/1.0`; copies in `/mnt/raid0/pp675/…`, NFS | ODbL (open) |
| MIMIC-IV 2.2, Note 2.2, ED 2.2, CXR | NFS `/mnt/nfs_yale_ecg/mimic/physionet.org/files/` | Credentialed; **note text is never read by agents** |
| MIMIC-IV-ECHO 0.1 | Lists in `/mnt/raid0/ak3398/physionet.org/files/mimic-iv-echo/`; DICOMs on the echo backup mount | Credentialed |
| Echo structured measurements (91k subjects) | `/mnt/raid0/gih5/…/echobench/structured-measurement.csv` | Provenance unconfirmed; not used |
| Our derived outputs | `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-*`, `claude-v20-mimic-*` | Restricted |

## 3. UK Biobank (analysed; **excluded from the manuscript**, PI decision 2026-10-01)
Full inventory: [v20/UKB_FEASIBILITY.md](v20/UKB_FEASIBILITY.md). Results: [v20/UKB_ANALYSIS.md](v20/UKB_ANALYSIS.md).

| Asset | Location |
|---|---|
| Main dataset, CMR phenotypes, 20205 ECG XML, CMR images | S3 mounts `~/mnt/ukb-s3` (profile `ukb_s3`) and `~/mnt/biobank-mri-1` (profile `biobank-mri-1`); read-only |
| ECG npy (93k ECGs, 84k participants) | `/mnt/raid0/bb2238/signals/preprocessed/ukb_2025/` |
| Our BCL embeddings | `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-ukb-bcl/` |
| Participant export (RAP-style) | `/mnt/raid0/rbc58/prs/ukb/data.csv` |
| GP prescriptions and record-level HES | Not local; on the UKB Research Analysis Platform only |

Do not use the genotypes or polygenic scores under `/mnt/raid0/rbc58/prs`. The project excludes genetics.

## 4. NHLBI BioData Catalyst (Seven Bridges): dbGaP controlled access held by the PI
Data are accessible **only inside the BDC workspace**, not on this server. Studies and ECG availability: [v20/COHORT_ECG_AVAILABILITY.md](v20/COHORT_ECG_AVAILABILITY.md). Each study needs the phenotype accession plus the ECG ("Imaging") accession. C1–C4 are consent groups.

| Study | Phenotype / clinical | Raw 12-lead ECG (XML) | Other imaging | Genomics (not used) |
|---|---|---|---|---|
| CHS | phs000287 (C1–C4) | **phs003639** (C1–C4): ~39k, annual visits 1–10 | Echo in phenotypes | phs001368 (TOPMed) |
| Framingham | phs000007 (C1, C2); phs003594 (FHS BioLINCC; C1, C2) | **phs003593** (C1, C2): ~38.5k, 1984–2022; also cardiac CT | — | phs000974 (TOPMed) |
| WHI | phs000200 (C1, C2) | **phs003824** (C1, C2): ~184k, trial participants, 4 visits | — | phs001237 (TOPMed) |
| ACCORD | phs003551 (C1) | **phs003562** (C1): ~41k | — | phs001411 |
| SPRINT | phs003483 (C1) | **phs003566** (C1): ~24k | — | — |
| MESA | phs000209 (C1, C2); phs003288 (MESA BioLINCC; C1, C2) | **phs003703** (C1, C2): ~11k, exams 1 and 5 | **phs003702** (C1, C2): echo images, exam 6 | phs001416 (TOPMed) |
| TOPMed | — | — | — | TOPMED-CONTROLLED |

- File counts come from BDC's public file index.
- The phs001237 and phs001411 mappings are from general knowledge and should be confirmed in the BDC catalog.
- To use these data, port the pipeline (ECG conversion, BCL encoder, PS/matching/balance/emulation) into a BDC workspace and export aggregates only. Check that the approved Data Use Statement covers trial-emulation methods research.

## 5. Other mounts seen (not inventoried)
- `~/mnt/rhdextas` (profile `rhdextas`): contents not reviewed for this project.
