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

### B. CLMBR-T transfer (`scripts/bdc/chs_clmbr.py`, map from `scripts/bdc/chs_clmbr_map.py`)

- **Model:** pretrained CLMBR-T base (`StanfordShahLab/clmbr-t-base`, Yale revision 5504b35), frozen, code-only, femr 0.2.3 / meds 0.1.3, as at Yale and in MIMIC-IV.
  - It is downloaded on BDC with the user's own Hugging Face access (gated, EHRSHOT licence).
  - The files are checked against the SHA-256 of the Yale copy.
  - The representation is the latest token before the cutoff (768-d), reduced to 64 PCs within each emulation.
- **Pseudo-timeline per emulation × person** (events on or before the visit *k*−1 study day):
  - **Birth:** `MEDS_BIRTH` at entry − (`AGEBL` + 0.5) years. Entry is set to 1989-06-15 for the original cohort and 1992-12-15 for the new cohort, because CHS has study days only. There is no sex or race token, as at Yale.
  - **Entry history:** prior MI, angina, HF, stroke, hypertension, diabetes and AF, one SNOMED code each.
  - **Adjudicated incident events** (MI, angina, angioplasty, bypass, HF, stroke, AF) at their study day.
  - **Each annual clinic visit:** `Visit/OP`, plus the medication-class flags at that visit. Each flag becomes one representative RxNorm clinical drug: the in-vocabulary oral product with the highest CLMBR-T pretraining frequency (crude, since CHS records classes, not drugs).
    - 85 of 99 flags get a token. Summary and non-drug fields get none: any CCB, any diuretic, counts, interviewer ID, days taken.
    - Mibefradil and probucol are not in the vocabulary.
  - **Each hospital admission:** `Visit/IP`, ICD-9-CM → SNOMED through OMOP "Maps to" (falling back to the 3-digit category), and ICD9Proc codes that are in the vocabulary.
- **Not written:**
  - lab and vital codes (protocol measurements on everyone; their values are held out);
  - each emulation's exposure drugs (as for PS-Codes).
- **Difference from PS-Codes:** admissions on the *k*−1 day itself are included here, while PS-Codes uses admissions strictly before that day.
- **Encoding:** one forward pass per subject. Because the model is causal, the representation at the last token before each row's cutoff equals encoding that row's truncated timeline.
  - Checked on a sample (`--verify`): max |diff| 3×10⁻⁶ on synthetic data.
  - Subjects longer than 4,096 tokens are encoded per row.
- **Runtime:** CPU only. A pure-PyTorch stand-in for the two xformers parts femr uses (`scripts/bdc/xformers_shim`) gives masks identical to real xformers. Embeddings match real xformers in `tests/test_bdc_chs_clmbr.py`.
- **Code map:** `chs_clmbr_map.json` is SNOMED-derived. It is generated locally and uploaded to BDC by the user, never committed.

### B2. Richer CLMBR-T timeline (`--rich`, map v2; added 2026-10-19 after the first CLMBR-T result)

The first timeline had a median of 17 events per row. Two changes add no new kind of information; they only render the same routine-care history more like the EHR data CLMBR-T was trained on:

1. **Ongoing conditions repeated at every later clinic visit, as an EHR problem list is re-coded at each encounter.** These are the entry history, the adjudicated events, and hospital diagnoses in chronic ICD-9 categories (`chs_clmbr.CHRONIC`):
   - cardiometabolic, valve and cardiomyopathy, cerebrovascular and peripheral vascular;
   - COPD and asthma, chronic kidney disease;
   - dementia, Parkinson's disease, depression;
   - cancer and status V-codes (`V10`, `V45`, `V58`, …).
2. **Curated procedure map (map v2, `chs_clmbr_map.PROC`).** CLMBR-T knows only 196 ICD-9 procedure codes, and ICD-9 procedures have no OMOP "Maps to" into SNOMED. So 133 category rules send common inpatient procedures to the nearest in-vocabulary concept, for example:
   - PTCA and stents, cardiac catheterisation, coronary angiography, echocardiography;
   - pacemakers, dialysis, transfusion, ventilation, endoscopy;
   - imaging, joint replacement, cataract surgery, TURP.

   CABG has no procedure concept in the vocabulary and maps to "history of CABG". Codes already in the vocabulary are used as they are.

The output is a separate set (`--tag rich` → `chs_clmbr_rich*`, `--ehr clmbr_rich`), so the first CLMBR-T run is kept for comparison. The timeline report lists the most frequent categories that still do not map (counts ≥ 11).

## C. Pre-specified tests of added information (written 2026-10-19, before any of them was run)

**Context.** These tests were written after the first two CLMBR-T runs, in which CLMBR-T matched PS-Codes but did not exceed its single-draw permuted placebo. They are fixed here before any of them runs, and each is run once. All are exploratory and descriptive. The locked CHS endpoints are unchanged.

**Representations tested.** ECG (32 PCs), crude backbone, CLMBR-T, and CLMBR-T on the richer timeline (64 PCs each, within each emulation).

**Emulations.** The five analysed ones: E1, E2, E3, E5, E6.

### Test 1. Balance on top of PS-Codes

