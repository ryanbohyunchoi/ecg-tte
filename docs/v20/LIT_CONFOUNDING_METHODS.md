# Methods for measuring, detecting, bounding and adjusting for unmeasured confounding, and for evaluating a high-dimensional proxy: a landscape for the AI-ECG target trial emulation paper

Compiled 2026-09-30 for the v20 cycle. This is a literature review only. No patient data and no `/mnt/raid0` files were accessed.

**How citations were checked.** Every numbered reference was checked against at least one primary index in this session:
- PubMed E-utilities (PMID, title, journal, abstract where needed);
- Crossref (DOI, authors, volume, pages);
- DataCite/arXiv for arXiv identifiers;
- publisher or proceedings pages (proceedings.neurips.cc, proceedings.mlr.press, jmlr.org) for conference papers.

Items that could not be fully checked are tagged **[unverified]** or **[partially verified]**, with the reason (Section 6). Claims about what a paper found come from its abstract or from our earlier verified notes in `docs/LITERATURE_RCT_DUPLICATE_LANDSCAPE.md`. That file covers RCT-DUPLICATE, hdPS and benchmarking in depth; this document does not repeat it and focuses on confounding methods.

---

## 1. Executive summary

- **Where the paper stands.** Three lines of evidence already support the claim that "the ECG is a partial proxy for unmeasured physiology":
  - better balance on held-out physiology and coded characteristics, against a permuted-ECG placebo;
  - agreement with RCTs across 38 emulations;
  - a plasmode simulation in which the ECG removes about 14% of the bias from a hidden confounder, roughly 100 × R²(confounder ~ ECG).

  That size of effect is what measurement-error theory predicts for an imperfect proxy [1–3]. It also mirrors German et al.'s polygenic-score trial emulations [4]: polygenic-score imbalance tracked design quality, but polygenic scores alone could not fully adjust for unmeasured confounding.
- **What reviewers are likely to ask.**
  - How big is the residual confounding in the real data, not just in simulation?
  - Would the conclusions survive plausible unmeasured confounding?
  - Is the ECG mostly predicting treatment rather than outcome? If so it could act like an instrument and amplify bias [5,6].
  - With only 38 RCT pairs, design mismatch dominates RCT–RWE disagreement [7,8]. What evidence has more power?
- **Five highest-value additions** (Section 4 sketches each):
  1. **Negative control outcomes (NCOs) with empirical calibration**, compared across the PS ladder with and without the ECG [9–12]. This gives hundreds of estimates whose true value is known (null). It is the OHDSI/LEGEND standard, including in Khera-lab JACC work [13–15].
  2. **Real-data bias removal in the echo validation subset.** Within echo patients, compare the ECG-augmented PS with a PS that includes the actual echo/NT-proBNP physiology. Then use propensity score calibration or two-stage calibration to carry this to the full cohort [2,16–19]. This is the real-data counterpart of the plasmode "fraction of bias removed".
  3. **Benchmarked omitted-variable-bias sensitivity analysis.** Use Cinelli–Hazlett robustness values and contour plots, with the machine-learning (ML) generalisation, Austen plots and E-values [20–23]. The held-out LVEF, NT-proBNP, eGFR and BMI serve as benchmarks: "residual confounding would need to be k × as strong as LVEF".
  4. **Prognostic-score balance plus overlap and bias-amplification diagnostics.** Collapse the 58 held-out physiology SMDs into one outcome-weighted balance metric [24–26]. Report the C-statistic, preference-score equipoise and the ECG–outcome association, to rule out Z-bias [27–30].
  5. **Proximal causal inference with ECG-derived proxies**, as an exploratory extension. Use two ECG instances as treatment- and outcome-inducing proxies [31–35]. Validate it where the truth is known: in the plasmode, and against measured LVEF in the echo subset.
- **Worth doing if cheap, lower priority:**
  - multivariate balance tests (energy distance, MMD, classifier two-sample) [36–38];
  - E-values with a meta-analytic E-value across trials [39];
  - Rosenbaum Γ for the matched pairs [40];
  - a specification curve over the PS ladder [41];
  - falsification and healthy-adherer endpoints [42–44];
  - a TARGET-compliant reporting checklist [45].
- **Low feasibility or not recommended here:**
  - physician-preference instrumental variables (IVs): one health system gives weak instruments with doubtful exclusion [46,47];
  - Mendelian randomization (MR): no genotypes; cite published drug-target MR as triangulation only [48,49];
  - combining observational data with RCT individual participant data: we have none [50,51];
  - the "deconfounder" family [52,53].
- **Framing lessons from recent high-impact papers:**
  - Fan et al. (*Nat Commun* 2026) found that PSM, IPTW, TMLE and a Transformer all recovered truth in semi-synthetic data but failed against RCT benchmarks [54]. Plasmode success is therefore necessary but not sufficient, which justifies adding NCOs and the echo-subset analysis.
  - Wyss et al. describe a "modest benefit" from ultra-high-dimensional NLP proxies [55]. Zeng et al. show text-mined confounders shifting HRs toward RCTs [56]. These are the closest precedents for how to word a modest gain.

---

## 2. How the current analyses map onto established methods

