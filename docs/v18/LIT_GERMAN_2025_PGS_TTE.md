# German et al., Nat Genet 2025: "Incorporating genetic data improves target trial emulations and informs the use of polygenic scores in RCT design"

**Citation.** German J, Yang Z, Urbut S, Vartiainen P, FinnGen, Natarajan P, Patorno E, Kutalik Z, Philippakis A, Ganna A. *Nat Genet* 2025. doi:10.1038/s41588-025-02229-8. PMC12283355. Code: github.com/dsgelab/trial_emulations_genetics.

## What they did
They emulated 4 RCTs in FinnGen (n = 425,483): EMPA-REG, TECOS, ARISTOTLE and ROCKET. All 4 were within the RCT CIs.

**Fig 2: PGS as an orthogonal balance diagnostic.** SMDs of 20 PGS were compared at 3 sequential design steps: plain observational, then eligibility + active comparator, then PS-matched. PGS imbalance shrank at each step. For example, in EMPA-REG the T2D PGS SMD went 0.56 → 0.08 → n.s.

**Fig 3: simulation.** PGS cannot adjust for unmeasured confounding: even at r² = 0.5 with the confounder, substantial bias remains. Matching on PGS alone left phenotypes unbalanced.

**Fig 4: Mendelian randomization for confounder detection.** Traits with genetic effects on both treatment and outcome were flagged as likely confounders. 12 were flagged before design and 2 (HbA1c, CRP) after the eligibility step.

**Fig 5: enrichment.** They tested the PGS–outcome association in the trial-eligible population against the general population. The two agreed for DM and differed for AF. Top-quartile PGS enrichment reduced the required sample size by 8.6–26%. There was no predictive (treatment × PGS) interaction.

## Framing lessons for our paper
- **They embraced a negative finding.** "PGS cannot adjust for unmeasured confounding" is a headline result. The positive claims are (a) the diagnostic value of the covariate, (b) confounder detection, and (c) trial design (enrichment). This parallels our result: ECG improves balance, but trial-specific bias reduction is not shown except in AF.
- **The title says "improves target trial emulations"** because the data improve the design and diagnostics of emulations, not because they fix bias.
- **Their stated limitations match ours:** sample loss with matching, the proxy being weak compared with measured phenotypes, and population-specific prognostic performance.

## Analyses we could emulate with the ECG (and CLMBR)
1. **ECG imbalance across design steps (their Fig 2).** Measure the SMDs of AI-ECG phenotypes (ECG-predicted LVEF, LVH, AF, age), or the ECG-embedding treatment C-statistic, at three steps:
   - all initiators vs non-initiators / crude;
   - after eligibility + active comparator;
   - after sparse / hdPS / clinical PS matching.

   If ECG imbalance tracks design quality, the ECG is an orthogonal diagnostic of residual confounding that is available when labs and echo are not.
2. **Simulation with a known truth (their Fig 3).** Measure how much confounding by a held-out physiological variable (e.g. echo LVEF) is removed by adjusting for the ECG embedding, as a function of the ECG's R² for that variable. Real R² values come from our data.
3. **Confounder detection (the analogue of MR).** Using ECG-predicted phenotypes, test which latent cardiac traits predict both treatment and outcome after each design step. This flags residual confounders.
4. **ECG-based enrichment for RCT design (their Fig 5).** This would be a new result with clinical appeal.
   - **Prognostic enrichment:** compare the AI-ECG risk score's association with the trial outcome in emulated trial populations against the general population, and estimate the sample-size reduction from enriching the top AI-ECG risk quartile.
   - **Predictive enrichment:** test treatment × AI-ECG phenotype interactions (e.g. rhythm control or DOAC choice in AF by AI-ECG phenotype; ARNI by AI-ECG LVEF). This parallels the heterogeneity finding in DISCO.
5. **Optional: UKB PGS.** PGS are available for UKB, so a PGS vs ECG comparison as orthogonal diagnostics would be possible in the UKB emulations. It is limited by the weak UKB emulations.