- **Arms:** `codes+ehr` (PS-Codes + representation) and `codes+permehr` (permuted placebo), added under `--ehr`.
- **Contrast:** relative reduction in mean held-out |SMD| versus PS-Codes alone.

### Test 2. Information without matching (`chs_ehr_tests.py info`)

- **Targets:** the 23 held-out items. Within each emulation, each item is predicted by ridge regression with 5-fold cross-validation grouped by person.
  - E5 and E6 are capped at 6,000 rows, a fixed random sample of people (seed 20261019), for run time.
- **Inputs, cumulative:**
  1. PS-Base;
  2. + the PS-Codes features;
  3. + one representation, or + ECG.
- **Quantity:** ΔR² = R²(PS-Codes + X) − R²(PS-Codes), per emulation × item cell.
- **Placebo:** the same with X permuted across rows, 10 draws.
- **Criterion (per representation):** "adds information beyond PS-Codes" if both hold:
  - (a) the mean ΔR² over all cells exceeds the 95th percentile of the placebo mean ΔR²;
  - (b) ΔR² exceeds that cell's placebo maximum in at least half of the cells.
- **Also reported:** the same increments on top of PS-Base only, for context.

### Test 3. Multi-draw placebo for balance (`chs_ehr_tests.py noise`)

- **Draws:** 50 permutations for each permuted arm:
  - ECG on PS-Base;
  - each EHR representation on PS-Base;
  - each EHR representation on PS-Codes.
- **Reported:**
  - the real pooled relative reduction;
  - the placebo median and its 2.5–97.5 percentile range;
  - the one-sided empirical P = (1 + #{placebo ≥ real}) / (N + 1);
  - per-emulation versions of the same.
- **Criterion:** a representation "improves balance beyond chance" if the real pooled reduction exceeds the placebo 95th percentile.

### Test 4. Extra rungs to match the YNHH ladder (`--ladder`)

- **PS-Demo:** age, sex, Black race, visit.
- **CVD10:** PS-Base plus five conditions, all known by visit *k*−1. Hospital codes are admissions before the *k*−1 day.

| Condition | Sources |
|---|---|
| CKD | hospital ICD-9 585, 586, 403, 404; codes only, never creatinine |
| COPD/asthma | baseline COPD, current asthma or emphysema diagnosed by a doctor; ICD-9 490–496 |
| PAD | Rose claudication at baseline; adjudicated incident claudication; ICD-9 440.2, 443.8, 443.9 |
| Stroke/TIA | prior stroke (as in PS-Base eligibility); prevalent or adjudicated TIA; ICD-9 430–438 |
| Valve disease | rheumatic or valve problems diagnosed by a doctor at baseline; ICD-9 394–397, 424 |

- **Arms:** each rung alone, + ECG and + permuted ECG.
- **Masking:** none, as for YNHH PS-Demo and CVD10.

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

CLMBR-T (after uploading `chs_clmbr_map.json` to `/sbgenomics/workspace/`):

```bash
python scripts/bdc/chs_clmbr.py timeline --map /sbgenomics/workspace/chs_clmbr_map.json
bash scripts/bdc/setup_clmbr_env.sh /sbgenomics/workspace/clmbr-env
env -u PYTHONPATH /sbgenomics/workspace/clmbr-env/bin/hf auth login   # or huggingface-cli login; the token stays on BDC
env -u PYTHONPATH /sbgenomics/workspace/clmbr-env/bin/python scripts/bdc/chs_clmbr.py download --model-root /sbgenomics/workspace/clmbr-t-base
env -u PYTHONPATH /sbgenomics/workspace/clmbr-env/bin/python scripts/bdc/chs_clmbr.py encode --model-root /sbgenomics/workspace/clmbr-t-base
python scripts/bdc/chs_emulate.py --protocol-locked --run ehr_clmbr --ehr clmbr
```

Richer timeline (map v2 uploaded as `/sbgenomics/workspace/chs_clmbr_map_v2.json`):

```bash
python scripts/bdc/chs_clmbr.py timeline --map /sbgenomics/workspace/chs_clmbr_map_v2.json --rich --tag rich
env -u PYTHONPATH /sbgenomics/workspace/clmbr-env/bin/python scripts/bdc/chs_clmbr.py encode --tag rich --model-root /sbgenomics/workspace/clmbr-t-base
python scripts/bdc/chs_emulate.py --protocol-locked --run ehr_clmbr_rich --ehr clmbr_rich
python scripts/bdc/chs_audit.py --run ehr_clmbr_rich --ehr clmbr_rich
```

The output goes to `chs_emulate/ehr_backbone/` (aggregates only). The `main_v2` run is not overwritten.

## Caveats

- **Post hoc:** this was added after the locked results were seen. It is descriptive and directional only.
- **Sparse input:** CHS has hospital codes but no outpatient codes. Many person-time rows have only medication flags, so the representation is much sparser than at Yale.
- **Not a pretrained model:** the crude backbone is fitted in-sample on CHS. It is a stand-in for an AI-EHR representation built from the same information, not a foundation model.
- **Out of distribution for CLMBR-T:** the timelines are short, coarse (annual visits, class-level drugs, pseudo-dates) and unlike Stanford EHR data. A weak CLMBR-T result here says more about the input than the model.
