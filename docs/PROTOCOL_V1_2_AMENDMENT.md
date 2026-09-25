# Protocol v1.2 amendment (2026-09-24): phase-2 outcome-code review, registered before outcome extraction

Source: the independent pre-run review of `extract_outcomes.py`, `run_phase2.py` and
`summarize_phase2.py` against v1/v1.1. The review used synthetic data only; no outcome had been
extracted. Tag `protocol-v1.2`.

1. **Index-day deaths:**
   - For outcomes that include death, a death on the index day is an event at t = 0.5 days; for
     other outcomes it censors at t = 0.5.
   - A death recorded *before* index (data error) excludes the patient from phase 2.
   - Patients indexed on or after the administrative end are excluded.
   - Excluded counts are reported (suppressed if < 11).
2. **Recurrent MI:** within 28 days of index only I22 (subsequent MI) counts, because ICD-10-CM
   codes I21 on every encounter for 4 weeks after an MI. After day 28, I21 or I22 counts.
3. **Index-stay events:**
   - Inpatient visits (9201) are merged into stays: overlapping or contiguous, gap ≤ 1 day.
   - An event must occur in a stay that starts after the end of the stay containing the index date.
   - This removes index-admission events split across records.
4. **Hospitalisation after an other-cause death** is never counted.
5. **Stroke codes harmonised:**
   - stroke = I60, I61, I63 (and legacy I64); subdural I62 excluded;
   - systemic embolism = I74 (AF trials).
6. **Negative control:** femoral hernia repair CPT 49550–49557 added (the label already said
   "inguinal or femoral").
7. **Benchmark standard errors** use each trial's CI level (ELITE II: 95.7%).
8. **One benchmark per RCT** in cross-trial summaries: PARADIGM-HF is represented by the sequential
   switcher design, the design closest to the trial population, which was already on ACEi/ARB. The
   new-user design is a sensitivity analysis.
9. **Stratification:** cross-trial agreement is reported stratified by role (physiology/control) and
   emulation rating (close vs moderate/limited). Item scores for (a)–(d) are in
   `trial_specs.RATING_ITEMS`; (e) comes from the v1.1 all-initiator grid.
10. **Regulatory agreement** keeps the protocol definition: both significant in the same direction,
    or both non-significant. It is applied uniformly to superiority and non-inferiority trials.
    This differs from RCT-DUPLICATE's non-inferiority-specific judgement and is stated as such.
11. **Disclosure and robustness:**
    - Event counts are suppressed when any imputation's count is 1–10.
    - Phase 2 asserts that no matched patient lacks an outcome record, other than flagged
      exclusions.
    - The horizon is checked against the spec.
    - CIs are Wald 95% (normal approximation) on the Rubin-pooled SE.
12. **Known limitations, stated rather than changed:**
    - Conditions are linked to stays by date only; gold has no visit link.
    - ALLHAT "CHD death" uses any listed I20–I25 cause.
    - The CT-Vitals causes are listed causes, without an underlying-cause flag.
