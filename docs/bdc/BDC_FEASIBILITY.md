# Figure 5 feasibility: hidden-confounder benchmark inside real RCTs (BioData Catalyst)

Written 2026-10-14. This pass used **public sources only**: the BDC Gen3 index and metadata services, the dbGaP FTP, BioLINCC study pages and data dictionaries, protocols, and papers. No controlled data was opened.
- Raw research notes are in the session scratchpad and are not committed.
- Each item is marked **[probe]** if it can only be confirmed by running `scripts/bdc/bdc_probe.py` inside BDC.

**Goal (user, 2026-10-13):** measure unmeasured-confounding bias inside randomized trials and test whether adding the ECG embedding to the PS removes it. This is for paper 1 (LATENT-RCT) and becomes **Figure 5**.

**Working mode:** the agent writes scripts here. The user pulls the repo inside a BDC Seven Bridges Data Studio, runs them, and relays the errors and aggregate outputs. Nothing controlled leaves BDC.

## 1. Bottom line

- **Feasible.** SPRINT, ACCORD (three randomized comparisons) and the WHI clinical trial (four comparisons) all have:
  - a raw 12-lead ECG taken **before randomization**;
  - baseline physiology measured on almost everyone;
  - centrally adjudicated outcomes;
  - published randomized HRs.
- **No precedent found.** Several searches found no published use of RCT rejection sampling on SPRINT, ACCORD or WHI. No AI-ECG analysis of these trials' raw waveforms was found either: the XML files were posted in 2025, and earlier ECG papers use reading-centre measures only.
- **Recommended design:** RCT rejection sampling (Keith et al., TMLR 2023). It is the real-data counterpart of the paper's plasmode simulation:
  - the outcomes, the treatment effect and the confounder distribution are all real;
  - only the treatment-assignment mechanism is altered.
- **Main practical work** (detail in §5):
  - import about 26k SPRINT/ACCORD baseline XML files plus the WHI visit-1 zips (about 1.6 GB);
  - link XML files to participants;
  - run the BCL encoder inside BDC.

## 2. Randomized comparisons with a pre-randomization ECG

| Comparison | N randomized (per arm) | Baseline ECG | Primary outcome: events, published HR | Other usable outcomes |
|---|---|---|---|---|
| **SPRINT** intensive vs standard SBP | 9,361 (4,678 / 4,683) | At the randomization visit. About 9,000 have one (estimated from file years; 12,092 files dated 2010–2013) **[probe]** | 264 vs 354; 0.73 (0.63–0.86) (final report, NEJM 2021) | All-cause death 0.75; primary or death 0.77; eGFR decline ≥30% (non-CKD) 3.67; serious AKI 1.69 |
| **ACCORD glycemia** intensive vs standard | 10,251 (5,128 / 5,123) | At the baseline (= randomization) visit. About 9,300–9,900 (13,640 files dated 2001–2005, mixed with 24/48-month ECGs) **[probe]** | 352 vs 371; 0.90 (0.78–1.04) | Death 1.22 (1.01–1.46); CV death 1.35; nonfatal MI 0.76 |
| **ACCORD BP** intensive vs standard | 4,733 (2,362 / 2,371) | same | 208 vs 237; 0.88 (0.73–1.06) | Stroke 0.59 (only 98 events) |
| **ACCORD lipid** fenofibrate vs placebo | 5,518 (2,765 / 2,753) | same | 291 vs 310; 0.92 (0.79–1.08) | HF 0.82; death 0.91 |
| **WHI E+P** vs placebo | 16,608 (8,506 / 8,102) | Screening ECG, median 32 days before randomization (range −313 to +5 days) | CHD 196 vs 159; 1.18 (Manson 2013) | Stroke 1.37; VTE about 1.9; fractures 0.76; global index 1.12 |
| **WHI E-alone** vs placebo | 10,739 (5,310 / 5,429) | same | CHD 204 vs 222; 0.94 | Stroke 1.35; fractures 0.72 |
| **WHI dietary modification** | 48,835 (19,541 / 29,294) | same | CHD 1,000 vs 1,549; 0.97 | Large null benchmark: stroke, breast cancer, death |
| **WHI calcium + vitamin D** | 36,282 (18,176 / 18,106) | Screening ECG about 1 year before this trial's randomization | MI/CHD death 499 vs 475; 1.04 | Null benchmark; hip fracture 0.88 |

