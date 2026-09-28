**Title:** AI-Enhanced Electrocardiography Improves Confounding Control in Emulations of 38 Cardiovascular Trials

**Background:** Trial emulation with real-world data is limited by unmeasured confounding. Propensity scores (PS) use prespecified structured variables that may miss latent features found in unstructured data. We hypothesized that AI-ECG embeddings capture unstructured cardiac phenotypes that improve confounding control.

**Methods:** Using Yale New Haven Health System records, we emulated 38 cardiovascular randomized trials (RCTs) with new-user, active-comparator designs. Patients were matched 1:1 on a demographic PS with or without an ECG foundation-model embedding, or a permuted-ECG placebo. Balance was assessed across 58 held-out clinical, laboratory and echocardiographic variables, and emulated hazard ratios (HR) were compared with RCT results. Simulations with known effects quantified bias removal.

**Results:** ECG embeddings increased the share of held-out covariates with standardized difference <0.1 from 51% to 57% (28 of 38 trials, p<0.001), robust to trial clustering; placebo had no effect. The mean absolute log-HR difference from RCTs fell from 0.26 to 0.21 (25 of 38 trials, p=0.002), largely by attenuating exaggerated estimates. In simulations, ECG embeddings removed bias from hidden confounders in proportion to how well they encoded them (up to 21% for NT-proBNP), while placebo removed none.

**Conclusion:** AI-ECG embeddings capture latent cardiac physiology missing from sparse structured data, improving covariate balance and partially reducing unmeasured confounding in trial emulations.
