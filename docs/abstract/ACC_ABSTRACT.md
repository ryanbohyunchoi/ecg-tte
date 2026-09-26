**Background:** Trial emulation with real-world data is limited by unmeasured confounding, because propensity scores (PS) use prespecified structured variables. AI-ECG embeddings capture high-dimensional cardiac phenotypes that may proxy unmeasured physiology.

**Methods:** Using electronic health records (2013–2024), we emulated 18 cardiovascular RCTs with new-user, active-comparator designs under a prespecified protocol.
- **Matching:** 1:1 PS matching on demographics and diagnoses (sparse PS) or a high-dimensional PS (hdPS), each with or without a self-supervised 12-lead ECG embedding.
- **Outcomes:**
  - balance on echocardiographic physiology not included in any PS;
  - agreement with RCT hazard ratios (HR);
  - plasmode simulation bias.

**Results:**
- **Balance:** in physiology-driven trials, adding ECG raised the share of left ventricular structural imbalance removed from 55% to 81% (sparse PS) and from 79% to 93% (hdPS).
- **Agreement with RCTs:** ECG moved sparse-PS estimates closer to the RCT HR in 14 of 18 trials. Mean absolute log-HR error fell from 0.18 to 0.16, standardized-difference agreement rose from 61% to 78%, and excess disagreement fell from 4.7 to 3.4 (p=0.02).
- **Simulation:** ECG alone removed 20% of confounding bias, vs 13% for demographics, and the gains grew with sparser coded data.
- ECG added nothing to hdPS.

**Conclusion:** AI-ECG embeddings capture confounding physiology absent from structured data. They improve balance and RCT concordance for sparse PS, especially when coded data are limited.