Notes:
- WHI sizes are lower on dbGaP: phs000200 holds about 92% of each trial, e.g. E+P 7,879 / 7,503 and dietary modification 17,757 / 26,853. WHI ECG imaging covers 67,979 trial participants.
- WHI event counts were read from the Manson 2013 figure; recheck them before citing.
- **Event power (rough):** rejection sampling keeps about half the trial. SPRINT then gives about 200–400 primary events per draw, so SE(log HR) is about 0.10–0.15.
  - Bias is estimated across 200–500 draws, paired against the oracle within each draw, so a single draw does not need to be powered.
  - ACCORD BP and the rare WHI outcomes are the weakest. Use composites or death there.

## 3. Candidate hidden confounders (measured at baseline on almost everyone)

Selection on a confounder only works if (a) almost everyone has it measured, (b) it is prognostic for the outcome, and (c) it is plausibly visible on the ECG to some degree. Items marked **(+)** are positive controls (ECG-derived) and **(−)** are negative controls (expected to be invisible to the ECG).

| Trial | Physiology (main) | Other prognostic | Positive control (+) | Negative control (−) |
|---|---|---|---|---|
| SPRINT | eGFR, UACR, BMI, SBP. **NT-proBNP and hs-TnI** (Biomarkers ancillary study; coverage **[probe]**). NT-proBNP and BMI/eGFR link directly to the paper's plasmode confounders | Framingham 10-year risk, prior clinical CVD, smoking | Reading-centre ECG-LVH (Cornell, Sokolow-Lyon, Minnesota) | LDL cholesterol, education |
| ACCORD | HbA1c, diabetes duration, eGFR, UACR, BMI, SBP | Prior CVD, insulin use, smoking | Minnesota codes, Cornell voltage | LDL, education |
| WHI CT | BMI, waist, SBP/DBP (labs only in a 4–9% subsample, so not usable) | Medical history (diabetes, MI, HTN, AF), smoking, physical activity, prior hormone use | Reading-centre ECG (ecg_rel2: Minnesota, Novacode, LVH; about 57,500 screening ECGs) | Education, income |

- **What is missing:** none of these trials has LVEF or echo, so the paper's strongest ECG confounder (LVEF) cannot be tested here. SPRINT NT-proBNP is the closest stand-in.
- **The (+) and (−) controls frame the result.** The ECG should remove most of the bias from ECG-LVH and none from LDL. Any gain on eGFR or NT-proBNP falls between the two.

## 4. Proposed Figure 5 design (draft for decision)

Following Keith et al. 2023 (arXiv 2307.15176; code github.com/kakeith/rct_rejection_sampling). Avoid OSRCT (Gentzel 2021): it shifts P(C) unless P(T) = 0.5.

1. **Selection.**
   - For each comparison and hidden confounder C (standardised), set logit P\*(T=1|C) = α + β·z(C), with OR per SD of 2 and 3 (primary) and 5 (stress test).
   - Clip P\* to [0.05, 0.95] and calibrate α so that the mean P\* equals the randomized share.
   - Keep each participant with probability P\*(T=tᵢ|Cᵢ) / (P(T=tᵢ)·M). This preserves P(C) and the outcome model, so the C-adjusted effect equals the trial's effect.
   - Run **300 draws** per cell (fixed seeds), and report the Monte Carlo SE.