| Our analysis | Established method it instantiates | Anchor references | Gap a reviewer may point to |
|---|---|---|---|
| Balance on 58 held-out physiology variables plus ~330 literature covariates after 1:1 PS matching | Balance on characteristics observed only in a richer source, not used in the PS (the claims-vs-EHR design) | [57–59] | Univariate SMDs are not weighted by prognostic importance and are not translated into bias |
| Permuted-ECG placebo | Placebo/negative-control *covariate*. It tests whether gains come from added dimensionality alone | [9,60] | Tests only "structure vs noise", not validity; a supervised placebo would be stronger (e.g., an ECG from a different patient matched on age/sex) |
| RCT-DUPLICATE agreement metrics and benchmark shuffle | External benchmarking of emulations | [7,8,58,61,62] | Low power; confounding mixed with design and estimand mismatch |
| Plasmode with hidden LVEF, NT-proBNP, BMI or eGFR | Plasmode simulation; partial adjustment by an imperfect proxy | [1,63,64] | Truth is known only in simulation, and real-data failure is possible [54] |
| Bias removed ≈ 100 × R² | Regression-calibration and measurement-error logic (see note); German et al. is the PGS analogue | [2–4] | A real-data analogue is needed (Top-5 #2) |
| PS ladder (demographic → sparse → hdPS → clinical → CLMBR-T) | Data-adaptive vs investigator-specified adjustment benchmarked against RCTs | [65–67] | Outcome-adaptive and DML variants are missing |

*Note on the R² relation.* This is our derivation, not a cited result. Take a linear model in which U confounds A and Y, and W is a proxy with U = λW + ν given X. Adjusting for W leaves a fraction of the bias of about Var(ν)/Var(U) = 1 − R²(U~W|X). The approximation holds when U explains a small share of the variance of A. The fraction of bias *removed* is then ≈ R². This is the logic behind propensity score calibration [2] and the partial-adjustment results for mismeasured confounders [1]. Our ≈100 × R² finding is therefore the theoretically expected size, and the paper can say so.

---

## 3. Candidate analyses, ranked by value for the paper

Feasibility is rated against what we have: OMOP EHR, echo reports, raw ECGs, state death records, 38 matched cohorts, an echo subset, and an existing plasmode harness. Effort is approximate analyst time once the cohorts are cached.

| # | Method | Question it answers | Key references | Data it needs | Feasibility (reason) | Expected effort | How it would appear in a JAMA Cardiology paper |
|---|---|---|---|---|---|---|---|
| 1 | **NCO panel + empirical calibration** across the PS ladder ± ECG, with synthetic positive controls | Does adding the ECG shrink residual systematic error in real data, where the truth (HR = 1) is known? | Methods [9–12,60,64,68,69]; applied [13,14,44,70–72]; FM-embedding precedent [73] | OMOP condition and procedure occurrence in the existing matched cohorts; a prespecified NCO list; EmpiricalCalibration (HADES) | **High.** OMOP-native, the cohorts exist, and the tooling is standard. Per-NCO events are few in one system, so pool across trials | 1–2 weeks, including clinician review of the NCO list | **Main figure:** empirical-null plots by PS spec. **Main table:** EASE, mean bias, CI coverage. eFigure of calibrated HRs vs RCT |
| 2 | **Echo validation-subset analysis**: real-data fraction of bias removed; propensity score calibration (PSC); two-stage calibration; multiple imputation (MI) with the ECG as auxiliary | How much of the confounding by measured cardiac physiology does the ECG remove in real data? Does it match the plasmode? | [2,16–19,74,75]; theory [1] | Echo/NT-proBNP subset within each trial cohort; existing PS specs | **High–medium.** Data exist. The echo subset is selected by indication (weight for it), and the surrogacy assumption must be tested [16] | 1–2 weeks | **Main table or figure:** real-data vs plasmode fraction of bias removed, by confounder, next to R² |
| 3 | **Benchmarked OVB sensitivity**: robustness values, contour plots, DML-OVB bounds, Austen plots | How strong must residual confounding be, relative to LVEF or NT-proBNP, to change conclusions? Does the ECG raise robustness? | [20–22,76,77]; Cox/survival [78–80] | Matched cohorts; a fixed-horizon risk outcome (or Cox approximations); held-out physiology as benchmarks | **High.** sensemakr and DoubleML are off the shelf. Time-to-event needs a fixed-horizon or approximate formulation | 1 week | eFigure: contour for an exemplar trial. eTable: robustness values (RV) for all 38. One Results sentence |
| 4 | **Prognostic-score balance** (outcome-weighted held-out balance), plus prognostic or joint PS–prognostic matching as an alternative use of the ECG | Is the balance gain concentrated on outcome-relevant physiology? | [24–26,81–84] | A prognostic model fit out of sample (pilot split or comparator arm); held-out physiology | **High.** Only needs sample splitting | 3–5 days | Panel in the balance figure: prognostic-score SMD by spec across 38 trials |
| 5 | **Overlap, equipoise and bias-amplification (Z-bias) diagnostics** for the ECG block | Does the ECG mainly predict treatment (instrument-like), harming overlap or amplifying bias? | [5,6,27–30,85–87] | PS models, matched n, and ECG–outcome association conditional on A and X | **High** | 2–3 days | eTable: C-statistic, % in equipoise, matched fraction, ECG–outcome LRT. One Methods/Results sentence |
| 6 | **Proximal causal inference** with ECG-derived treatment- and outcome-inducing proxies (two ECG instances) | Can the ECG *identify* the effect despite U, rather than only partially adjust for it? | [31–34,88–91]; embeddings/text as proxies [35,92]; ML [93,94]; proxy search [95] | Patients with ≥2 pre-baseline ECGs; an ECG→phenotype predictor trained outside the cohorts; the plasmode and echo subset for validation | **Medium.** Proxy assumptions are strong. Survival methods exist only for additive hazards (pci2s). Requiring two ECGs changes the population | 2–3 weeks | eFigure: bias removed in the plasmode, PS+ECG vs proximal. Discussion paragraph. Labelled exploratory |
| 7 | **E-values and quantitative bias analysis (QBA)**, including a meta-analytic E-value across the 38 emulations and Bross-type translation of residual echo SMDs into HR bias | How robust is each HR? What bias does the residual echo imbalance imply? | [23,39,96–102]; critiques [103,104]; cardiology [105] | Final HRs and CIs; residual SMDs; literature or echo-subset confounder–outcome associations | **High.** Summary statistics only | 2–3 days | E-value column in the results eTable; QBA eTable; Discussion sentence |
| 8 | **Multivariate/distributional balance**: energy distance, MMD permutation test, classifier two-sample test (post-matching C-statistic) on held-out physiology and on the embedding | Is the joint distribution of physiology balanced, beyond marginal SMDs? Does this sharpen the placebo test? | [36–38,106–110] | Matched cohorts (already cached) | **High** | 2–3 days | eFigure: energy distance relative to demographic PS, with permutation null |
| 9 | **Interpretable ECG-derived phenotypes** (AI-ECG LVSD probability, ECG-age, predicted NT-proBNP) instead of, or besides, the 32 PCs | Which physiology does the ECG carry into the PS? Can a clinician-legible covariate reproduce the gain? | [111–119]; AI echo (Stanford) [120,121] | ECG waveforms or images; CarDS-lab or public AI-ECG models | **High.** The models exist in-lab. Check for training-data overlap | 1 week | eTable: PS with AI-ECG scalars vs PCs; Discussion on clinical interpretability |
| 10 | **Falsification endpoints and healthy-adherer diagnostics** (accidents, screening, vaccination, cancer), especially for per-protocol/adherence estimands | Is there residual healthy-user or healthy-adherer bias, and does the ECG change it? | [42–44,122–126] | OMOP procedures and immunizations (partial capture), adherence definitions | **High–medium.** Out-of-system vaccination is under-captured | 3–5 days (overlaps #1) | eFigure forest plot by spec, combined with #1 |
| 11 | **DML/TMLE with the full embedding**; supervised ("causally sufficient") reduction; outcome-adaptive selection of ECG features | Are the 32 unsupervised PCs discarding confounding signal? Does the ECG survive outcome-aware selection? | [66,127–137]; applied cardiometabolic TMLE [138] | Full embedding vectors; compute; fixed-horizon outcomes | **Medium–high.** Survival TMLE is heavier; fixed-horizon risk is simpler | 1–2 weeks | Sensitivity eTable; one Discussion sentence |
| 12 | **Heyard-style meta-regression, ratio of ratios, BenchExCal-style calibration** of RCT agreement by PS spec | Does the ECG reduce between-pair heterogeneity once design differences are modelled? | [7,8,58,61,62,66,139,140] | The 38 RCT–RWE pairs and a closeness rubric | **High.** Summary level | 3–5 days | Main agreement figure (already planned); eTable |
| 13 | **NCO-based bias *correction***: control-outcome calibration (COCA), NC-calibrated difference-in-differences (DiD) | Can NCOs estimate and remove bias, not only detect it? | [141–145] | Same as #1, plus a pre-period for DiD | **Medium.** Needs NCOs that share U with the outcome | 1 week after #1 | eTable sensitivity |
| 14 | **Rosenbaum sensitivity (Γ)** for matched pairs; marginal sensitivity model for weighting | How much hidden bias in treatment odds would overturn each finding? Does the ECG change Γ? | [40,146–153] | Matched pairs and a binary or fixed-horizon outcome | **High–medium.** Censoring complicates it; use a fixed horizon | 2–3 days | eTable column (Γ at α = 0.05) |
| 15 | **Specification curve / multiverse** over PS spec × caliper × look-back × estimand | Is the ECG effect robust to analyst choices? | [41,154] | Existing pipeline outputs | **High** | 3–5 days (compute) | eFigure (specification curve) |
| 16 | **TARGET reporting and external-validation framing** (closeness rubric; same-population comparisons) | Is the emulation transparent and comparable to RCT-DUPLICATE? | [45,61,155–160] | Protocol documents | **High** | 2 days | Supplement checklist; Methods citation |
| 17 | **Physician- or facility-preference IV**, using ECG/echo balance across IV levels as the validity diagnostic | Does an IV analysis agree with PS±ECG? Is the IV independent of the physiology the ECG captures? | [46,47,161–167]; applied cardiology [168] | OMOP provider_id/care_site, prescriber history | **Low–medium.** One health system; weak instruments across 38 small cohorts; exclusion doubtful; LATE ≠ ATE | 2 weeks | At most an eTable. The IV-balance-by-ECG diagnostic is the novel part |
| 18 | **Representativeness/transportability diagnostics** (phenotypic distance of emulated cohorts from trial populations) | Is RCT disagreement due to effect modification rather than confounding? | [51,169–171] | Published trial baseline tables | **Medium.** Summary-level only | 1 week | eFigure; Discussion |
| 19 | **Combining RCT and observational data / experimental grounding** | Can RCTs estimate a bias function for the observational estimator? | [50,51] | RCT individual participant data (not available) | **Low** | — | Discussion only |
| 20 | **MR / genetic triangulation** | Is the confounding physiology causal for outcomes? Do independent designs agree? | [4,48,49,172–176] | Genotypes (not available); published MR estimates | **Low.** No genotypes; cite published MR only | 1–2 days (literature) | Discussion sentence and triangulation eTable |
| 21 | **Deconfounder / multiple-causes latent-factor methods** | Can a factor model over many treatments recover U? | [52,53] | Many simultaneous treatments | **Not recommended.** Identification is contested and the setting doesn't fit | — | Not included |

Other ML-causal and Nature-portfolio work worth citing in the Introduction or Discussion:
- representation-learning theory [133,177];
- text-as-confounder work [131,178–180];
- imaging causality [181];
- causal-ML reviews [182,183];
- deep-learning trial emulation in EHRs [184,185];
- EHR foundation-model caveats [186];
- an NCO-based long-COVID cardiovascular analysis [187].

---

## 4. Top-5 recommended additions: analysis sketches

### 4.1 Negative control outcomes with empirical calibration across the PS ladder

**Rationale.**
- Our RCT benchmark has 38 pairs, and much of the disagreement is design mismatch [7].
- NCOs give many estimates with known truth in the same cohorts [9].
- OHDSI made them a standard diagnostic [10–12]. It is used in cardiology by LEGEND-HTN (*Lancet*) and LEGEND-T2DM (*JACC*) [13–15], and to compare PS methods [64].
- A 2026 claims foundation-model preprint reported a 72% average reduction in systematic bias in a trial emulation [73]. It is the closest precedent for "embedding in PS".

**Inputs.**
- The 38 matched cohorts under each PS spec: demographic, sparse, hdPS, clinical, CLMBR-T, each ± ECG, plus the permuted-ECG placebo.
- A **prespecified** list of 40–60 NCOs. Candidates come from the OHDSI approach (no label, literature or knowledge-base association with any study drug [68]), then clinician review, frozen before any estimates are seen [60].
- Two NCO strata:
  - (a) generic NCOs (e.g., ingrown nail, cataract, allergic rhinitis);
  - (b) **physiology-sensitive NCOs**, whose risk plausibly depends on the same unmeasured cardiac or frailty state but not on the drugs (e.g., non-cardiac hospitalisation for pneumonia, pressure ulcer, hip fracture where the drugs have no known effect). These must be vetted class by class. Sloot et al. found cancer, fracture, pressure ulcer and influenza vaccination NCOs revealing confounding in a PCSK9 emulation [44].
- Synthetic positive controls injected at HR 1.5, 2 and 4 [11].

**Estimand and analysis.**
- Same design, estimand and model as the primary analysis for each NCO.
- Per spec: fit the empirical null N(μ, σ²) of log HRs. Report EASE [12], 95% CI coverage for NCOs, and the share with p < .05.
- Primary contrast: ΔEASE (spec+ECG − spec), with bootstrap or hierarchical-model CIs pooled across trials. Test within the physiology-sensitive stratum separately.
- Secondary: calibrate each trial's primary HR [11]. Re-compute the RCT-DUPLICATE agreement metrics on calibrated estimates to see whether calibration improves agreement, and whether it does so more for ECG specs.

**Output.**
- Main figure: one panel per spec, NCO log HR vs SE with the fitted null. Headline numbers: EASE and coverage.
- Main table (or eTable): μ, σ, EASE and coverage by spec, overall and by NCO stratum.
- eFigure: calibrated vs uncalibrated HRs against RCT HRs.

**Caveats.**
- NCOs detect only confounding they share with the outcome. Generic NCOs may be insensitive to cardiac physiology, so stratum (b) is essential.
- Calibration assumes the NCO bias is exchangeable with the outcome bias. It works best when bias comes from unmeasured confounding [69].
- Low event counts in one system call for pooling across trials or hierarchical shrinkage.
- Mis-specified NCOs (true drug effects) inflate σ. Report a sensitivity analysis that drops NCOs flagged by the knowledge base.
- Pre-register the NCO list in the protocol amendment.

### 4.2 Real-data bias removal in the echo validation subset (PSC / two-stage calibration / MI)

**Rationale.**
- The plasmode shows ECG ≈ R² bias removal *when we control the truth*. Fan et al. warn that simulation success can coexist with real-data failure [54].
- The echo/NT-proBNP subset is a natural *internal validation sample* in which the "unmeasured" confounders are measured. That is exactly the setting for PSC [2,74] and its successors [17,18].
- In the original PSC application, PSC moved an implausible NSAID–mortality RR of 0.80 to 1.06 [2].

**Inputs.**
- In each trial cohort, patients with a baseline echo (and NT-proBNP where available) inside the baseline window.
- PS specs S (demographic, sparse, hdPS, CLMBR-T).
- Physiology set P: LVEF, NT-proBNP, BMI and eGFR individually, plus the full 58-variable panel.

**Estimands and analysis.**
- (a) **Within-subset bias-removal fraction.**
  - Fit HRs under S, S+ECG and S+P, where S+P is the "gold standard" G for the physiology confounding.
  - F = (log HR_S − log HR_{S+ECG}) / (log HR_S − log HR_G).
  - Pool across trials with a random-effects ratio estimator (or report the numerator and denominator on the log-HR difference scale when denominators are near 0).
  - Weight by the inverse probability of having an echo, to reduce selection into the subset.
- (b) **PSC to the full cohort.**
  - Regress the gold-standard PS (S+P) on the error-prone PS (S or S+ECG) in the subset, then apply the calibrated PS in the full cohort [2].
  - Test surrogacy, i.e., whether the error-prone PS carries no outcome information beyond the gold-standard PS, following [16]. If surrogacy fails, use two-stage calibration [17] or Bayesian external-validation adjustment [18].
- (c) **ECG as imputation model, not PS covariate.** Multiply impute P in non-echo patients with the ECG embedding as an auxiliary predictor, then include imputed P in the PS [19]. Compare with S+ECG. This tests whether the ECG works better as a *measurement* of physiology than as a raw PS input.

**Output.**
- Main table or figure: F by confounder (LVEF, NT-proBNP, BMI, eGFR, full panel), real-data vs plasmode, next to R²(P ~ ECG | S). If the points lie near the identity line, that is the paper's strongest mechanistic result.
- eTable: PSC-corrected full-cohort HRs by trial, with RCT HRs.

**Caveats.**
- The echo subset is selected by indication. Transporting F to the full cohort assumes the proxy–confounder relation is stable.
- G adjusts only for P, not for all U.
- F is unstable when HR_S ≈ HR_G.
- PSC needs surrogacy, which fails often in practice [16].
- MI assumes missing at random given the ECG and covariates.
- Keep the echo variables out of every PS used for the primary held-out-balance analysis, so it is not contaminated.

### 4.3 Benchmarked omitted-variable-bias (OVB) sensitivity analysis with held-out physiology as benchmarks

**Rationale.**
- The E-value alone is hard to interpret and often misused [103,104].
- Cinelli–Hazlett express sensitivity as partial R² *relative to observed covariates* [20]. Chernozhukov et al. extend this to DML and general causal parameters [21]. Austen plots do the same for any ML model [22]. Calibrating to observed covariates dates to Imbens [77] and Hsu & Small [76].
- Our unusual asset: we can *measure* where real, clinically important confounders sit on the sensitivity contour. For LVEF and NT-proBNP these are the observed partial R² with treatment and outcome after conditioning on each PS spec. We can show that adding the ECG pulls those points toward the origin.

**Inputs.**
- Matched cohorts.
- A fixed-horizon outcome, e.g., 1- or 3-year risk with IPCW for censoring, for the linear/DML framework.
- For Cox: the bias formulas of Lin, Psaty & Kronmal [79] and Lin et al. [78], or the survival sensitivity approach of Huang et al. [80].
- Benchmarks: LVEF, NT-proBNP, eGFR, BMI (echo subset), the ECG block itself, and the CLMBR-T block.

**Estimand and analysis.**
- Risk difference at the horizon.
- For each trial and spec: the robustness value RV_{q=1} and RV_{q=1,α=0.05}; bounds at 1×, 2× and 3× each benchmark; and the empirical (R²_{Y~P|A,X}, R²_{A~P|X}) of each held-out physiology variable before and after adding the ECG.
- DML version with cross-fitted nuisance models (DoubleML / sensemakr).
- As a by-product: E-values for the HRs [23], a meta-analytic E-value across the 38 trials [39], and the "E-value of the ECG shift" (the confounding strength equivalent to the change from S to S+ECG).

**Output.**
- eFigure: contour plot for one exemplar trial, with benchmark points under S and S+ECG.
- eTable: RVs for all 38 trials by spec.
- Results sentence: "In the median trial, an unmeasured confounder would need to be X times as strongly associated with treatment and outcome as LVEF to move the estimate to the null. Adding the ECG increased this by Y."

**Caveats.**
- Partial-R² formulas are exact for linear models. For time-to-event outcomes use fixed-horizon risks or state the approximation.
- Benchmark-based bounds assume unmeasured confounders are no stronger than k × the benchmark, which is a judgement.
- Benchmarking with echo variables applies only to the subset.
- Report as supplementary sensitivity, not primary inference.

### 4.4 Prognostic-score balance, overlap and bias-amplification diagnostics

**Rationale.**
- Fifty-eight univariate SMDs are hard to summarise and treat all variables alike.
- Balance on a prognostic score weights each covariate by its outcome relevance [24,25]. It is the natural single-number summary of "balance that matters for bias".
- Adding a strong treatment predictor that is weakly prognostic can *increase* bias and variance [5,6,29]. High-dimensional PS covariates also threaten overlap [30].
- Reviewers will check whether the ECG gains come with worse overlap.

**Inputs.**
- For each trial, a prognostic model for the primary outcome, fit **out of sample**: either a random 20–30% pilot split discarded from analysis [81], or the comparator arm with cross-fitting [26].
- Two versions:
  - (i) PS_phys: held-out physiology only. This is the primary version and is not circular for ECG specs.
  - (ii) PS_full: codes + physiology + ECG.
- Optionally, external AI-ECG prognostic scores (mortality or HF risk) [115–117]. These are circular for ECG specs, so they are descriptive only.

**Estimand and analysis.**
- After matching under each spec: SMD of the prognostic score, and the difference in mean predicted risk between arms (the expected confounding bias on the risk scale if the prognostic model were correct).
- Diagnostics:
  - PS C-statistic, noting it is not a balance metric [28];
  - preference-score equipoise (% of patients between 0.3 and 0.7) [27];
  - matched fraction and effective sample size;
  - a likelihood-ratio test of the ECG PCs for the outcome, given treatment and spec covariates, in the comparator arm. The Z-bias check: if the ECG predicts treatment but not outcome, gains are suspect.
  - trimming sensitivity [85–87].
- Optional: joint PS + prognostic-score matching as an alternative way to use the ECG [26,82].

**Output.**
- Main figure panel: prognostic-score SMD (PS_phys) by spec across 38 trials (dot plot with medians), next to the existing held-out SMD panel.
- eTable: C-statistic, equipoise, matched n and ECG–outcome LRT by spec.

**Caveats.**
- Prognostic models fit on analysis-cohort outcomes risk "peeking". Use sample splitting and prespecify.
- PS_phys is available only in the echo subset unless physiology is imputed.
- Prognostic-score balance covers measured prognostic factors only.
- The C-statistic rises with instrument-like variables. Interpret it together with the ECG–outcome association, never alone.

### 4.5 Proximal causal inference with two ECG-derived proxies (exploratory)

**Rationale.**
- Proximal inference identifies the effect under unmeasured confounding when two kinds of proxy are available [31,32,88]:
  - a treatment-inducing proxy Z, which may affect A but not Y except through U;
  - an outcome-inducing proxy W, which is related to A only through U.
- Epidemiology-facing introductions and regression-based two-stage estimators now exist [33,90], including right-censored time-to-event outcomes under additive hazards [34] (R package pci2s) and survival curves [91].
- Chen et al. (NeurIPS 2024) showed that proxies inferred from **two separate instances** of pre-treatment unstructured data (clinical notes) satisfy the identification conditions where naive single-instance proxies do not. They also give an odds-ratio falsification heuristic [35].
- A patient's index ECG and an earlier ECG are the direct analogue. This is the only method on the list that aims to *remove*, rather than *reduce*, the bias from the physiology the ECG measures.

**Inputs.**
- Patients with ≥2 pre-baseline ECGs, e.g., the index ECG within 90 days and an earlier ECG ≥180 days before the index.
- An ECG→phenotype predictor (predicted LVEF or NT-proBNP) trained **outside** the trial cohorts, or supervised projections of the 32 PCs.
- Z = prediction from the index ECG. It is seen by the prescriber, so it may drive A.
- W = prediction from the earlier ECG. It must be independent of A given U and X.
- X = the demographic or sparse PS covariates.

**Estimand and analysis.**
- Risk difference at a fixed horizon, or an additive-hazard effect, using two-stage regression PCI [33,34].
- Neural or kernel bridge-function estimators as sensitivity [93,94].
- Validation where truth is known:
  - (i) **plasmode**: the hidden LVEF confounder with known HR 0.80. Compare the bias removed by PS+ECG (~14%) with the bias removed by proximal adjustment;
  - (ii) **echo subset**: compare the proximal estimate with the LVEF-adjusted estimate;
  - (iii) RCT agreement, descriptive only.
- Check the assumptions with the Chen et al. odds-ratio heuristic [35] and, in the echo subset, a direct test of W ⊥ A | LVEF, X. Where many candidate proxies exist, DANCE-style proxy validation [95] is an option.

**Output.**
- eFigure: plasmode bias removed, with bootstrap CIs, for PS, PS+ECG and proximal.
- Discussion paragraph framing ECG embeddings as candidate negative-control proxies, citing Veitch et al.'s "embeddings as proxies" argument [92,131].

**Caveats.**
- The identifying assumptions are strong and partly untestable. W's measurement error must be independent of Z's given U, which fails if both ECGs share stable non-U traits (body habitus, lead placement).
- Completeness requires the proxies to be at least as rich as U. A scalar U with scalar proxies is the easiest case.
- Variance is large with weak proxies.
- The additive-hazards scale differs from the trial HR.
- Requiring two ECGs selects sicker, more-monitored patients.
- Present as proof of concept in the supplement.

---

## 5. Practical notes and pitfalls

- **Pre-specify** the NCO list, the prognostic-model sample split, and the proxy definitions in a protocol amendment before running analyses. OHDSI's objective-diagnostics framework makes pre-specified thresholds (e.g., EASE < 0.25) part of study validity [12].
- **E-values** should be reported alongside benchmarked sensitivity, not alone [99,103]. Brophy's *Circulation: Population Health and Outcomes* commentary shows that cardiology editors reward explicit bias analysis [105].
- **The C-statistic is not a balance metric**, and adding instrument-like variables raises it while harming inference [5,28,29].
- **Adherence estimands.** Per-protocol analyses reintroduce healthy-adherer bias. Accident and screening endpoints are the standard falsification checks [42,43,122].
- **Language.** Frame gains as "partial proxy adjustment" consistent with theory [1] and with the polygenic-score analogue [4]. Avoid "removes confounding".
- **Reporting.** Follow TARGET [45]; it explicitly asks for sensitivity analyses to assumptions.

---

## 6. Items not fully verified

- **ReClaim (Ma et al., arXiv 2605.02740)** [partially verified]. The abstract confirms "in a target trial emulation it reduced systematic bias by 72% on average relative to Delphi". It does not state whether systematic bias was measured with negative control outcomes. That detail comes from a search snippet in our earlier notes. The paper is a preprint.
- **Wang H et al., medRxiv 2026 (PMID 42528508)**: verified in PubMed, but a preprint that has not been peer reviewed.
- **Lopez-Paz & Oquab (arXiv 1610.06545)**: the arXiv record was verified. The ICLR 2017 venue was not re-verified this session.
- **Ying, Cui & Tchetgen Tchetgen (arXiv 2204.13144)**: the arXiv record was verified; we did not check whether a journal version exists.
- **Zhang B et al., *Diabetes Obes Metab* 2026 (PMID 42660859)**: title, journal and DOI verified. PubMed had no abstract, so the "empirically calibrated" description rests on the title only.
- **Venue details.** Conference venues for NeurIPS/ICML/UAI papers were checked on proceedings sites via search results, not by downloading each paper.
- **The ≈R² bias-removal relation** in Section 2 is our own derivation under a linear model, not a quoted result.
- **The German 2025 author list** was taken from PubMed (the Crossref author order places a consortium collaborator oddly).
- **"BENCHMARK" in the brief.** We read this as BenchExCal [139], the Dahabreh–Robins–Hernán benchmarking framework [62] and the OHDSI Methods Benchmark [140]. If a specific project named BENCHMARK was meant, we did not identify it.
- **No precedent for AI-ECG embeddings as confounding adjusters.** Consistent with our 2026-09-25 search, this session again found no published study using AI-ECG waveform embeddings or AI-ECG scalars for confounding adjustment in comparative-effectiveness research. The closest are text or NLP proxies [55,56,188], polygenic scores [4] and claims foundation-model embeddings [73]. Absence from searches does not prove novelty.
- **Not cited because unverified in this session**: Greenland 1980 on confounder misclassification; LaLonde 1986 (Crossref DOI lookup failed); Han et al. medRxiv 2026 on procedure-name embeddings (cited in our earlier notes, but its DOI prefix could not be re-checked).

---

## 7. References

1. Ogburn EL, VanderWeele TJ. On the Nondifferential Misclassification of a Binary Confounder. *Epidemiology*. 2012;23(3):433-439. doi:10.1097/EDE.0b013e31824d1f63. PMID: 22450692
2. Stürmer T, Schneeweiss S, Avorn J, Glynn RJ. Adjusting Effect Estimates for Unmeasured Confounding with Validation Data using Propensity Score Calibration. *American Journal of Epidemiology*. 2005;162(3):279-289. doi:10.1093/aje/kwi192. PMID: 15987725
3. Kuroki M, Pearl J. Measurement bias and effect restoration in causal inference. *Biometrika*. 2014;101(2):423-437. doi:10.1093/biomet/ast066
4. German J, Yang Z, Urbut S, Vartiainen P; FinnGen; Natarajan P, Patorno E, Kutalik Z, Philippakis A, Ganna A. Incorporating genetic data improves target trial emulations and informs the use of polygenic scores in randomized controlled trial design. *Nature Genetics*. 2025;57(7):1620-1627. doi:10.1038/s41588-025-02229-8. PMID: 40533517
5. Myers JA, Rassen JA, Gagne JJ, Huybrechts KF, Schneeweiss S, Rothman KJ, et al. Effects of Adjusting for Instrumental Variables on Bias and Precision of Effect Estimates. *American Journal of Epidemiology*. 2011;174(11):1213-1222. doi:10.1093/aje/kwr364. PMID: 22025356
6. Pearl J. Invited Commentary: Understanding Bias Amplification. *American Journal of Epidemiology*. 2011;174(11):1223-1227. doi:10.1093/aje/kwr352. PMID: 22034488
7. Heyard R, Held L, Schneeweiss S, Wang SV. Design differences and variation in results between randomised trials and non-randomised emulations: meta-analysis of RCT-DUPLICATE data. *BMJ Medicine*. 2024;3(1):e000709. doi:10.1136/bmjmed-2023-000709. PMID: 38348308
8. Wang C, Tang D, von Dadelszen P, Ju C, Liu L, Wang Y, et al. Concordance between target trial emulation and randomised controlled trials: systematic review and meta-analysis. *BMJ*. 2026;393:e086810. doi:10.1136/bmj-2025-086810. PMID: 42156120
9. Lipsitch M, Tchetgen Tchetgen E, Cohen T. Negative Controls. *Epidemiology*. 2010;21(3):383-388. doi:10.1097/EDE.0b013e3181d61eeb. PMID: 20335814
10. Schuemie MJ, Ryan PB, DuMouchel W, Suchard MA, Madigan D. Interpreting observational studies: why empirical calibration is needed to correct p‐values. *Statistics in Medicine*. 2014;33(2):209-218. doi:10.1002/sim.5925. PMID: 23900808
11. Schuemie MJ, Hripcsak G, Ryan PB, Madigan D, Suchard MA. Empirical confidence interval calibration for population-level effect estimation studies in observational healthcare data. *Proceedings of the National Academy of Sciences*. 2018;115(11):2571-2577. doi:10.1073/pnas.1708282114. PMID: 29531023
12. Conover MM, Ryan PB, Chen Y, Suchard MA, Hripcsak G, Schuemie MJ. Objective study validity diagnostics: a framework requiring pre-specified, empirical verification to increase trust in the reliability of real-world evidence. *Journal of the American Medical Informatics Association*. 2025;32(3):518-525. doi:10.1093/jamia/ocae317. PMID: 39789670
13. Suchard MA, Schuemie MJ, Krumholz HM, You SC, Chen R, Pratt N, et al. Comprehensive comparative effectiveness and safety of first-line antihypertensive drug classes: a systematic, multinational, large-scale analysis. *The Lancet*. 2019;394(10211):1816-1826. doi:10.1016/S0140-6736(19)32317-7. PMID: 31668726
14. Khera R, Aminorroaya A, Dhingra LS, Thangaraj PM, Pedroso Camargos A, Bu F, et al. Comparative Effectiveness of Second-Line Antihyperglycemic Agents for Cardiovascular Outcomes. *Journal of the American College of Cardiology*. 2024;84(10):904-917. doi:10.1016/j.jacc.2024.05.069. PMID: 39197980
15. Bu F, Wu R, Ostropolets A, Aminorroaya A, Chen HY, Chai Y, et al. Comparative Cardiovascular Effectiveness of Glucagon-Like Peptide 1 Receptor Agonists and Sodium-Glucose Cotransporter 2 Inhibitors in Diabetes Mellitus. *JACC*. 2026;87(21):2963-2977. doi:10.1016/j.jacc.2026.02.5123. PMID: 41984016
16. Lunt M, Glynn RJ, Rothman KJ, Avorn J, Stürmer T. Propensity Score Calibration in the Absence of Surrogacy. *American Journal of Epidemiology*. 2012;175(12):1294-1302. doi:10.1093/aje/kwr463. PMID: 22688682
17. Lin HW, Chen YH. Adjustment for Missing Confounders in Studies Based on Observational Databases: 2-Stage Calibration Combining Propensity Scores From Primary and Validation Data. *American Journal of Epidemiology*. 2014;180(3):308-317. doi:10.1093/aje/kwu130. PMID: 24966224
18. McCandless LC, Richardson S, Best N. Adjustment for Missing Confounders Using External Validation Data and Propensity Scores. *Journal of the American Statistical Association*. 2012;107(497):40-51. doi:10.1080/01621459.2011.643739
19. Toh S, García Rodríguez LA, Hernán MA. Analyzing partially missing confounder information in comparative effectiveness and safety research of therapeutics. *Pharmacoepidemiology and Drug Safety*. 2012;21(S2):13-20. doi:10.1002/pds.3248. PMID: 22552975
20. Cinelli C, Hazlett C. Making Sense of Sensitivity: Extending Omitted Variable Bias. *Journal of the Royal Statistical Society Series B: Statistical Methodology*. 2020;82(1):39-67. doi:10.1111/rssb.12348
21. Chernozhukov V, Cinelli C, Newey WK, Sharma A, Syrgkanis V. Long Story Short: Omitted Variable Bias in Causal Machine Learning. *Review of Economics and Statistics*. 2026:1-45. doi:10.1162/REST.a.1705
22. Veitch V, Zaveri A. Sense and sensitivity analysis: simple post-hoc analysis of bias due to unobserved confounding. In: *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. 2020. arXiv:2003.01747. doi:10.48550/arXiv.2003.01747
23. VanderWeele TJ, Ding P. Sensitivity Analysis in Observational Research: Introducing the E-Value. *Annals of Internal Medicine*. 2017;167(4):268-274. doi:10.7326/M16-2607. PMID: 28693043
24. Hansen BB. The prognostic analogue of the propensity score. *Biometrika*. 2008;95(2):481-488. doi:10.1093/biomet/asn004
25. Stuart EA, Lee BK, Leacy FP. Prognostic score–based balance measures can be a useful diagnostic for propensity score methods in comparative effectiveness research. *Journal of Clinical Epidemiology*. 2013;66(8):S84-S90.e1. doi:10.1016/j.jclinepi.2013.01.013. PMID: 23849158
26. Leacy FP, Stuart EA. On the joint use of propensity and prognostic scores in estimation of the average treatment effect on the treated: a simulation study. *Statistics in Medicine*. 2014;33(20):3488-3508. doi:10.1002/sim.6030. PMID: 24151187
27. Walker A, Patrick, Lauer, Hornbrook, Marin, Platt, et al. A tool for assessing the feasibility of comparative effectiveness research. *Comparative Effectiveness Research*. 2013:11. doi:10.2147/CER.S40357
28. Westreich D, Cole SR, Funk MJ, Brookhart MA, Stürmer T. The role of the c‐statistic in variable selection for propensity score models. *Pharmacoepidemiology and Drug Safety*. 2011;20(3):317-320. doi:10.1002/pds.2074. PMID: 21351315
29. Brookhart MA, Schneeweiss S, Rothman KJ, Glynn RJ, Avorn J, Stürmer T. Variable Selection for Propensity Score Models. *American Journal of Epidemiology*. 2006;163(12):1149-1156. doi:10.1093/aje/kwj149. PMID: 16624967
30. D’Amour A, Ding P, Feller A, Lei L, Sekhon J. Overlap in observational studies with high-dimensional covariates. *Journal of Econometrics*. 2021;221(2):644-654. doi:10.1016/j.jeconom.2019.10.014
31. Miao W, Geng Z, Tchetgen Tchetgen EJ. Identifying causal effects with proxy variables of an unmeasured confounder. *Biometrika*. 2018;105(4):987-993. doi:10.1093/biomet/asy038. PMID: 33343006
32. Tchetgen Tchetgen EJ, Ying A, Cui Y, Shi X, Miao W. An Introduction to Proximal Causal Inference. *Statistical Science*. 2024;39(3). doi:10.1214/23-STS911
33. Liu J, Park C, Li K, Tchetgen Tchetgen EJ. Regression-based proximal causal inference. *American Journal of Epidemiology*. 2025;194(7):2030-2036. doi:10.1093/aje/kwae370. PMID: 39323264
34. Li KQ, Linderman GC, Shi X, Tchetgen Tchetgen EJ. Regression-based Proximal Causal Inference for Right-censored Time-to-event Data. *Epidemiology*. 2025;36(5):694-704. doi:10.1097/EDE.0000000000001884. PMID: 40513053
35. Chen JM, Bhattacharya R, Keith KA. Proximal causal inference with text data. In: *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*. 2024. arXiv:2401.06687. doi:10.48550/arXiv.2401.06687
36. Huling JD, Mak S. Energy balancing of covariate distributions. *Journal of Causal Inference*. 2024;12(1):20220029. doi:10.1515/jci-2022-0029
37. Zhu Y, Savage JS, Ghosh D. A Kernel-Based Metric for Balance Assessment. *Journal of Causal Inference*. 2018;6(2):20160029. doi:10.1515/jci-2016-0029. PMID: 30498678
38. Gretton A, Borgwardt KM, Rasch MJ, Schölkopf B, Smola A. A kernel two-sample test. *Journal of Machine Learning Research*. 2012;13:723-773. https://jmlr.org/papers/v13/gretton12a.html (JMLR does not assign DOIs)
39. Mathur MB, VanderWeele TJ. Sensitivity Analysis for Unmeasured Confounding in Meta-Analyses. *Journal of the American Statistical Association*. 2020;115(529):163-172. doi:10.1080/01621459.2018.1529598. PMID: 32981992
40. Rosenbaum PR. *Observational Studies*. 2nd ed. New York: Springer; 2002. doi:10.1007/978-1-4757-3692-2
41. Simonsohn U, Simmons JP, Nelson LD. Specification curve analysis. *Nature Human Behaviour*. 2020;4(11):1208-1214. doi:10.1038/s41562-020-0912-z. PMID: 32719546
42. Dormuth CR, Patrick AR, Shrank WH, Wright JM, Glynn RJ, Sutherland J, et al. Statin Adherence and Risk of Accidents. *Circulation*. 2009;119(15):2051-2057. doi:10.1161/CIRCULATIONAHA.108.824151. PMID: 19349320
43. Brookhart MA, Patrick AR, Dormuth C, Avorn J, Shrank W, Cadarette SM, et al. Adherence to Lipid-lowering Therapy and the Use of Preventive Health Services: An Investigation of the Healthy User Effect. *American Journal of Epidemiology*. 2007;166(3):348-354. doi:10.1093/aje/kwm070. PMID: 17504779
44. Sloot R, Breskin A, Colantonio LD, Allmon AG, Yu Y, Sakhuja S, et al. Comparing PCSK9 Monoclonal Antibody Treatment Strategies Following Myocardial Infarction Using Negative Control Outcomes: A Target Trial Emulation Study. *Epidemiology*. 2024;35(4):579-588. doi:10.1097/EDE.0000000000001730. PMID: 38629975
45. Cashin AG, Hansford HJ, Hernán MA, Swanson SA, Lee H, Jones MD, et al. Transparent Reporting of Observational Studies Emulating a Target Trial—The TARGET Statement. *JAMA*. 2025;334(12):1084. doi:10.1001/jama.2025.13350. PMID: 40899949
46. Brookhart MA, Wang PS, Solomon DH, Schneeweiss S. Evaluating Short-Term Drug Effects Using a Physician-Specific Prescribing Preference as an Instrumental Variable. *Epidemiology*. 2006;17(3):268-275. doi:10.1097/01.ede.0000193606.58671.c5. PMID: 16617275
47. Garabedian LF, Chu P, Toh S, Zaslavsky AM, Soumerai SB. Potential Bias of Instrumental Variable Analyses for Observational Comparative Effectiveness Research. *Annals of Internal Medicine*. 2014;161(2):131-138. doi:10.7326/M13-1887. PMID: 25023252
48. Lawlor DA, Tilling K, Davey Smith G. Triangulation in aetiological epidemiology. *International Journal of Epidemiology*. 2016;45(6):1866-1886. doi:10.1093/ije/dyw314. PMID: 28108528
49. Gill D, Georgakis MK, Walker VM, Schmidt AF, Gkatzionis A, Freitag DF, et al. Mendelian randomization for studying the effects of perturbing drug targets. *Wellcome Open Research*. 2021;6:16. doi:10.12688/wellcomeopenres.16544.2. PMID: 33644404
50. Kallus N, Puli AM, Shalit U. Removing hidden confounding by experimental grounding. In: *Advances in Neural Information Processing Systems 31 (NeurIPS 2018)*. 2018. arXiv:1810.11646. doi:10.48550/arXiv.1810.11646
51. Colnet B, Mayer I, Chen G, Dieng A, Li R, Varoquaux G, et al. Causal Inference Methods for Combining Randomized Trials and Observational Studies: A Review. *Statistical Science*. 2024;39(1). doi:10.1214/23-STS889. PMID: 41059256
52. Wang Y, Blei DM. The Blessings of Multiple Causes. *Journal of the American Statistical Association*. 2019;114(528):1574-1596. doi:10.1080/01621459.2019.1686987
53. Ogburn EL, Shpitser I, Tchetgen Tchetgen EJ. Comment on "Blessings of multiple causes". arXiv:1910.05438. doi:10.48550/arXiv.1910.05438; 2019
54. Fan Z, Yang Q, Hu Y, Danaei G, Davey Smith G, Rao S, et al. Evaluating bias in target trial emulation for heart failure across statistical and deep learning methods. *Nature Communications*. 2026;17(1):8618. doi:10.1038/s41467-026-74999-6. PMID: 42443168
55. Wyss R, Yang J, Schneeweiss S, Plasek JM, Zhou L, Deramus T, et al. Natural language processing for scalable feature engineering and ultra-high-dimensional confounding adjustment in healthcare database studies. *Journal of Biomedical Informatics*. 2025;169:104882. doi:10.1016/j.jbi.2025.104882. PMID: 40691893
56. Zeng J, Gensheimer MF, Rubin DL, Athey S, Shachter RD. Uncovering interpretable potential confounders in electronic medical records. *Nature Communications*. 2022;13(1):1014. doi:10.1038/s41467-022-28546-8. PMID: 35197467
57. Patorno E, Gopalakrishnan C, Franklin JM, Brodovicz KG, Masso‐Gonzalez E, Bartels DB, et al. Claims‐based studies of oral glucose‐lowering medications can achieve balance in critical clinical variables only observed in electronic health records. *Diabetes, Obesity and Metabolism*. 2018;20(4):974-984. doi:10.1111/dom.13184. PMID: 29206336
58. Franklin JM, Patorno E, Desai RJ, Glynn RJ, Martin D, Quinto K, et al. Emulating Randomized Clinical Trials With Nonrandomized Real-World Evidence Studies. *Circulation*. 2021;143(10):1002-1013. doi:10.1161/CIRCULATIONAHA.120.051718. PMID: 33327727
59. Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity‐score matched samples. *Statistics in Medicine*. 2009;28(25):3083-3107. doi:10.1002/sim.3697. PMID: 19757444
60. Bots SH, Schultze A, Pajouheshnia R, Douglas IJ, Gini R, Klungel OH, et al. Negative controls and how to use them: a guidance paper. *International Journal of Epidemiology*. 2026;55(5):dyag163. doi:10.1093/ije/dyag163. PMID: 42667681
61. Wang SV, Schneeweiss S, RCT-DUPLICATE Initiative, Franklin JM, Desai RJ, Feldman W, et al. Emulation of Randomized Clinical Trials With Nonrandomized Database Analyses. *JAMA*. 2023;329(16):1376. doi:10.1001/jama.2023.4221. PMID: 37097356
62. Dahabreh IJ, Robins JM, Hernán MA. Benchmarking Observational Methods by Comparing Randomized Trials and Their Emulations. *Epidemiology*. 2020;31(5):614-619. doi:10.1097/EDE.0000000000001231. PMID: 32740470
63. Franklin JM, Schneeweiss S, Polinski JM, Rassen JA. Plasmode simulation for the evaluation of pharmacoepidemiologic methods in complex healthcare databases. *Computational Statistics & Data Analysis*. 2014;72:219-226. doi:10.1016/j.csda.2013.10.018. PMID: 24587587
64. Tian Y, Schuemie MJ, Suchard MA. Evaluating large-scale propensity score performance through real-world and synthetic data experiments. *International Journal of Epidemiology*. 2018;47(6):2005-2014. doi:10.1093/ije/dyy120. PMID: 29939268
65. Schneeweiss S, Rassen JA, Glynn RJ, Avorn J, Mogun H, Brookhart MA. High-dimensional Propensity Score Adjustment in Studies of Treatment Effects Using Health Care Claims Data. *Epidemiology*. 2009;20(4):512-522. doi:10.1097/EDE.0b013e3181a663cc. PMID: 19487948
66. Weckstein AR, Wang SV, Wyss R, Schneeweiss S. Scalable confounding adjustment in real-world evidence: benchmarking data-adaptive and investigator-specified strategies in a large-scale trial emulation study. *Journal of the American Medical Informatics Association*. 2026;33(3):573-586. doi:10.1093/jamia/ocaf204. PMID: 41338229
67. Steinberg E, Jung K, Fries JA, Corbin CK, Pfohl SR, Shah NH. Language models are an effective representation learning technique for electronic health record data. *Journal of Biomedical Informatics*. 2021;113:103637. doi:10.1016/j.jbi.2020.103637. PMID: 33290879
68. Voss EA, Boyce RD, Ryan PB, van der Lei J, Rijnbeek PR, Schuemie MJ. Accuracy of an automated knowledge base for identifying drug adverse reactions. *Journal of Biomedical Informatics*. 2017;66:72-81. doi:10.1016/j.jbi.2016.12.005. PMID: 27993747
69. Hwang H, Quiroz JC, Gallego B. Assessing the effectiveness of empirical calibration under different bias scenarios. *BMC Medical Research Methodology*. 2022;22(1):208. doi:10.1186/s12874-022-01687-6. PMID: 35896966
70. Schuemie MJ, Ryan PB, Pratt N, Chen R, You SC, Krumholz HM, et al. Principles of Large-scale Evidence Generation and Evaluation across a Network of Databases (LEGEND). *Journal of the American Medical Informatics Association*. 2020;27(8):1331-1337. doi:10.1093/jamia/ocaa103. PMID: 32909033
71. Hripcsak G, Suchard MA, Shea S, Chen R, You SC, Pratt N, et al. Comparison of Cardiovascular and Safety Outcomes of Chlorthalidone vs Hydrochlorothiazide to Treat Hypertension. *JAMA Internal Medicine*. 2020;180(4):542. doi:10.1001/jamainternmed.2019.7454. PMID: 32065600
72. Zhang B, Zhou T, Tang H, Lu Y, Zhang D, Chen J, et al. Comparative Effectiveness of GLP-1RAs, SGLT2is and DPP4is for Cardiovascular Outcomes in Type 2 Diabetes: An Empirically Calibrated Target Trial Emulation Study. *Diabetes, Obesity and Metabolism*. 2026:dom.71244. doi:10.1111/dom.71244. PMID: 42660859
73. Ma F, Liu Y, Lan X, Zhou W, Ni J, Giuffrè M, et al. Foundation models to unlock real-world evidence from nationwide medical claims. arXiv:2605.02740. doi:10.48550/arXiv.2605.02740; 2026 (preprint) [partially verified, see Section 6]
74. Sturmer T, Schneeweiss S, Rothman KJ, Avorn J, Glynn RJ. Performance of Propensity Score Calibration--A Simulation Study. *American Journal of Epidemiology*. 2007;165(10):1110-1118. doi:10.1093/aje/kwm074. PMID: 17395595
75. Stürmer T, Glynn RJ, Rothman KJ, Avorn J, Schneeweiss S. Adjustments for Unmeasured Confounders in Pharmacoepidemiologic Database Studies Using External Information. *Medical Care*. 2007;45(10):S158-S165. doi:10.1097/MLR.0b013e318070c045. PMID: 17909375
76. Hsu JY, Small DS. Calibrating Sensitivity Analyses to Observed Covariates in Observational Studies. *Biometrics*. 2013;69(4):803-811. doi:10.1111/biom.12101. PMID: 24328711
77. Imbens GW. Sensitivity to Exogeneity Assumptions in Program Evaluation. *American Economic Review*. 2003;93(2):126-132. doi:10.1257/000282803321946921
78. Lin NX, Logan S, Henley WE. Bias and Sensitivity Analysis When Estimating Treatment Effects from the Cox Model with Omitted Covariates. *Biometrics*. 2013;69(4):850-860. doi:10.1111/biom.12096. PMID: 24224574
79. Lin DY, Psaty BM, Kronmal RA. Assessing the Sensitivity of Regression Results to Unmeasured Confounders in Observational Studies. *Biometrics*. 1998;54(3):948. doi:10.2307/2533848
80. Huang R, Xu R, Dulai PS. Sensitivity analysis of treatment effect to unmeasured confounding in observational studies with survival and competing risks outcomes. *Statistics in Medicine*. 2020;39(24):3397-3411. doi:10.1002/sim.8672. PMID: 32677758
81. Aikens RC, Greaves D, Baiocchi M. A pilot design for observational studies: Using abundant data thoughtfully. *Statistics in Medicine*. 2020;39(30):4821-4840. doi:10.1002/sim.8754. PMID: 33015867
82. Wyss R, Ellis AR, Brookhart MA, Jonsson Funk M, Girman CJ, Simpson RJ, et al. Matching on the disease risk score in comparative effectiveness research of new treatments. *Pharmacoepidemiology and Drug Safety*. 2015;24(9):951-961. doi:10.1002/pds.3810. PMID: 26112690
83. Glynn RJ, Gagne JJ, Schneeweiss S. Role of disease risk scores in comparative effectiveness research with emerging therapies. *Pharmacoepidemiology and Drug Safety*. 2012;21(S2):138-147. doi:10.1002/pds.3231. PMID: 22552989
84. Arbogast PG, Ray WA. Use of disease risk scores in pharmacoepidemiologic studies. *Statistical Methods in Medical Research*. 2009;18(1):67-80. doi:10.1177/0962280208092347. PMID: 18562398
85. Crump RK, Hotz VJ, Imbens GW, Mitnik OA. Dealing with limited overlap in estimation of average treatment effects. *Biometrika*. 2009;96(1):187-199. doi:10.1093/biomet/asn055
86. Sturmer T, Rothman KJ, Avorn J, Glynn RJ. Treatment Effects in the Presence of Unmeasured Confounding: Dealing With Observations in the Tails of the Propensity Score Distribution--A Simulation Study. *American Journal of Epidemiology*. 2010;172(7):843-854. doi:10.1093/aje/kwq198. PMID: 20716704
87. Glynn RJ, Lunt M, Rothman KJ, Poole C, Schneeweiss S, Stürmer T. Comparison of alternative approaches to trim subjects in the tails of the propensity score distribution. *Pharmacoepidemiology and Drug Safety*. 2019;28(10):1290-1298. doi:10.1002/pds.4846. PMID: 31385394
88. Cui Y, Pu H, Shi X, Miao W, Tchetgen Tchetgen E. Semiparametric Proximal Causal Inference. *Journal of the American Statistical Association*. 2024;119(546):1348-1359. doi:10.1080/01621459.2023.2191817
89. Shi X, Miao W, Nelson JC, Tchetgen Tchetgen EJ. Multiply Robust Causal Inference with Double-Negative Control Adjustment for Categorical Unmeasured Confounding. *Journal of the Royal Statistical Society Series B: Statistical Methodology*. 2020;82(2):521-540. doi:10.1111/rssb.12361. PMID: 33376449
90. Zivich PN, Cole SR, Edwards JK, Mulholland GE, Shook-Sa BE, Tchetgen Tchetgen EJ. INTRODUCING PROXIMAL CAUSAL INFERENCE FOR EPIDEMIOLOGISTS. *American Journal of Epidemiology*. 2023;192(7):1224-1227. doi:10.1093/aje/kwad077. PMID: 37005072
91. Ying A, Cui Y, Tchetgen Tchetgen EJ. Proximal causal inference for marginal counterfactual survival curves. arXiv:2204.13144. doi:10.48550/arXiv.2204.13144; 2022 (preprint)
92. Veitch V, Wang Y, Blei DM. Using embeddings to correct for unobserved confounding in networks. In: *Advances in Neural Information Processing Systems 32 (NeurIPS 2019)*. 2019:13792-13802. arXiv:1902.04114. doi:10.48550/arXiv.1902.04114
93. Kompa B, Bellamy D, Kolokotrones T, Robins JM, Beam AL. Deep learning methods for proximal inference via maximum moment restriction. In: *Advances in Neural Information Processing Systems 35 (NeurIPS 2022)*. 2022. arXiv:2205.09824. doi:10.48550/arXiv.2205.09824
94. Mastouri A, Zhu Y, Gultchin L, Korba A, Silva R, Kusner M, et al. Proximal causal learning with kernels: two-stage estimation and moment restriction. In: *Proceedings of the 38th International Conference on Machine Learning (ICML)*. PMLR 139; 2021:7512-7523. arXiv:2105.04544. doi:10.48550/arXiv.2105.04544
95. Kummerfeld E, Lim J, Shi X. Data-driven automated negative control estimation (DANCE): search for, validation of, and causal inference with negative controls. *Journal of Machine Learning Research*. 2024;25(229):1-35. arXiv:2210.00528. doi:10.48550/arXiv.2210.00528. https://jmlr.org/papers/v25/22-1062.html
96. Ding P, VanderWeele TJ. Sensitivity Analysis Without Assumptions. *Epidemiology*. 2016;27(3):368-377. doi:10.1097/EDE.0000000000000457. PMID: 26841057
97. Haneuse S, VanderWeele TJ, Arterburn D. Using the E-Value to Assess the Potential Effect of Unmeasured Confounding in Observational Studies. *JAMA*. 2019;321(6):602. doi:10.1001/jama.2018.21554. PMID: 30676631
98. Mathur MB, Ding P, Riddell CA, VanderWeele TJ. Web Site and R Package for Computing E-values. *Epidemiology*. 2018;29(5):e45-e47. doi:10.1097/EDE.0000000000000864. PMID: 29912013
99. VanderWeele TJ, Ding P, Mathur M. Technical Considerations in the Use of the E-Value. *Journal of Causal Inference*. 2019;7(2):20180007. doi:10.1515/jci-2018-0007
100. Lash TL, Fox MP, MacLehose RF, Maldonado G, McCandless LC, Greenland S. Good practices for quantitative bias analysis. *International Journal of Epidemiology*. 2014;43(6):1969-1985. doi:10.1093/ije/dyu149. PMID: 25080530
101. Schneeweiss S. Sensitivity analysis and external adjustment for unmeasured confounders in epidemiologic database studies of therapeutics. *Pharmacoepidemiology and Drug Safety*. 2006;15(5):291-303. doi:10.1002/pds.1200. PMID: 16447304
102. Bross IDJ. Spurious effects from an extraneous variable. *Journal of Chronic Diseases*. 1966;19(6):637-647. doi:10.1016/0021-9681(66)90062-2. PMID: 5966011
103. Ioannidis JPA, Tan YJ, Blum MR. Limitations and Misinterpretations of E-Values for Sensitivity Analyses of Observational Studies. *Annals of Internal Medicine*. 2019;170(2):108-111. doi:10.7326/M18-2159. PMID: 30597486
104. Blum MR, Tan YJ, Ioannidis JPA. Use of E-values for addressing confounding in observational studies—an empirical assessment of the literature. *International Journal of Epidemiology*. 2020;49(5):1482-1494. doi:10.1093/ije/dyz261. PMID: 31930286
105. Brophy JM. Causality in Observational Cardiology: “Chapeau” to a Bias Analysis Approach. *Circulation: Population Health and Outcomes*. 2026;19(2). doi:10.1161/CIRCOUTCOMES.125.013104. PMID: 41697665
106. Franklin JM, Rassen JA, Ackermann D, Bartels DB, Schneeweiss S. Metrics for covariate balance in cohort studies of causal effects. *Statistics in Medicine*. 2014;33(10):1685-1699. doi:10.1002/sim.6058. PMID: 24323618
107. Székely GJ, Rizzo ML. Energy statistics: A class of statistics based on distances. *Journal of Statistical Planning and Inference*. 2013;143(8):1249-1272. doi:10.1016/j.jspi.2013.03.018
108. Lopez-Paz D, Oquab M. Revisiting classifier two-sample tests. arXiv:1610.06545. doi:10.48550/arXiv.1610.06545; 2016 (ICLR 2017 venue not re-verified)
109. Kallus N. Generalized optimal matching methods for causal inference. *Journal of Machine Learning Research*. 2020;21:1-54. arXiv:1612.08321. doi:10.48550/arXiv.1612.08321. https://jmlr.org/papers/v21/19-120.html
110. Stuart EA. Matching Methods for Causal Inference: A Review and a Look Forward. *Statistical Science*. 2010;25(1). doi:10.1214/09-STS313. PMID: 20871802
111. Attia ZI, Kapa S, Lopez-Jimenez F, McKie PM, Ladewig DJ, Satam G, et al. Screening for cardiac contractile dysfunction using an artificial intelligence–enabled electrocardiogram. *Nature Medicine*. 2019;25(1):70-74. doi:10.1038/s41591-018-0240-2. PMID: 30617318
112. Sangha V, Nargesi AA, Dhingra LS, Khunte A, Mortazavi BJ, Ribeiro AH, et al. Detection of Left Ventricular Systolic Dysfunction From Electrocardiographic Images. *Circulation*. 2023;148(9):765-777. doi:10.1161/CIRCULATIONAHA.122.062646. PMID: 37489538
113. Yao X, Rushlow DR, Inselman JW, McCoy RG, Thacher TD, Behnken EM, et al. Artificial intelligence–enabled electrocardiograms for identification of patients with low ejection fraction: a pragmatic, randomized clinical trial. *Nature Medicine*. 2021;27(5):815-819. doi:10.1038/s41591-021-01335-4. PMID: 33958795
114. Attia ZI, Friedman PA, Noseworthy PA, Lopez-Jimenez F, Ladewig DJ, Satam G, et al. Age and Sex Estimation Using Artificial Intelligence From Standard 12-Lead ECGs. *Circulation: Arrhythmia and Electrophysiology*. 2019;12(9):e007284. doi:10.1161/CIRCEP.119.007284. PMID: 31450977
115. Raghunath S, Ulloa Cerna AE, Jing L, vanMaanen DP, Stough J, Hartzel DN, et al. Prediction of mortality from 12-lead electrocardiogram voltage data using a deep neural network. *Nature Medicine*. 2020;26(6):886-891. doi:10.1038/s41591-020-0870-z. PMID: 32393799
116. Sau A, Pastika L, Sieliwonczyk E, Patlatzoglou K, Ribeiro AH, McGurk KA, et al. Artificial intelligence-enabled electrocardiogram for mortality and cardiovascular risk estimation: a model development and validation study. *The Lancet Digital Health*. 2024;6(11):e791-e802. doi:10.1016/S2589-7500(24)00172-9. PMID: 39455192
117. Dhingra LS, Aminorroaya A, Sangha V, Pedroso AF, Asselbergs FW, Brant LCC, et al. Heart failure risk stratification using artificial intelligence applied to electrocardiogram images: a multinational study. *European Heart Journal*. 2025;46(11):1044-1053. doi:10.1093/eurheartj/ehae914. PMID: 39804243
118. Khurshid S, Friedman S, Reeder C, Di Achille P, Diamant N, Singh P, et al. ECG-Based Deep Learning and Clinical Risk Factors to Predict Atrial Fibrillation. *Circulation*. 2022;145(2):122-133. doi:10.1161/CIRCULATIONAHA.121.057480. PMID: 34743566
119. Diamant N, Reinertsen E, Song S, Aguirre AD, Stultz CM, Batra P. Patient contrastive learning: A performant, expressive, and practical approach to electrocardiogram modeling. *PLOS Computational Biology*. 2022;18(2):e1009862. doi:10.1371/journal.pcbi.1009862. PMID: 35157695
120. Ouyang D, He B, Ghorbani A, Yuan N, Ebinger J, Langlotz CP, et al. Video-based AI for beat-to-beat assessment of cardiac function. *Nature*. 2020;580(7802):252-256. doi:10.1038/s41586-020-2145-8. PMID: 32269341
121. He B, Kwan AC, Cho JH, Yuan N, Pollick C, Shiota T, et al. Blinded, randomized trial of sonographer versus AI cardiac function assessment. *Nature*. 2023;616(7957):520-524. doi:10.1038/s41586-023-05947-3. PMID: 37020027
122. Shrank WH, Patrick AR, Alan Brookhart M. Healthy User and Related Biases in Observational Studies of Preventive Interventions: A Primer for Physicians. *Journal of General Internal Medicine*. 2011;26(5):546-550. doi:10.1007/s11606-010-1609-1. PMID: 21203857
123. Simpson SH, Eurich DT, Majumdar SR, Padwal RS, Tsuyuki RT, Varney J, et al. A meta-analysis of the association between adherence to drug therapy and mortality. *BMJ*. 2006;333(7557):15. doi:10.1136/bmj.38875.675486.55. PMID: 16790458
124. Jackson LA, Jackson ML, Nelson JC, Neuzil KM, Weiss NS. Evidence of bias in estimates of influenza vaccine effectiveness in seniors. *International Journal of Epidemiology*. 2006;35(2):337-344. doi:10.1093/ije/dyi274. PMID: 16368725
125. Prasad V, Jena AB. Prespecified Falsification End Points. *JAMA*. 2013;309(3):241. doi:10.1001/jama.2012.96867. PMID: 23321761
126. Arnold BF, Ercumen A. Negative Control Outcomes. *JAMA*. 2016;316(24):2597. doi:10.1001/jama.2016.17700. PMID: 28027378
127. Chernozhukov V, Chetverikov D, Demirer M, Duflo E, Hansen C, Newey W, et al. Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal*. 2018;21(1):C1-C68. doi:10.1111/ectj.12097
128. van der Laan MJ, Rubin D. Targeted Maximum Likelihood Learning. *The International Journal of Biostatistics*. 2006;2(1). doi:10.2202/1557-4679.1043
129. Schuler MS, Rose S. Targeted Maximum Likelihood Estimation for Causal Inference in Observational Studies. *American Journal of Epidemiology*. 2017;185(1):65-73. doi:10.1093/aje/kww165. PMID: 27941068
130. Schulte R, Rügamer D, Nagler T. Adjustment for confounding using pre-trained representations. In: *Proceedings of the 42nd International Conference on Machine Learning (ICML)*. PMLR 267; 2025:53557-53580. arXiv:2506.14329. doi:10.48550/arXiv.2506.14329. https://proceedings.mlr.press/v267/schulte25a.html
131. Veitch V, Sridhar D, Blei DM. Adapting text embeddings for causal inference. In: *Proceedings of the 36th Conference on Uncertainty in Artificial Intelligence (UAI)*. PMLR 124; 2020. arXiv:1905.12741. doi:10.48550/arXiv.1905.12741. https://proceedings.mlr.press/v124/veitch20a.html
132. Shi C, Blei DM, Veitch V. Adapting neural networks for the estimation of treatment effects. In: *Advances in Neural Information Processing Systems 32 (NeurIPS 2019)*. 2019. arXiv:1906.02120. doi:10.48550/arXiv.1906.02120
133. Shalit U, Johansson FD, Sontag D. Estimating individual treatment effect: generalization bounds and algorithms. In: *Proceedings of the 34th International Conference on Machine Learning (ICML)*. PMLR 70; 2017. arXiv:1606.03976. doi:10.48550/arXiv.1606.03976. https://proceedings.mlr.press/v70/shalit17a.html
134. Louizos C, Shalit U, Mooij JM, Sontag D, Zemel R, Welling M. Causal effect inference with deep latent-variable models. In: *Advances in Neural Information Processing Systems 30 (NeurIPS 2017)*. 2017. arXiv:1705.08821. doi:10.48550/arXiv.1705.08821
135. Belloni A, Chernozhukov V, Hansen C. Inference on Treatment Effects after Selection among High-Dimensional Controls. *The Review of Economic Studies*. 2014;81(2):608-650. doi:10.1093/restud/rdt044
136. Shortreed SM, Ertefaie A. Outcome-Adaptive Lasso: Variable Selection for Causal Inference. *Biometrics*. 2017;73(4):1111-1122. doi:10.1111/biom.12679. PMID: 28273693
137. Weberpals J, Becker T, Davies J, Schmich F, Rüttinger D, Theis FJ, et al. Deep Learning-based Propensity Scores for Confounding Control in Comparative Effectiveness Research. *Epidemiology*. 2021;32(3):378-388. doi:10.1097/EDE.0000000000001338. PMID: 33591049
138. Neugebauer R, An J, Dombrowski SK, Oshiro C, Cassidy-Bushrow A, Gilliam L, et al. Glucose-Lowering Medication Classes and Cardiovascular Outcomes in Patients With Type 2 Diabetes. *JAMA Network Open*. 2025;8(10):e2536100. doi:10.1001/jamanetworkopen.2025.36100. PMID: 41091469
139. Wang SV, Russo M, Glynn RJ, Bradley MC, He J, Concato J, et al. A Benchmark, Expand, and Calibration (BenchExCal) Trial Emulation Approach for Using Real‐World Evidence to Support Indication Expansions: Design and Process for a Planned Empirical Evaluation. *Clinical Pharmacology & Therapeutics*. 2025;117(6):1820-1828. doi:10.1002/cpt.3621. PMID: 40067205
140. Schuemie MJ, Cepeda MS, Suchard MA, Yang J, Tian Y, Schuler A, et al. How confident are we about observational findings in health care: a benchmark study. *Harvard Data Science Review*. 2020;2(1). doi:10.1162/99608f92.147cc28e. PMID: 33367288
141. Tchetgen Tchetgen E. The Control Outcome Calibration Approach for Causal Inference With Unobserved Confounding. *American Journal of Epidemiology*. 2014;179(5):633-640. doi:10.1093/aje/kwt303. PMID: 24363326
142. Sofer T, Richardson DB, Colicino E, Schwartz J, Tchetgen Tchetgen EJ. On Negative Outcome Control of Unobserved Confounding as a Generalization of Difference-in-Differences. *Statistical Science*. 2016;31(3). doi:10.1214/16-STS558. PMID: 28239233
143. Zhang D, Zhang B, Wang H, Lu Y, Wolock CJ, Hu W, et al. Negative control-calibrated difference-in-difference analyses: addressing unmeasured confounding in RWD with application to racial/ethnic differences. *npj Digital Medicine*. 2025;8(1):452. doi:10.1038/s41746-025-01821-w. PMID: 40676203
144. Wang H, Zhang B, Lei Y, Lu Y, Zhang D, Jian X, et al. Distributional diagnosis and calibration with negative controls for outcome-wide real-world evidence. *medRxiv* [preprint]. 2026. doi:10.64898/2026.07.08.26357550. PMID: 42528508
145. Shi X, Miao W, Tchetgen ET. A Selective Review of Negative Control Methods in Epidemiology. *Current Epidemiology Reports*. 2020;7(4):190-202. doi:10.1007/s40471-020-00243-4. PMID: 33996381
146. ROSENBAUM PR. Sensitivity analysis for certain permutation inferences in matched observational studies. *Biometrika*. 1987;74(1):13-26. doi:10.1093/biomet/74.1.13
147. Rosenbaum PR. *Design of Observational Studies*. 2nd ed. Cham: Springer; 2020. doi:10.1007/978-3-030-46405-9
148. Rosenbaum PR, Silber JH. Amplification of Sensitivity Analysis in Matched Observational Studies. *Journal of the American Statistical Association*. 2009;104(488):1398-1405. doi:10.1198/jasa.2009.tm08470. PMID: 22888178
149. Rosenbaum PR, Rubin DB. Assessing Sensitivity to an Unobserved Binary Covariate in an Observational Study with Binary Outcome. *Journal of the Royal Statistical Society Series B: Statistical Methodology*. 1983;45(2):212-218. doi:10.1111/j.2517-6161.1983.tb01242.x
150. Zhao Q, Small DS, Bhattacharya BB. Sensitivity Analysis for Inverse Probability Weighting Estimators via the Percentile Bootstrap. *Journal of the Royal Statistical Society Series B: Statistical Methodology*. 2019;81(4):735-761. doi:10.1111/rssb.12327
151. Tan Z. A Distributional Approach for Causal Inference Using Propensity Scores. *Journal of the American Statistical Association*. 2006;101(476):1619-1637. doi:10.1198/016214506000000023
152. Dorn J, Guo K. Sharp Sensitivity Analysis for Inverse Propensity Weighting via Quantile Balancing. *Journal of the American Statistical Association*. 2023;118(544):2645-2657. doi:10.1080/01621459.2022.2069572
153. Niknam BA, Zubizarreta JR. Using Cardinality Matching to Design Balanced and Representative Samples for Observational Studies. *JAMA*. 2022;327(2):173. doi:10.1001/jama.2021.20555. PMID: 35015049
154. Schneeweiss S, Eddings W, Glynn RJ, Patorno E, Rassen J, Franklin JM. Variable Selection for Confounding Adjustment in High-dimensional Covariate Spaces When Analyzing Healthcare Databases. *Epidemiology*. 2017;28(2):237-248. doi:10.1097/EDE.0000000000000581. PMID: 27779497
155. Hernán MA, Wang W, Leaf DE. Target Trial Emulation. *JAMA*. 2022;328(24):2446. doi:10.1001/jama.2022.21383. PMID: 36508210
156. Hernán MA, Robins JM. Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available: Table 1.. *American Journal of Epidemiology*. 2016;183(8):758-764. doi:10.1093/aje/kwv254. PMID: 26994063
157. Matthews AA, Szummer K, Dahabreh IJ, Lindahl B, Erlinge D, Feychting M, et al. Comparing Effect Estimates in Randomized Trials and Observational Studies From the Same Population: An Application to Percutaneous Coronary Intervention. *Journal of the American Heart Association*. 2021;10(11):e020357. doi:10.1161/JAHA.120.020357. PMID: 33998290
158. Hernán MA, Alonso A, Logan R, Grodstein F, Michels KB, Willett WC, et al. Observational Studies Analyzed Like Randomized Experiments. *Epidemiology*. 2008;19(6):766-779. doi:10.1097/EDE.0b013e3181875e61. PMID: 18854702
159. Lodi S, Phillips A, Lundgren J, Logan R, Sharma S, Cole SR, et al. Effect Estimates in Randomized Trials and Observational Studies: Comparing Apples With Apples. *American Journal of Epidemiology*. 2019;188(8):1569-1577. doi:10.1093/aje/kwz100. PMID: 31063192
160. Dickerman BA, García-Albéniz X, Logan RW, Denaxas S, Hernán MA. Avoidable flaws in observational analyses: an application to statins and cancer. *Nature Medicine*. 2019;25(10):1601-1606. doi:10.1038/s41591-019-0597-x. PMID: 31591592
161. Brookhart MA, Schneeweiss S. Preference-Based Instrumental Variable Methods for the Estimation of Treatment Effects: Assessing Validity and Interpreting Results. *The International Journal of Biostatistics*. 2007;3(1). doi:10.2202/1557-4679.1072. PMID: 19655038
162. Hernán MA, Robins JM. Instruments for Causal Inference. *Epidemiology*. 2006;17(4):360-372. doi:10.1097/01.ede.0000222409.00878.37. PMID: 16755261
163. Swanson SA, Hernán MA. Commentary. *Epidemiology*. 2013;24(3):370-374. doi:10.1097/EDE.0b013e31828d0590. PMID: 23549180
164. Jackson JW, Swanson SA. Toward a Clearer Portrayal of Confounding Bias in Instrumental Variable Applications. *Epidemiology*. 2015;26(4):498-504. doi:10.1097/EDE.0000000000000287. PMID: 25978796
165. Ertefaie A, Small DS, Flory JH, Hennessy S. A tutorial on the use of instrumental variables in pharmacoepidemiology. *Pharmacoepidemiology and Drug Safety*. 2017;26(4):357-367. doi:10.1002/pds.4158. PMID: 28239929
166. Baiocchi M, Cheng J, Small DS. Instrumental variable methods for causal inference. *Statistics in Medicine*. 2014;33(13):2297-2340. doi:10.1002/sim.6128. PMID: 24599889
167. Widding-Havneraas T, Chaulagain A, Lyhmann I, Zachrisson HD, Elwert F, Markussen S, et al. Preference-based instrumental variables in health research rely on important and underreported assumptions: a systematic review. *Journal of Clinical Epidemiology*. 2021;139:269-278. doi:10.1016/j.jclinepi.2021.06.006. PMID: 34126207
168. Stukel TA, Fisher ES, Wennberg DE, Alter DA, Gottlieb DJ, Vermeulen MJ. Analysis of Observational Studies in the Presence of Treatment Selection Bias. *JAMA*. 2007;297(3):278. doi:10.1001/jama.297.3.278. PMID: 17227979
169. Thangaraj PM, Oikonomou EK, Dhingra LS, Aminorroaya A, Jayaram RH, Suchard MA, et al. Computational Phenomapping of Randomized Clinical Trial Participants to Enable Assessment of Their Real-World Representativeness and Personalized Inference. *Circulation: Cardiovascular Quality and Outcomes*. 2025;18(5). doi:10.1161/CIRCOUTCOMES.124.011306. PMID: 40261065
170. Oikonomou EK, Thangaraj PM, Bhatt DL, Ross JS, Young LH, Krumholz HM, et al. An explainable machine learning-based phenomapping strategy for adaptive predictive enrichment in randomized clinical trials. *npj Digital Medicine*. 2023;6(1):217. doi:10.1038/s41746-023-00963-z. PMID: 38001154
171. Oikonomou EK, Van Dijk D, Parise H, Suchard MA, de Lemos J, Antoniades C, et al. A phenomapping-derived tool to personalize the selection of anatomical vs. functional testing in evaluating chest pain (ASSIST). *European Heart Journal*. 2021;42(26):2536-2548. doi:10.1093/eurheartj/ehab223. PMID: 33881513
172. Munafò MR, Davey Smith G. Robust research needs many lines of evidence. *Nature*. 2018;553(7689):399-401. doi:10.1038/d41586-018-01023-3
173. Davies NM, Holmes MV, Davey Smith G. Reading Mendelian randomisation studies: a guide, glossary, and checklist for clinicians. *BMJ*. 2018;362:k601. doi:10.1136/bmj.k601. PMID: 30002074
174. Sanderson E, Glymour MM, Holmes MV, Kang H, Morrison J, Munafò MR, et al. Mendelian randomization. *Nature Reviews Methods Primers*. 2022;2(1):6. doi:10.1038/s43586-021-00092-5. PMID: 37325194
175. Ference BA, Yoo W, Alesh I, Mahajan N, Mirowska KK, Mewada A, et al. Effect of Long-Term Exposure to Lower Low-Density Lipoprotein Cholesterol Beginning Early in Life on the Risk of Coronary Heart Disease. *Journal of the American College of Cardiology*. 2012;60(25):2631-2639. doi:10.1016/j.jacc.2012.09.017. PMID: 23083789
176. Pingault JB, O’Reilly PF, Schoeler T, Ploubidis GB, Rijsdijk F, Dudbridge F. Using genetic data to strengthen causal inference in observational research. *Nature Reviews Genetics*. 2018;19(9):566-580. doi:10.1038/s41576-018-0020-3. PMID: 29872216
177. Scholkopf B, Locatello F, Bauer S, Ke NR, Kalchbrenner N, Goyal A, et al. Toward Causal Representation Learning. *Proceedings of the IEEE*. 2021;109(5):612-634. doi:10.1109/JPROC.2021.3058954
178. Roberts ME, Stewart BM, Nielsen RA. Adjusting for Confounding with Text Matching. *American Journal of Political Science*. 2020;64(4):887-903. doi:10.1111/ajps.12526
179. Keith K, Jensen D, O’Connor B. Text and Causal Inference: A Review of Using Text to Remove Confounding from Causal Estimates. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*. 2020:5332-5344. doi:10.18653/v1/2020.acl-main.474
180. Egami N, Fong CJ, Grimmer J, Roberts ME, Stewart BM. How to make causal inferences using texts. *Science Advances*. 2022;8(42):eabg2652. doi:10.1126/sciadv.abg2652. PMID: 36260669
181. Castro DC, Walker I, Glocker B. Causality matters in medical imaging. *Nature Communications*. 2020;11(1):3673. doi:10.1038/s41467-020-17478-w. PMID: 32699250
182. Feuerriegel S, Frauen D, Melnychuk V, Schweisthal J, Hess K, Curth A, et al. Causal machine learning for predicting treatment outcomes. *Nature Medicine*. 2024;30(4):958-968. doi:10.1038/s41591-024-02902-1. PMID: 38641741
183. Prosperi M, Guo Y, Sperrin M, Koopman JS, Min JS, He X, et al. Causal inference and counterfactual prediction in machine learning for actionable healthcare. *Nature Machine Intelligence*. 2020;2(7):369-375. doi:10.1038/s42256-020-0197-y
184. Liu R, Wei L, Zhang P. A deep learning framework for drug repurposing via emulating clinical trials on real-world patient data. *Nature Machine Intelligence*. 2021;3(1):68-75. doi:10.1038/s42256-020-00276-w. PMID: 35603127
185. Zang C, Zhang H, Xu J, Zhang H, Fouladvand S, Havaldar S, et al. High-throughput target trial emulation for Alzheimer’s disease drug repurposing with real-world data. *Nature Communications*. 2023;14(1):8180. doi:10.1038/s41467-023-43929-1. PMID: 38081829
186. Wornow M, Xu Y, Thapa R, Patel B, Steinberg E, Fleming S, et al. The shaky foundations of large language models and foundation models for electronic health records. *npj Digital Medicine*. 2023;6(1):135. doi:10.1038/s41746-023-00879-8. PMID: 37516790
187. Xie Y, Xu E, Bowe B, Al-Aly Z. Long-term cardiovascular outcomes of COVID-19. *Nature Medicine*. 2022;28(3):583-590. doi:10.1038/s41591-022-01689-3. PMID: 35132265
188. Wyss R, Plasek JM, Zhou L, Bessette LG, Schneeweiss S, Rassen JA, et al. Scalable Feature Engineering from Electronic Free Text Notes to Supplement Confounding Adjustment of Claims‐Based Pharmacoepidemiologic Studies. *Clinical Pharmacology & Therapeutics*. 2023;113(4):832-838. doi:10.1002/cpt.2826. PMID: 36528788
