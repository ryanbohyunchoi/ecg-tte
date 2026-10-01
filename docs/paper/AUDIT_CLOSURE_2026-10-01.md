# Audit closure: docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md vs paper.md (2026-10-01, final post-audit pass)

The status shown is after this pass, which builds on fix commits d0111c4 (audit fixes) and 8ad1314 (SENS_PRIMARY32 integration). "Before" is the status at the start of this pass.
- **FIXED:** the paper now matches the source.
- **PI:** an item the PI must decide or supply. It is marked "[PI: …]" in paper.md and listed at the top of the draft notes.

## A. Rows marked MISMATCH, UNSUPPORTED or NOT CHECKED (45)

| Row | Audit status | Before | After | What changed / where in paper.md |
|---|---|---|---|---|
| 2 | MISMATCH | PARTIAL | FIXED | eMethods 3 now explains the 4 trials built earlier but not among the 38. PARAGON-HF, DAPA-HF/EMPEROR-Reduced and PARTNER had fewer than 400 matched pairs with the clinical PS (the development data-sufficiency rule, PROTOCOL_V1 §4c). DIONYSOS's outcome (AF recurrence) could not be ascertained (af_candidates.md). |
| 14 | MISMATCH | FIXED | FIXED | F1 is listed in the Trial selection paragraph. |
| 16 | MISMATCH | PARTIAL | PI | eMethods 3 discloses the re-rater's exposure and LLM assistance. The wording is marked "[PI: confirm the wording of this disclosure]". |
| 19 | MISMATCH | FIXED | FIXED | Table 1 shows the four adjudicated tiers with points (3/12/17/6). |
| 20 | MISMATCH | FIXED | FIXED | Table 1 footnote: "made from design information and blind to emulation results". |
| 21 | MISMATCH | FIXED | FIXED | Table 1 footnote gives the four-tier definitions. |
| 23 | MISMATCH | FIXED | FIXED | Non-95% intervals, the PROTECT AF credible interval and the ROCKET-AF ITT estimate are footnoted. |
| 28 | MISMATCH | FIXED | FIXED | eMethods 1: echo values are masked before 2016-07-31. |
| 34 | MISMATCH | FIXED | FIXED | eMethods 4: noise placebo of 96 columns (real data) and 32 (simulation). |
| 39 | MISMATCH | FIXED | FIXED | "five cardiovascular and metabolic diagnoses". |
| 41 | MISMATCH | FIXED | FIXED | eMethods 5: the hdPS base is not limited to CV diagnoses. |
| 42 | MISMATCH | FIXED | FIXED | eMethods 5: prevalence ≥2%; laboratory tests enter as measured indicators only. |
| 49 | MISMATCH | FIXED | FIXED | eMethods 5: 90-day look-back (365 d for BMI and LVEF); latest value, set to missing if implausible. |
| 52 | MISMATCH | FIXED | FIXED | eMethods 5: matching order is by the smaller group's own membership probability. |
| 58 | MISMATCH | FIXED | FIXED | eMethods 6 discloses the prognostic score and the pool-B code summaries, and their overlap with the PS. |
| 61 | MISMATCH | FIXED | FIXED | Missingness indicators are stated for the expanded panel only. |
| 63 | MISMATCH | PARTIAL | FIXED | eMethods 6: "Expanded-panel results are reported for the demographic PS only". The P5/P2 exclusion bug therefore does not affect any reported number. |
| 64 | MISMATCH | FIXED | FIXED | 245–336 per trial; about 330 with the demographic PS. |
| 67 | MISMATCH | FIXED | FIXED | Ratio of across-trial means with 4,000 resamples (Statistical analysis, eMethods 6, CAPTIONS.md). |
| 76 | MISMATCH | FIXED | FIXED | LV systolic function 14.6% (−0.5 to 27.3), described as imprecise. |
| 80 | MISMATCH | FIXED | FIXED | hdPS 7.6% (1.9–12.8), with paired variable sets (SENS_PRIMARY32). |
| 84 | MISMATCH | FIXED | FIXED | All CIs are from fixed-seed resampling (SENS_PRIMARY32 ci.csv). Figure 2 reads that file. |
| 105 | MISMATCH | FIXED | FIXED | Post hoc orientation and ECG-only design are disclosed in the Simulation Methods and Results. |
| 106 | MISMATCH | FIXED | FIXED | eMethods 7 has a single orientation statement. |
| 110 | MISMATCH | PARTIAL | FIXED | Results now add, for the 29 trials, that the RCT-distance gain is absent (0.213 → 0.196; 14/29; P = .24) and that the SE rises ×1.37 (SENS_OUTPATIENT.md). The 23 primary-set values are kept. |
| 112 | MISMATCH | FIXED | FIXED | eMethods 9: the outpatient analysis refits and rematches. |
| 118 | MISMATCH | FIXED | FIXED | "without substitution"; earlier estimates for 5 of the 7 trials are disclosed. |
| R1 | MISMATCH | FIXED | FIXED | References are in first-citation order (1–19), rechecked after this pass. |
| R3 | MISMATCH | FIXED | FIXED | Ref 10 and 13 pages are complete. |
| 6 | UNSUPPORTED | FIXED | FIXED | Candidate sourcing now includes investigator review. |
| 11 | UNSUPPORTED | FIXED | FIXED | 15-trial prespecified results are given in Results and eTable 10. |
| 54 | UNSUPPORTED | FIXED | FIXED | Sensitivity analyses were rerun in the 32/38 trials (SENS_PRIMARY32); Results and eTable 6. |
| 56 | UNSUPPORTED | FIXED | FIXED | The 58-panel timing is disclosed (Covariate balance). |
| 68 | UNSUPPORTED | FIXED | FIXED | The treatment-classifier AUC sentence is removed. |
| 96 | UNSUPPORTED | FIXED | FIXED | Comparator-cluster, leave-one-out and FDR results come from SENS_PRIMARY32. Split halves are removed per the PI. |
| 97 | UNSUPPORTED | FIXED | FIXED | Replaced by "recomputed … in an internal consistency audit". |
| 108 | UNSUPPORTED | FIXED | FIXED | Design-step result is in eMethods 8 (supplement only). |
| 109 | UNSUPPORTED | FIXED | FIXED | Enrichment dropped per PI decision. |
| S2 | UNSUPPORTED | FIXED | FIXED | statsmodels removed. |
| R2 | UNSUPPORTED | PARTIAL | FIXED / PI | Heyard (18) verified via Crossref, tag removed; Morris (19) numbered. The 12 expanded-panel sources (incl. Sentinel, OHDSI) are referred to eTable 2; whether to add them to the reference list is a PI item. |
| X3 | UNSUPPORTED | FIXED | FIXED | Echo-subset Results sentence plus eMethods 12. |
| 24 | NOT CHECKED | PARTIAL | FIXED | Table 1 footnote names the omitted outcome components: LODESTAR and PROVE IT (revascularization), AMPLIFY (VTE death), FRAIL-AF (CRNM bleeding), CABANA (disabling stroke). |
| 32 | NOT CHECKED | NOT FIXED | PARTIAL / PI | eMethods 4 now gives the architecture (convolutional encoder plus lead–time transformer; µV input) and the held-out probe performance (ECG_MODEL.md). Training data details are marked [PI: …]. |
| 115 | NOT CHECKED | FIXED | FIXED | CLMBR-T results in Results (italic) and eTable 12. |
| R5 | NOT CHECKED | NOT FIXED | FIXED | Ref 9 full author list, issue and DOI verified via Crossref. |