2. **Adjustment arms**, all with the paper's primary method (1:1 greedy NN on the PS logit, caliper 0.2 SD, L2 logistic C = 1, Cox with pair-clustered SE):
   - crude;
   - **PS-Base**: age, sex, race/ethnicity, plus whichever PS-CVD5 history items vary in that trial (prior CVD, AF; T2D does not vary within ACCORD, and HF does not vary within SPRINT);
   - PS-Base **+ ECG** (BCL 256-d → 32 PCs within the trial);
   - PS-Base + **permuted ECG** (placebo);
   - **PS-Rich (−C)**: all baseline covariates except C and anything derived from it. This is the PS-Clinical analogue, and it uses the paper's leakage rules: same quantity, derived, or |ρ| ≥ 0.80 with C. For example, eGFR removes creatinine and the CKD flag; BMI removes weight; HbA1c removes glucose;
   - PS-Rich (−C) + ECG;
   - **oracle**: PS-Base + C.
3. **Truth and metrics.**
   - **Primary metric: share of the confounding gap closed**, (log HR_crude-PS − log HR_arm) / (log HR_crude-PS − log HR_oracle). It is paired within each draw, so the trial's own sampling noise cancels. This is the same quantity as the paper's plasmode "bias removed relative to adjusting for the confounder itself".
   - **Balance:** post-match |SMD| of C and of the other held-out baseline measures. This repeats Figure 2's metric in an RCT where the truth is known.
   - **Fixed truth for absolute bias and coverage:** the full-trial Cox HR weighted by P\*(T=1|C). That is the randomized HR in the population the matching targets (ATT-like), and it avoids non-collapsibility drift. Also report the unweighted full-trial HR and a 5-year risk difference.
   - Also report coverage, RMSE, the % of treated participants matched, and events.
4. **Supplement.**
   - A confounding-vs-error plot (|crude − truth| vs |oracle − truth|).
   - Cross-validated R² of C from PS-Base, from the ECG, and from both, to show the ECG-predicts-C relation as in Figure 4A.
   - An instrument-only C, where adding the ECG should not hurt.
   - Two confounders: one ECG-visible and one ECG-invisible, as a bias-amplification check (Ding, VanderWeele and Robins 2017).
5. **Compute.** About 8 comparisons × about 6 C × 3 strengths × 300 draws × 7 arms ≈ 300k matched Cox fits on n ≈ 3–25k. That is CPU work, a few hours per trial in Data Studio. Embedding about 86k baseline ECGs is a short GPU job, and a CPU fallback is possible.
6. **Lock before results.** Given the post hoc disclosures in the main paper, freeze this design (trials, confounders, strengths, arms, metric) in `pipeline.md` §8 **before** any ECG-adjusted estimate is seen. Probe and linkage results may change *feasibility*, but they must not change the *design*.

## 5. Data on BDC and how to get it into Data Studio

| Study | Clinical project (Gen3) | ECG project | ECG files we need |
|---|---|---|---|
| SPRINT | `BL_SPRINT_GRU` (phs003483.c1): about 400 files, 2.4 GB; the BioLINCC SPRINT_2023a tree in SAS + CSV + xlsx codebooks, including the SPRINT-POP and Ancillary_Studies folders | `img_SPRINT_GRU` (phs003566.c1): 24,269 XML (about 198 KB each), all named `SPRINT_ECG_VISIT01_<year>0101_<serial>.xml` | Files dated 2010–2013 (manifest `m2_baseline_SPRINT.tsv`) |
| ACCORD | `BL_ACCORD_GRU` (phs003551.c1): about 370 files, 1.6 GB; BioLINCC 2017 package | `img_ACCORD_GRU` (phs003562.c1): 41,054 XML, all named VISIT01 | Files dated 2001–2005 |
| WHI | phs000200 (dbGaP `pht*.txt.gz` + XML dictionaries). WHI-BioLINCC phs004266 also exists (100% of participants, outcomes to 2018); is it in our approved request? | `img_WHI_HMB` (c1) / `img_WHI_HMB-NPU` (c2): 184k XML **and one zip per visit** | The `visit1.zip` of each consent group |

