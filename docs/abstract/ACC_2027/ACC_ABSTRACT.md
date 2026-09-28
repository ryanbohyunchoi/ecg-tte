**Title:** AI-Enhanced Electrocardiography Improves Confounding Control in Emulations of 33 Cardiovascular Trials

**Background:** Trial emulation with real-world data is limited by unmeasured confounding. Propensity scores (PS) use prespecified structured variables that may miss latent features found in unstructured data. We hypothesized that AI-ECG embeddings capture latent cardiac phenotypes that improve confounding control.

**Methods:** Using Yale New Haven Health System electronic health records, we emulated 33 cardiovascular randomized trials (RCTs) with new-user, active-comparator designs. Fifteen trials were analyzed under a prespecified confirmation protocol. Patients were matched 1:1 on a demographic PS with or without an ECG foundation-model embedding, or a permuted-ECG placebo. Balance was assessed across 58 held-out clinical, laboratory and echocardiographic variables, and emulated hazard ratios (HR) were compared with RCT results.

**Results:** ECG embeddings increased the share of held-out covariates with standardized difference <0.1 from 53% to 59% (improved in 25 of 33 trials, p<0.001). This replicated in the 15 prespecified trials (52% to 58%, p=0.03), and the placebo had no effect. The mean absolute log-HR difference from RCTs fell from 0.26 to 0.21 (p=0.004). Gains were largest in atrial fibrillation trials, where all 7 emulations moved closer to the RCT (0.44 to 0.32) and RCT-consistent estimates rose from 2 to 5.

**Conclusion:** AI-ECG embeddings capture confounding information absent from structured data, improving covariate balance and agreement with RCTs, particularly in atrial fibrillation.
