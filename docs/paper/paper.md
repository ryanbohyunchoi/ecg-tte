# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

*Working draft; last updated 2026-09-28. Sections are added in order. Draft notes are marked and must be removed before submission.*

## Abstract

*(to be written last)*

## Introduction


Randomized controlled trials (RCTs) remain the reference standard for estimating treatment effects, but they are costly and slow. They also often exclude the older, multimorbid patients who receive these therapies in practice.^1^ Target trial emulation offers a principled framework for estimating the same effects from routinely collected data.^2^ In this framework, the protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational data. Systematic efforts to benchmark emulations against completed RCTs, most prominently RCT-DUPLICATE, have shown that agreement is achievable. These efforts also show that agreement depends heavily on how closely the design can be emulated and on how well the available data capture the determinants of treatment choice.^3–5^ When those determinants are not recorded, residual confounding persists regardless of design rigour.

In cardiovascular medicine, many of the strongest determinants of both prescribing and prognosis are physiological rather than administrative. Examples include left ventricular systolic and diastolic function, chamber size, atrial substrate, congestion and conduction disease. Clinicians choose between therapies on the basis of these features, and the same features predict outcomes, so they are classic sources of confounding by indication. They are also largely absent from the structured data on which most emulations rely. Claims and structured electronic health record (EHR) data record diagnoses, procedures and prescriptions well, but echocardiographic measurements and natriuretic peptides are available for only a subset of patients and are rarely captured in a form usable for adjustment. High-dimensional propensity score (PS) methods and EHR foundation models can recover some of this information indirectly from coding patterns.^6,7^ Neither, however, measures the physiology itself.

A recent study introduced a complementary strategy: integrating an orthogonal biological data layer into trial emulation. German and colleagues emulated four cardiometabolic trials in FinnGen and examined polygenic scores (PGS) across successive design steps.^8^ They showed that PGS imbalance between arms shrank as the design improved, from crude comparison to eligibility criteria to PS matching. This provided an independent readout of confounding that the design itself did not target. Two further findings were instructive. First, simulations showed that PGS cannot by themselves adjust away unmeasured confounding, because they are weak and pleiotropic proxies of the traits they index. Second, the emulation framework could be used to evaluate PGS for prognostic enrichment of future trials. The study thus reframed a biological data type not as a remedy for confounding but as a tool for diagnosing it and for informing trial design. Germline genetics, however, captures lifelong liability rather than current physiological state. Genetic data are also available for only a small minority of patients in routine care.

The 12-lead electrocardiogram (ECG) may be better suited to this role in cardiovascular emulations. The ECG is inexpensive and is acquired routinely across care settings, so it is often available for most patients in an emulated cohort around the time of treatment initiation. It records the heart's current electrical and, indirectly, structural state. Deep learning applied to the ECG (AI-ECG) detects left ventricular systolic dysfunction, structural heart disease and other latent phenotypes with high accuracy.^9–12^ Self-supervised ECG foundation models compress this information into general-purpose embeddings that are not tied to any single diagnostic label.^13^ In a single heart failure emulation, matching on AI-ECG embeddings recovered the direction of the RCT effect where adjustment for a few clinical covariates did not.^14^ It remains unknown whether this generalizes across therapeutic areas. It is also unknown whether AI-ECG information improves balance on physiology that is not otherwise measured, whether it reduces bias or merely shifts estimates, and how it compares with embeddings derived from the structured record itself.

Here we evaluated AI-ECG embeddings as a source of information on unmeasured confounding in 38 emulations of cardiovascular RCTs in a large US health system. The emulations spanned atrial fibrillation, heart failure, hypertension, coronary disease and diabetes. Following the logic of German et al., we asked four questions:
1. whether ECG-derived phenotypes track confounding across design steps;
2. whether adding ECG embeddings to a PS improves balance on 58 clinical, laboratory and echocardiographic characteristics that no PS included, beyond a permuted-ECG placebo;
3. whether this translates into closer agreement with RCT results and into reduced bias in simulations with a known treatment effect;
4. whether AI-ECG can inform trial design through prognostic enrichment.

To guard against selective reporting:
- we prespecified confirmation analyses in 15 trials and, separately, in 5 atrial fibrillation trials whose results had not been examined;
- a blinded rater classified emulation fidelity;
- all analyses were compared with an EHR foundation-model embedding and audited independently.

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