Each ECG project also ships three things:
- a data dictionary: `DD_*_Imaging*.xlsx/csv`. This is probably a per-file table that may carry subject IDs; the probe only summarises it;
- de-identification QC PDFs;
- Gen3 **PFB** avro files (harmonized and preharmonized), which should map each file to a subject. WHI also has `*_subject_ids.csv`.

The public index lists superseded releases alongside the current ones; `bdc_manifest.py` keeps only the latest.

**Linking (the main unknown) [probe]:**
- **File → participant:** through the PFB or the WHI subject-ID file. The file names carry a serial number, not a participant ID.
- **Participant → clinical record:** the imaging subject ID must match BioLINCC `MASKID` (SPRINT), the ACCORD key, or the dbGaP WHI ID. A dbGaP subject-mapping step may be needed.
- **Choosing the baseline ECG:**
  - SPRINT and ACCORD: the earliest file per participant within the enrolment years. Follow-up ECGs are at 2 years or later, so this is unambiguous.
  - WHI: VISIT01.

**Import routes:**
1. Gen3 Exploration → Files → filter the project → "Export to Seven Bridges" (Dynamic PFB Importer, April 2026). Use this for the clinical projects and the imaging documentation/PFB.
2. For the XML, Seven Bridges Files → "+ Add files" → GA4GH DRS → upload a manifest from `docs/bdc/manifests/`.
   - Bulk DRS import is throttled (about 500 files per 5 minutes on the sister platform CGC), so SPRINT + ACCORD baseline takes about 4–5 hours. WHI is two zip files.
   - The manifests give both a host-form and a compact-form DRS URI. Which one BDC accepts is untested.
3. **Project settings:** "Allow network access" must be on, or `git clone` and `pip install` fail.
4. **Data Studio paths:**
   - inputs are read-only at `/sbgenomics/project-files`;
   - code goes in `/sbgenomics/workspace`;
   - outputs go in `/sbgenomics/output-files`, which is copied to the project only when the analysis stops.
   - The only listed image is an old Python 3.7 one. The probe has no special requirements: it uses pandas + numpy, and fastavro for PFB.
5. **GPU:** g4dn, g5 and p3 instances are available. Running the encoder needs `pip install torch`.

**ECG encoder port (to build next):**
- The BCL encoder depends on lab code that is **not in this repo** (`bcl-smoke-runtime/upstream`, the `models_torch.CNN0SignalBackbone` backbone) plus the checkpoint `trained_12lead_30.pt` (24 MB).
- The plan has four steps:
  1. A standalone embedder: minimal model definition, the same preprocessing, and the ×1000 µV fix.
  2. A parity test here: identical embeddings to the existing Yale and MIMIC ones.
  3. A MUSE-XML → (5000, 12) mV converter. The 8 stored leads are I, II and V1–V6; III, aVR, aVL and aVF are derived.
  4. Uploading the checkpoint through the Seven Bridges uploader.

## 6. What only the probe can answer

1. The real table and column names, and coverage at baseline, for every candidate C. This includes whether SPRINT NT-proBNP and hs-TnI cover nearly everyone.
2. The file-to-participant key: PFB entities and fields, the content of the `DD_*` files, the WHI subject-ID file, and the ID formats.
3. The XML structure:
   - GE MUSE root;
   - Rhythm vs Median waveforms;
   - 8 vs 12 stored leads;
   - 500 Hz, 5,000 samples;
   - µV per bit;
   - acquisition device.
   - Also any oddities in the WHI and ACCORD XML.
4. The environment: Python and package versions, GPU, network access, disk.

## 7. Step 0 for the user (run order)

