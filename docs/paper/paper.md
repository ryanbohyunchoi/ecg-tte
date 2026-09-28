# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

*Working draft; last updated 2026-09-28. Sections are added in order. Draft notes are marked and must be removed before submission.*

## Abstract

*(to be written last)*

## Introduction

Randomization is the foundation of causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation is a leading candidate approach.^3^ The protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational data. Confounding is typically addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ Its guarantee extends only to what is measured, however. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) contain richer clinical information, but laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ Because the ECG measures current physiology and is available for most patients, AI-ECG may capture confounding that structured data miss.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, (iii) bias removal in simulations with a known treatment effect, and (iv) utility for trial enrichment.

## Methods

*(next)*

## Results

*(pending)*

## Discussion

*(pending)*

## References

1. Hernán MA, Robins JM. *Causal Inference: What If.* Boca Raton: Chapman & Hall/CRC; 2020.
2. Sherman RE, Anderson SA, Dal Pan GJ, et al. Real-world evidence — what is it and what can it tell us? *N Engl J Med.* 2016;375:2293–2297.
3. Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial is not available. *Am J Epidemiol.* 2016;183:758–764.
4. Franklin JM, Patorno E, Desai RJ, et al. Emulating randomized clinical trials with nonrandomized real-world evidence studies: first results from the RCT DUPLICATE initiative. *Circulation.* 2021;143:1002–1013.
5. Wang SV, Schneeweiss S; RCT-DUPLICATE Initiative. Emulation of randomized clinical trials with nonrandomized database analyses: results of 32 clinical trials. *JAMA.* 2023;329:1376–1385.
6. Haneuse S, Arterburn D, Daniels MJ. Assessing missing data assumptions in EHR-based studies: a complex and underappreciated task. *JAMA Netw Open.* 2021;4:e210184.
7. Attia ZI, Kapa S, Lopez-Jimenez F, et al. Screening for cardiac contractile dysfunction using an artificial intelligence–enabled electrocardiogram. *Nat Med.* 2019;25:70–74.
8. Dhingra LS, Aminorroaya A, Sangha V, et al. Ensemble deep learning algorithm for structural heart disease screening using electrocardiographic images: PRESENT SHD. *J Am Coll Cardiol.* 2025;85:1302–1313.
9. Dhingra LS, et al. Heart failure risk stratification using artificial intelligence applied to electrocardiogram images: a multinational study. *Eur Heart J.* 2025;46:1044–1053.
10. Sangha V, Khunte A, Holste G, Mortazavi BJ, Wang Z, Oikonomou EK, Khera R. Biometric contrastive learning for data-efficient deep learning from electrocardiographic images. *J Am Med Inform Assoc.* 2024;31(4):855.

---

### Draft notes (remove before submission)
- **Introduction v3 (2026-09-28):**
  - It follows the PI outline: randomization, then RCT limits, then the unmet need, then TTE with a PS on structured data (strengths and limits), then EHR missingness vs claims, then CV physiology and AI-ECG, then "Here, we".
  - References 1–10 are checked against PubMed/publisher pages. Still to confirm: the ref 9 full author list and the ref 10 page range.
- **Optional closing sentence for the Introduction**, consistent with the v1.6–v1.9 results and the round-4 audit: "We find that AI-ECG embeddings improve balance on unmeasured physiology and remove confounding bias in proportion to how well they encode the confounder, but do not by themselves reproduce trial-specific RCT results."
- **Possible additional citation:** DISCO (Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. *Eur Heart J* 2025;46(Suppl 1):ehaf784.4614), the closest precedent. Cite it in the Introduction or the Discussion.
