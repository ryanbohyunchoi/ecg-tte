# Protocol v1.1 amendment (2026-09-24): audit corrections, registered before any outcome extraction

This amends `docs/PROTOCOL_V1.md` (tag `protocol-v1`). It is tagged `protocol-v1.1` before any
outcome was extracted.
- Source: the independent code and reporting audit of 2026-09-24 and Ryan's decisions on it.
- Everything not listed here is unchanged.
- Phase 1 (balance) is re-run in full under v1.1. Phase 2 runs once, after this tag.

## A. Design changes (approved by Ryan)

1. **PARADIGM-HF switcher → sequential design.**
   - The v1 switcher arm used future information: dual-eligible persons were assigned to the
     switcher role, so the comparators were "never switched later". That is an immortal-time-like
     bias toward ARNI benefit.
   - v1.1 (`paradigm_hf_seq`, design `switch_seq`) works through ARNI switchers (with ACEi/ARB in
     the prior year) in calendar order.
   - For each switcher, up to 4 established ACEi users are sampled: a repeat order at the candidate
     date, another in the prior year, no ARNI on or before the date, candidate date within ±30 days
     of the switch. Eligibility is applied per record, and one record per person (the closest date)
     is kept.
   - A person enters once. Comparators who later switch stay comparators (ITT). The sampling is
     seeded.
   - The v1 switcher cohort is kept as history and is not analysed in phase 2.
2. **Echo coverage (option A).** The echo sources (EF file and structured reports) start in 2015-07.
   - Echo-domain balance and measured-LVEF balance are scored only for patients indexed on or
     after **2016-07-31**, the first date with a full 365-day echo window.
   - "Echo performed" is masked the same way.
   - Sensitivity: every trial restricted to index on or after 2016-07-31 (re-imputed), all domains.
3. **PARTNER concomitant-surgery exclusion** window changed from [index−1, index+1] to
   [index−1, index], so no post-index information is used. The cohort changes by +1 patient; the
   analysed cohort is retained (below).

## B. Implementation corrections (bugs; no change of intent)

1. **Matching:** the greedy caliper matcher searched only ±60 sorted positions and missed valid
   matches (up to 15% of pairs in hdPS arms). It now takes the exact nearest available control
   within the caliper; a regression test checks it against brute force.
2. **Exposure-defining features:** for switch designs, the prior-class drugs (ACEi/ARB) are now
   exposure-defining features, removed from hdPS, pool B and the C-statistic (v1 kept, e.g.,
   rx_losartan in the switcher trial).
3. **SHD leakage mask:** measured LVEF (core-9) is now masked for patients in the PRESENT-SHD
   training MRNs (v1 masked echo-report domains only). The mask is applied inside the evaluator
   for the SHD population.
4. **Sparse base:** only `pci_index_30d` is excluded. v1 also dropped the prior PCI/CABG Z-code
   diagnoses (PLATO, PARTNER).
5. **PCI codes:** replaced by explicit CPT/HCPCS/ICD-PCS codes (v1 prefixes also matched
   valvuloplasty codes).
6. **Echo panel:** plausibility limits for every numeric measurement; GLS as magnitude; the
   "trivial" grade = 0.5; wall-thickness "decreased" = missing.
7. **Tie-breaks:** deterministic for same-day values (latest date, then highest value; echo:
   accession number).
   - Rebuilding every cohort with the corrected builder changed membership by 0–7 patients per
     trial (PARADIGM-HF +7, PARAGON-HF +4, ELITE II +1, DAPA-HF +6, PARTNER +1, others 0; ≤ 0.15%).
   - **The analysed v1 cohorts and embeddings are retained.** The difference is documented.
8. **Primary-set rule:** computed in the all-initiator population, as §4c specifies. The
   summariser previously applied it within the outpatient population.
9. **SHD validation:** the HCM/LVDD model is validated against its training target
   (`HCM_LVDD_IVSd15_IntermediateAsNA`).
10. **COMET benchmark orientation:** our arm order is metoprolol vs carvedilol, so the benchmark is
    HR 1/0.83 = 1.205 (CI 1.075–1.351).

## C. Reporting corrections

- **Emulation-rating item (e)** uses clinical-PS pairs in the **primary (all-initiator)**
  population. Recomputed (with the v1.1 matcher; final values in the report):
  - COMET → close;
  - ELITE II → close;
  - PARADIGM-HF → moderate.

  Item scores are now given for every trial, including the switcher, DAPA-HF and PARTNER.
- **H2 is reported for all three pre-specified domains:** LV structure, LV function and core-9. Each
  gets the one-sided Mann-Whitney p-value.
- **Stale or over-strong statements are corrected in `report.md`:**
  - labs "balanced by every PS";
  - "unchanged in the primary set";
  - "hdPS is the better tool for valves";
  - "valves are the only domain";
  - the H3 medians pool both roles.

## D. Phase-2 implementation details (specified before running)

- **Matched sets:** from the v1.1 capture grid (split seed 0 fixes the hdPS pool), all 5
  imputations.
  - Arms: M0 unadjusted, M1 sparse, M2 sparse + ECG, M3 hdPS200, M4 hdPS200 + ECG,
    R clinical reference; plus the sensitivity arms of the capture set.
  - Model: Cox with robust SE clustered on pair, pooled by Rubin's rules.
  - Secondary: overlap-weighted Cox.
- **Outcomes** (`trial_specs.OUTCOMES`, `extract_outcomes.py`):
  - Hospitalisation events are inpatient stays that **start after index**, with a qualifying code
    recorded during the stay. Events during the index admission (e.g. periprocedural stroke in
    PARTNER, in-hospital reinfarction in PLATO) are therefore not captured. This is a limitation.
  - CV death: any listed cause I00–I99, or no cause record. Sensitivity: no cause record = non-CV.
  - Other-cause death censors (cause-specific hazard).
  - Administrative end: 2024-06-24 for composites with CV/CHD death, 2024-12-31 otherwise.
  - Follow-up is extracted to max(trial horizon, 60 months) and truncated for each horizon.
- **Phase-2 trial set:** the primary analysis set (≥ 400 clinical-PS pairs, all initiators, v1.1
  matcher), minus DIONYSOS (not emulable) and minus the v1 switcher (replaced by the sequential
  design). The others are reported in the supplement.
- **Agreement metrics** (per protocol §8):
  - versus the RCT: estimate agreement, regulatory agreement, standardised difference, and
    |log HR difference|;
  - versus the full-data reference R: log-HR difference;
  - across trials: paired Wilcoxon of M2 vs M1 and M4 vs M3.
