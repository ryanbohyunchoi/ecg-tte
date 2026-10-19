# CHS AI-EHR arms (EXPLORATORY, post hoc)

**Status: exploratory, added 2026-10-19 after the locked CHS results (`main_v2`) were seen.** These arms are not part of the locked protocol (`docs/bdc/CHS_PROTOCOL.md`). They do not change any locked endpoint, and they are reported as a comparison only, as CLMBR-T is at Yale and in MIMIC-IV.

## Question

Does an AI-EHR representation, built from the same coded information the PS-Codes (hdPS-like) rung uses, add balance on the held-out panel? Does the ECG still add balance on top of it?

## Representations

### A. Crude backbone (`scripts/bdc/chs_backbone.py`)

- **Input:** per emulation row, the same features as PS-Codes (`chs_codes`):
  - 3-digit ICD-9 hospital diagnoses (`D:`) and 2-digit procedures (`P:`) admitted before the visit *k*−1 day;
  - medication-class flags at visit *k*−1 (`M:`). Exposure drugs and the summary flags that contain them are already excluded.
- **Model:** binary TF-IDF (smooth idf), then truncated SVD to 64 components, with codes present in ≥ 20 person-time rows.
- **Fit:** once, on all distinct person-time rows (person × visit *k*−1) across the emulations. It is unsupervised: no treatment, outcome or held-out item enters the fit. Rows with no code get the zero projection.
- **Difference from PS-Codes:** PS-Codes picks the 200 codes that best separate the arms (a treatment-aware ranking). The backbone instead compresses every code without looking at treatment, as a pretrained EHR model would.
- **Output (restricted, stays on BDC):** `chs_ehr_backbone` (row, b0..b63). The aggregate summary is `chs_backbone/report.json` (vocabulary, explained variance, share of rows with any code).

### B. CLMBR-T transfer (planned)

- **Approach:** a MEDS pseudo-timeline per person, with events on or before the visit *k*−1 day. The pretrained CLMBR-T (code-only, as at Yale and in MIMIC-IV) is run on it.
- **Mapping and timeline:**
  - ICD-9-CM → SNOMED through OMOP "Maps to": 964 of 1,037 three-digit categories reach the vocabulary.
  - ICD-9 procedures are used as they are.
  - Admissions become `Visit/IP` and annual clinic visits become `Visit/OP`.
  - Medication classes map to a representative RxNorm ingredient (crude).
  - Lab LOINC presence is coded; history conditions become SNOMED codes at entry.
- **Blocked on three things:**
  - access to the gated model weights;
  - a GPU instance on BDC;
  - uploading the mapping file to BDC (it is SNOMED-derived, so it is not committed to the public repository).

## Arms (added to `chs_emulate.py` with `--ehr backbone|clmbr`)

These are the locked arms plus:
- `base+ehr`: PS-Base plus 64 PCs of the representation (within each emulation);
- `base+ecg+ehr`: PS-Base, the ECG PCs and the representation PCs;
- `base+permehr`: PS-Base plus the representation PCs permuted across rows (placebo).

Estimator, matching, held-out panel and masking are unchanged. The representation contains no lab or vital values, so no extra masking is needed, as for PS-Codes.

**Contrasts reported:**
- base+ehr vs base;
- base+permehr vs base;
- base+ecg+ehr vs base+ecg (EHR on top of ECG);
- base+ecg+ehr vs base+ehr (ECG on top of EHR);
- base+ehr vs PS-Codes.

## Run (BDC)

```bash
python scripts/bdc/chs_backbone.py
python scripts/bdc/chs_emulate.py --protocol-locked --run ehr_backbone --ehr backbone
```

The output goes to `chs_emulate/ehr_backbone/` (aggregates only). The `main_v2` run is not overwritten.

## Caveats

- **Post hoc:** this was added after the locked results were seen. It is descriptive and directional only.
- **Sparse input:** CHS has hospital codes but no outpatient codes. Many person-time rows have only medication flags, so the representation is much sparser than at Yale.
- **Not a pretrained model:** the crude backbone is fitted in-sample on CHS. It is a stand-in for an AI-EHR representation built from the same information, not a foundation model.
