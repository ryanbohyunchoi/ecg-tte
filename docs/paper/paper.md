# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

*Working draft; last updated 2026-09-28. Sections are added in order. Draft notes are marked and must be removed before submission.*

## Abstract

*(to be written last)*

## Introduction

Randomization is the foundation of causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation is a leading candidate approach.^3^ The protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational data. Confounding is typically addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ Its guarantee extends only to what is measured, however. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) contain richer clinical information, but laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ By analogy, polygenic scores were recently shown to serve as an orthogonal readout of residual confounding in trial emulations, even though they could not remove it.^11^ AI-ECG may play a similar and more direct role, because it measures current physiology and is available for most patients.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, (iii) bias removal in simulations with a known treatment effect, and (iv) utility for trial enrichment.

## Methods

*(next)*

## Results

*(pending)*

## Discussion

*(pending)*

## References

*(see draft notes; to be formatted)*

---

### Draft notes: Introduction (remove before submission)
- **v2 (2026-09-28), restructured per PI outline:**
  - randomization and why it works, then RCT limits;
  - unmet need for causal inference from routine data;
  - TTE with a PS on structured variables: strengths and successes, then limits;
  - EHR missingness vs claims;
  - CV physiology, the ECG and AI-ECG;
  - the German PGS analogy;
  - "Here, we".
- **v2 reference mapping:**
  1. Randomization and causal inference, e.g. Hernán & Robins, *Causal Inference: What If*, or Rubin 1974 [?]
  2. RCT limitations / representativeness, e.g. Sherman RE et al. NEJM 2016; Bothwell LE et al. NEJM 2016 [?]
  3. Hernán MA, Robins JM. Am J Epidemiol 2016 [?]
  4. Franklin JM et al. Circulation 2021 [V]
  5. Wang SV et al. JAMA 2023 [V]
  6. EHR missingness / informative observation, e.g. Haneuse S et al. or Goldstein BA et al.; the Khera-lab LEGEND papers use "measured-or-not" labs [?]
  7. Attia ZI et al. Nat Med 2019 [?]
  8. Dhingra LS et al. PRESENT-SHD, JACC 2025 [V]
  9. Dhingra LS et al. Eur Heart J 2025, or Croon PM et al. Circulation 2025 [V]
  10. BCL ECG foundation model [?]
  11. German J et al. Nat Genet 2025 [V]
  - Consider also citing DISCO (Biswas … Khera, EHJ 2025 suppl) in paragraph 3 or the Discussion.
- The earlier v1 notes below refer to the v1 numbering.
- **Tone.** Paragraph 5 deliberately does not preview results. We could add a German-style closing sentence: "We find that AI-ECG embeddings track design quality and improve balance on unmeasured physiology, remove confounding bias in proportion to how well they encode the confounder, and inform trial enrichment, but do not by themselves reproduce trial-specific RCT results." It is accurate per v1.6–v1.9 and the round-4 audit.
- **Claims to keep consistent with results.**
  - The "single heart failure emulation" (DISCO) is an abstract only.
  - We say "whether," not "that," for the RCT agreement question.
- **Citations: all must be verified against the source before submission** ([V] = verified in this project's literature notes; [?] = to locate).
  1. Bothwell LE et al., or Sherman RE et al. NEJM 2016 on RCT limits / real-world evidence [?]
  2. Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial is not available. Am J Epidemiol 2016 [?]
  3. Franklin JM, Patorno E, Desai RJ, et al. Circulation 2021;143:1002 (RCT-DUPLICATE, PMID 33327727) [V]
  4. Wang SV, Schneeweiss S, et al. JAMA 2023;329:1376 (PMID 37097356) [V]
  5. Heyard R, et al. BMJ Medicine 2024 (design differences and agreement) [V, in docs/v14]
  6. Schneeweiss S, et al. Epidemiology 2009 (hdPS, PMID 19487948) [V]
  7. Steinberg E, et al. J Biomed Inform 2021 (CLMBR) [?]
  8. German J, Yang Z, Urbut S, ... Ganna A. Nat Genet 2025, doi:10.1038/s41588-025-02229-8 [V]
  9. Attia ZI, et al. Nat Med 2019 (AI-ECG low EF) [?]
  10. Dhingra LS, et al. PRESENT-SHD. J Am Coll Cardiol 2025 (PMID 40139886) [V]
  11. Dhingra LS, et al. Eur Heart J 2025 (PMID 39804243) [V]
  12. Croon PM, et al. Circulation 2025 (PMID 40888124) [V]
  13. BCL ECG foundation-model reference: add the model paper/preprint (see docs/ECG_MODEL.md) [?]
  14. Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. DISCO. Eur Heart J 2025;46(Suppl 1):ehaf784.4614 [V]
