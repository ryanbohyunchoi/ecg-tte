# CHS target-trial emulations (LATENT-RCT pipeline in the Cardiovascular Health Study)

**Status: DRAFT 2026-10-16.** The CHS feasibility counts are known; no ECG-adjusted estimate exists yet.
- The draft becomes LOCKED on user approval, before `chs_emulate.py` is run on real data.
- Changes after the lock are deviations, logged in `pipeline.md` §9.
- Sources: `docs/bdc/COHORT_FEASIBILITY_CHS_MESA.md` (variables) and `scripts/bdc/cohort_count.py` (counts).

## Common design (all emulations)

**Data:** CHS phenotype tables (phs000287 c1, dbGaP format) and ECG XML (phs003639 c1), linked through the Gen3 PFB tables (`participant_id`).

**Visits** are annual clinic years 2–11, each with a medication inventory (class flags).

**Time zero, treatment and baseline:**
- **Time zero:** visit *k*, the first visit at which the new drug class is recorded. The study day is `STDYTIME`, days since entry.
- **Treatment:** that drug class (arm A) vs the comparator class (arm B), or vs no use of the class.
- **Washout:** neither class at any earlier visit on record, with at least one earlier visit required.
- **Combination products** count toward every class they contain, so starting a product with both comparators excludes the person.
- **Baseline window:** the drug started somewhere between visits *k*−1 and *k*. So every covariate, held-out item and the ECG is taken from visit *k*−1 **or earlier**, using the latest non-missing value. Nothing from visit *k* is used.

**ECG:** the ECG XML from visit *k*−1, file label `VISIT(k−2)`. It is embedded with the paper's BCL encoder, 256-d → 32 PCs within each emulation.
- The files are 250 Hz and are upsampled to 500 Hz before baseline removal, as in the lab's upstream code.
- **Gate before use:** a sex and age linear probe. Sex AUC ≥ 0.80.

**PS-Base** (the PS-CVD5 analogue), all at visit *k*−1:
- age (`AGEY{k−1}`), sex (`GEND01`), Black race (`RACE01` = 2);
- hypertension (`BPHI`, or any antihypertensive at *k*−1);
- diabetes (`DIABADA` ∈ {3, 4}, or `INSULN06`/`OHGA06` at *k*−1);
- CAD (prevalent MI or angina at entry, or incident MI, angina, angioplasty or bypass before *k*−1);
- AF (`CARE_AFIB` prevalent, or incident before *k*−1);
- HF (`CHBLMOD` prevalent, or incident CHF before *k*−1);
- visit *k* (calendar proxy).

**PS-Clinical (richest):** PS-Base plus SBP and DBP, BMI, smoking, creatinine, LDL, HDL, glucose and albumin (latest at or before *k*−1), with median imputation plus missingness indicators. Echo is never a PS input.

**Arms** (estimator as in `pipeline.md` §4–5: L2 logistic, C = 1; 1:1 greedy caliper 0.2 SD on the logit; Cox with pair-clustered SE):
- crude;
- PS-Base, PS-Base + ECG, PS-Base + permuted ECG;
- PS-Clinical, PS-Clinical + ECG.

**Held-out panel** (latest value at or before *k*−1; balance is computed only where an item is observed in both arms):
- **Echo** (primary domain), from baseline `BASE2` (original cohort) or Year 7:
  - LV mass `NEWLVM43` / `MMLVMS43`;
  - LV function `LVEF43` / `LVFNCT43` (grade);
  - LA dimension `MMLAD43`;
  - septal and posterior wall thickness `MMVSTD43`, `MMLVWD43`;
  - E/A ratio `DPMEP43`/`DPMAP43` (the ratio cancels the unit change between visits).
- **Labs:**
  - creatinine `CRE44` (adjusted `CREADJ` where present);
  - LDL `LDLADJ`/`LDLUNADJ`, HDL `HDL44`, triglycerides `TRIG44`;
  - glucose `GLU44`, insulin `INS44`, albumin `ALB44`;
  - fibrinogen `FIB44`, CRP `CRPBLADJ`, cystatin C `CYSTATC` (Year 5).
- **Vitals and function:**
  - SBP/DBP (`AVZMSYS`/`AVZMDIA` in Years 2–3, `AVESYS`/`AVEDIA` in Years 4–11);
  - BMI, weight;
  - gait time `TIME27`, FEV1 `FEV118`;
  - ankle-arm index `AAI`.
- **Masking:** for PS-Clinical, its own inputs (BP, BMI, labs) are masked, and so is anything derived from them or with |ρ| ≥ 0.80. That is the paper's leakage rule.
- **Never held out:** ECG-derived items (`*42`, `*21`, `ECGLVH`, `LVM42`, `ECGAFIB`, `MAJABN`, `MINABN`).