**Counts** (45 rows):
- **Before this pass:** 37 FIXED, 6 PARTIAL (2, 16, 24, 63, 110, R2), 2 NOT FIXED (32, R5).
- **After this pass:** 43 FIXED. Rows 16 and 32 remain partly open as PI items, R2 has a residual PI item, and there is nothing else outstanding.

## B. Rows marked CONFIRMED that carried a recommended fix

| Row | Fix | Status |
|---|---|---|
| 1 | State the counting rule | FIXED. eMethods 3: design variants counted once; grouped screening entries counted separately. |
| 5 | ACS/MI naming | FIXED ("acute coronary syndromes or myocardial infarction"). |
| 8, 10 | Near-duplicate rule; count-only screen before registration | FIXED (eMethods 3). |
| 15, 17 | Heyard numbered; 82% (81.6%) | FIXED |
| 29 | "First recorded encounter ≥365 d" | FIXED (eMethods 2) |
| 35 | CLMBR-T input window | FIXED (eMethods 4) |
| 47 | STEMI/PCI window includes the index day | FIXED (eMethods 5) |
| 53 | Caliper SD definition | FIXED (eMethods 5) |
| 55 | Prespecified endpoint only for the confirmation trials | FIXED. Statistical analysis: "the primary balance measure prespecified for the confirmation analyses". |
| 82 | Expanded-panel CI 13.2 | FIXED. Caption and text agree at 6.3–13.2. |
| 93 | P = .009 attribution | FIXED |
| 103, 104 | Partial R² and 38-trial median; 14.2% design label | FIXED |
| 113 | Truncation, landmark deviation; primary-set values | FIXED. The Results now report the switch-only, per-protocol (365 d), landmark and run-in estimands for the primary set. |
| 114 | AF confirmation failed | FIXED |
| 116, 117 | Clinical-lite; "decreased" limited to mean \|Δ\|; pair range for the demographic PS | FIXED |
| R4 | Drop [verify] on 15–17 | FIXED. The 38 trial publications remain uncited (PI item). |
| S3 | CLMBR-T PC environment | FIXED. eMethods 10: PCs computed in the core analysis environment (v13_common). |
| X1 | No genetics content | CONFIRMED (re-grep: none; UK Biobank, enrichment and split halves also absent). |
| X2 | Display-item limit | Not applicable; the journal is to be decided. |

## C. Other changes in this pass
- **Journal-neutral.** The paper no longer targets a specific journal: JAMA limits, subtitle and abstract headings were removed. Key Points are optional, and the abstract is structured as Background, Methods, Results and Conclusions.
- **Detail restored:** the feasibility thresholds and near-duplicate rule are back in the main-text Trial selection paragraph, and the cohort sizes are filled.
  - 212,496 patients with an ECG across the 32 cohorts (median 4,729 per trial).
  - 88,460 retained in 44,230 matched pairs (median 981 pairs; 314–4,100).
- **Supplement numbering:**
  - eTables are renumbered in order of first citation, and a list of the 12 eTables was added to Tables and Figures.
  - eFigures 5 and 8 are swapped. The files, scripts/v20/make_paper_figures.py and CAPTIONS.md were renamed to match. The figures were rebuilt; the PNGs are unchanged.
- **Unchanged:** the P-value style was already uniform ("P = .008"; q values as "q = .007"), and references stay as superscript numbers.