1. In the BDC Seven Bridges project, turn on **Allow network access** (Project settings).
2. Import into the project:
   - **(a) Clinical files:** with Gen3 export, or with the `m0_docs_<study>.tsv` DRS manifests (clinical + imaging documentation + PFB).
   - **(b) The probe sample:** `m1_probe_<study>.tsv`, 50 XML per study. For WHI, the sample is 50 baseline XML files rather than the 1.4 GB zip.
3. Start Data Studio (JupyterLab, CPU is enough), open a terminal, and run:
   ```bash
   cd /sbgenomics/workspace && git clone git@github.com:ryanbohyunchoi/ecg-tte.git && cd ecg-tte
   pip install --user fastavro openpyxl
   python scripts/bdc/bdc_probe.py
   ```
4. Review `/sbgenomics/output-files/bdc-tte/probe/probe.md`. It contains aggregates only and suppresses counts of 1–10. Then send back:
   - `probe.md` and `probe_columns.tsv`;
   - any traceback;
   - after a privacy look, the `docs_extract/` folder (data dictionaries and codebooks only).
5. If that works, import the `m2_baseline_<study>.tsv` manifests (about 26k XML plus 2 WHI zips) and rerun the probe with `--only files,xml`.

## 8. Decisions for the user

1. **Comparisons:** all eight, or a core set first? The recommended core is SPRINT, ACCORD glycemia, WHI E+P and WHI E-alone, with WHI dietary modification and calcium/vitamin D as large null benchmarks.
2. **Hidden confounders:** the list in §3, including the (+) and (−) controls.
3. **PS ladder in trials:** PS-Base / PS-Rich(−C) / oracle, as in §4.2.
4. **Encoder port:** permission to (a) copy the minimal BCL model code into this repo, and (b) upload the Yale-trained checkpoint to BDC. Check with the code owner and the PI, and against Yale policy on moving model weights.
5. **WHI accession:** whether WHI-BioLINCC phs004266 is in the approved request. Our data-access map lists only phs000200.
6. **Lock:** freeze §4 in `pipeline.md` before the ECG arms are run.

## 9. Not pursued now
- ACCORD within-trial **non-randomized** drug-class contrasts (TZD vs SU vs insulin, from yearly concomitant-medication flags). This is real confounding by indication, with the trial's arms as context. It is goal 2 or later.
- Cohort trial emulation in CHS, FHS and MESA (goal 2).

## Key sources
- Keith KA et al. RCT rejection sampling for causal estimation evaluation. TMLR 2023. https://arxiv.org/abs/2307.15176
- Gentzel AM, Pruthi P, Jensen D. ICML 2021. https://proceedings.mlr.press/v139/gentzel21a.html
- SPRINT: Wright, NEJM 2015 (PMC4689591); Lewis, NEJM 2021 (PMC9907774); BioLINCC https://biolincc.nhlbi.nih.gov/studies/sprint/
- ACCORD: BioLINCC https://biolincc.nhlbi.nih.gov/studies/accord/ ; data dictionary ACCORD_v2016a.pdf; BP PMC4123215; lipid PMC2879499; glycemia PMC4083508
- WHI: Manson, JAMA 2013 (PMC3963523); dbGaP phs000200 (FTP v12.p3), phs003824 (GapExchange)
- BDC: Dynamic PFB Importer https://sb-biodatacatalyst.readme.io/docs/dynamic-pfb-importer ; DRS import https://sb-biodatacatalyst.readme.io/docs/import-a-drs-file ; Data Studio files https://sb-biodatacatalyst.readme.io/docs/about-files-in-a-data-cruncher-analysis ; network access https://sb-biodatacatalyst.readme.io/docs/modify-project-settings#manage-network-access-control
- Gen3 index (public metadata): https://gen3.biodatacatalyst.nhlbi.nih.gov/index/index?acl=phs003566.c1

## 10. Results so far (aggregates from BDC runs, relayed by the user)