**Outcomes:**
- **Event sources:** first events after time zero from `CHS_Event16` (all adjudicated events: `EVTYPE` 1 = MI, 3 = stroke, 4 = CHF; `TTOEVENT` in days from entry). Deaths and cause come from `EVENT_SUMMARY` (`TTODTH`, `CAUSE80`: 1 = atherosclerotic CHD, 2 = cerebrovascular, 3 = other atherosclerotic).
- **Censoring:** at death (for non-fatal outcomes), at the censor date (`EVENT_TIME_TO_CENSUS`), or at the trial horizon.
- **Exclusions:** people whose outcome event is unknowable after time zero (death before time zero) are excluded from that outcome.

**Metrics** (as in the paper):
- **Primary:** relative reduction in mean held-out |SMD| with the ECG. Analysed per emulation and pooled, with sign-flip tests over comparator clusters.
- **Secondary:**
  - % of held-out items with |SMD| < 0.1;
  - per-domain reductions (echo first);
  - |Δ log HR| vs the RCT, with the benchmark-permutation caveat (§7).
- **Comparator clusters:** thiazide-comparator emulations (1, 1b, 2, 4); 3; 5; 6.

## Emulations

Benchmarks were verified against the PubMed abstracts on 2026-10-16:
- ALLHAT (JAMA 2002, PMID 12479763): amlodipine and lisinopril vs chlorthalidone, plus the secondary HF and stroke results.
- PROSPER (Lancet 2002, PMID 12457784).
- ASPREE (NEJM 2018, PMID 30221597).
- STOP-2 (Lancet 1999, PMID 10577635): the abstract reports only conventional vs newer drugs pooled (CV mortality RR 0.99, 0.84–1.16). The ACE inhibitor vs CCB head-to-head figures are in the paper body and are **not yet verified**. Emulation 3 is therefore excluded from RCT-agreement metrics until they are checked; its balance results are unaffected.

| # | New users: A vs B | Eligibility (at *k*−1) | Primary outcome | Horizon | RCT benchmark (verify) |
|---|---|---|---|---|---|
| 1 | CCB vs thiazide | No prevalent HF (ALLHAT excluded symptomatic HF) | MI or fatal CHD | 60 mo | ALLHAT amlodipine vs chlorthalidone: RR 0.98 (0.90–1.07) ✓; HF 1.38 (1.25–1.52) ✓ |
| 1b | Dihydropyridine CCB (`AMLOD06`, `NIF*06`) vs thiazide | as 1 | as 1 | 60 mo | as 1 (sensitivity) |
| 2 | ACE inhibitor vs thiazide | as 1 | as 1 | 60 mo | ALLHAT lisinopril vs chlorthalidone: RR 0.99 (0.91–1.08) ✓; HF 1.19 (1.07–1.31) ✓; stroke 1.15 (1.02–1.30) ✓ |
| 3 | ACE inhibitor vs CCB | Age 70–84 | Cardiovascular death | 60 mo | STOP-2 ACEi vs CCB: head-to-head not in the abstract, to verify (pooled newer vs conventional: CV mortality 0.99 (0.84–1.16) ✓) |
| 4 | Thiazide vs beta-blocker | Age 65–74 | Stroke, MI or fatal CHD | 70 mo | MRC older adults: no head-to-head HR; balance only |
| 5 | Statin vs none (one sequential trial per visit) | Age 70–82; no prior statin | MI, stroke or fatal CHD | 39 mo | PROSPER: HR 0.85 (0.74–0.97) ✓ |
| 6 | Aspirin vs none (one sequential trial per visit) | Age ≥ 70; no prior MI, stroke, HF or AF | MI, stroke or HF | 56 mo | ASPREE CVD: HR 0.95 (0.83–1.08) ✓; major haemorrhage 1.38 (1.18–1.62) ✓ |

- **Secondary outcomes for every emulation:** each component, all-cause death, and HF.
- **Sequential trials (5 and 6):** at each visit *k*, initiators at *k* are compared with eligible non-users at *k*. Visit is included in the PS, and pairs are formed within the pooled set. A person may be a comparator at one visit and an initiator later; the SE is clustered on pairs, as in the paper.

## Feasibility (`cohort_count.py`, 2026-10-16; the smaller arm with an ECG at the prior visit)

| Emulation | Smaller arm with prior ECG |
|---|---|
| 1 | 427 |
| 1b | 365 |
| 2 | 483 |
| 3 | 539 |
| 4 | 365 |
| 5 | 559 initiators |
| 6 | 1,849 initiators |

All pass the paper's ≥ 350 rule before the eligibility restrictions above, which will reduce the counts. Emulations 3–6 must be re-checked after the age restrictions. Any that fall below 350 are reported as infeasible, not analysed.
