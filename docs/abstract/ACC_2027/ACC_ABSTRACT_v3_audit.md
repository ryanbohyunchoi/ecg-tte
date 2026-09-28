**Title:** AI-ECG Embeddings Modestly Improve Covariate Balance but Not Trial-Specific Agreement in Emulations of 38 Cardiovascular Trials

**Background:** Trial emulation with real-world data is limited by unmeasured confounding. We tested whether AI-ECG embeddings capturing latent cardiac phenotypes improve confounding control.

**Methods:** Using Yale New Haven Health System records, we emulated 38 cardiovascular randomized trials (RCTs) with new-user, active-comparator designs; 20 (15 general, 5 atrial fibrillation [AF]) were analyzed under prespecified confirmation protocols. Patients were matched 1:1 on a demographic propensity score with or without an ECG foundation-model embedding, or a permuted-ECG placebo. Balance was assessed on 58 held-out clinical, laboratory and echocardiographic variables; emulated hazard ratios (HR) were compared with RCT results.

**Results:** In 33 trials, ECG embeddings increased the share of held-out covariates with standardized difference <0.1 from 53% to 59% (25/33 trials, p<0.001); the placebo did not. In the 15 confirmation trials the gain was 52% to 58% (p=0.03), but not robust to comparator clustering or a richer score. The mean absolute log-HR difference from RCTs fell from 0.26 to 0.21 (p=0.004), but not in the confirmation trials (p=0.07), and equally with shuffled RCT benchmarks (generic shrinkage). An exploratory AF signal did not replicate in 5 new AF trials (3/5 closer, p=0.19). A structured-EHR embedding matched the ECG.

**Conclusion:** AI-ECG embeddings modestly improve balance on held-out variables when structured covariates are sparse but did not improve trial-specific agreement with RCTs.