**2026-10-15: probe** (`scripts/bdc/bdc_probe.py`, SPRINT clinical CSVs + Gen3 PFB tables + all 24,269 ECG XML imported through Gen3 "Export to Seven Bridges"):
- **Import notes.**
  - Some exports partially fail with 90001 "Unauthorized" for random files. Re-exporting the same selection with Skip retries only the missing files.
  - The DRS URI form BDC uses is `drs://dg.4503:dg.4503/<uuid>`.
  - Data Studio has no SSH key, so clone the repo over HTTPS with a personal access token (or upload the two probe files).
- **ECG XML** (30 sampled):
  - GE MUSE `RestingECG` 8.0, MAC 1200;
  - Rhythm waveform with 8 stored leads (I, II, V1–V6) × 5,000 samples at 500 Hz, 4.88 µV/bit, MICROVOLTS; plus a Median beat (600 samples);
  - no decode errors and no flat leads;
  - III, aVR, aVL and aVF must be derived.
- **Linkage tables:**
  - `tsv/imaging_file.tsv` has 24,269 files → `subject`;
  - `tsv/subject.tsv` has 9,320 subjects; `submitter_id` = MASKID;
  - `ecg.csv` has 24,428 reading-centre ECGs with ECGDAYS.

**2026-10-15: cohort** (`scripts/bdc/sprint_cohort.py`, git ad3f99d):

| Check | Result |
|---|---|
| Randomized | 9,361 (4,678 intensive / 4,683 standard) |
| Gen3 subject → MASKID | `object.submitter_id`, exact for 9,320 / 9,320; all 24,269 files linked and present locally |
| File / reading-centre ECG counts equal | 8,976 participants (98 more files, 259 fewer files) |
| Year spacing consistent after alignment | 23,531 / 23,531 files |
| Baseline ECG XML assigned (ECGDAYS in [−90, 30]) | **8,815 (94.2%)**: 4,412 intensive / 4,403 standard; file years 2010–2013 |
| Randomized-arm balance | max \|SMD\| 0.05 over 50 covariates |
| Primary HR, SPRINT-POP (published 0.75, 0.64–0.89) | 243 vs 319 events; **0.755 (0.639–0.892)**; baseline-ECG subset 0.758 (0.637–0.901) |
| Death HR (published 0.73) | 155 vs 210; 0.735 (0.597–0.905); subset 0.730 |
| Primary, full adjudicated file (incl. post-intervention) | 315 vs 411; 0.757 (0.653–0.876) |

**Baseline coverage of the hidden-confounder candidates:**
- eGFR 99.6%;
- BMI 99.2%;
- UACR 95.2%;
- NT-proBNP 94.1% and hs-TnI 94.2% (randomization visit);
- LDL (Friedewald) 98.7%;
- reading-centre ECG measures at baseline 97.7%: LVH by Cornell, Cornell product, Minnesota and Sokolow-Lyon; QRS duration; AF/flutter.

**Not yet assigned:** 329 participants have a baseline reading-centre ECG but an unequal file count. A fallback rule, using the earliest file when its year precedes the next ECG, could recover some of them. This is not needed for feasibility.

**2026-10-15: ECG embedding** (`scripts/bdc/ecg_bcl.py embed`, git 8fd9713; slim checkpoint sha256 verified; CPU):
- **Embedded:** 8,815 / 8,815 baseline ECGs, 0 failures. Conversion took 4,105 s single-core (now parallel, a7fb8a7); embedding took 116 s.
- **Not degenerate:** mean pairwise cosine 0.148; norms 16.03–16.11.
- **5-fold linear probes:**
  - sex AUC 0.896;
  - age R² 0.311;
  - **log NT-proBNP R² 0.338**;
  - eGFR R² 0.055;
  - **Cornell voltage (positive control) R² 0.784**;
  - LDL (negative control) R² 0.035.
- **Comparison with the paper:** at Yale, the median ECG R² was 0.26 for LVEF, 0.20 for NT-proBNP and 0.04 for eGFR.
