# Reference notes for the restart

Checked 2026-09-09. These are focused primary-source checks supporting the plan,
not a completed systematic review. Method/model recommendations in the plan are
proposals; their suitability for this dataset remains to be established.

## RCT-DUPLICATE

[Wang, Schneeweiss, and the RCT-DUPLICATE Initiative. JAMA 2023;329:1376–1385.](https://jamanetwork.com/journals/jama/fullarticle/2804067)

The project used selected trial emulations with prespecified protocols and
propensity-score matching. Its agreement definitions distinguish statistical
significance agreement, point-estimate inclusion in the RCT confidence interval,
and standardized effect differences. It also emphasizes emulation-design
differences as a limitation when interpreting disagreement.

The main article was accessible. The direct supplement retrieval returned an
error during this review. Supplement-specific formulas, noninferiority rules,
individual emulation protocols, and their code lists still require verification.
The legacy implementation's generic benefit/harm/null and CI-overlap summaries
must not be assumed to reproduce the original agreement metrics exactly.

Primary project index for follow-up:
[RCT-DUPLICATE publications](https://www.rct-duplicate.org/publications.html).

## Time-zero design

[Hernán et al. Specifying a target trial prevents immortal time bias and other self-inflicted injuries in observational analyses.](https://pubmed.ncbi.nlm.nih.gov/27237061/)

This framework motivates the explicit synchronization of eligibility, treatment
assignment, and follow-up. Our proposed baseline-only feature rules and separate
handling of adherence strategies operationalize that principle for this rebuild.

## Structured EHR representations

[StanfordShahLab CLMBR-T-Base model card](https://huggingface.co/StanfordShahLab/clmbr-t-base).

The card describes structured medical-event inputs mapped to standard OMOP
vocabulary concepts, with MEDS-formatted patient inputs. It also documents its
training source and model access conditions. Check the installed checkpoint,
runtime, vocabulary, and access status before implementation; do not assume
the new JDAT codes are directly consumable.

[FEMR source repository](https://github.com/som-shahlab/femr).
The adapter/runtime version is an implementation decision, not yet selected.

## Note embeddings

[Official Qwen3-Embedding implementation](https://github.com/QwenLM/Qwen3-Embedding),
[technical report](https://arxiv.org/abs/2506.05176).

These document candidate text encoders. They do not establish benefit for causal
adjustment using JDAT notes. Keep exact model revision, tokenization, instructions,
truncation, and pooling in the representation contract.

## Matching uncertainty

[Austin and Small. The use of bootstrapping when using propensity-score matching without replacement: a simulation study.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4260115/)

Variance behavior depends on matching details. The plan therefore requires
estimator-specific simulation and avoids assuming that an ordinary patient
bootstrap is valid for every proposed nearest-neighbor estimator.

## Literature and protocol work still required

- Retrieve the JAMA supplement and candidate-trial original protocols/reports.
- Review representation learning specifically for confounding adjustment, distinct
  from risk prediction/retrieval; do not infer causal validity from prediction AUC.
- Choose survival estimands and variance methods for the exact matched/weighted designs.
- Review multiple-imputation compatibility with those estimators and any model selection.
- Review multimodal availability/selection and patient/trial-family dependence.
- Audit the actual ECG/echo encoder papers, model cards, objectives, checkpoints,
  and training populations once asset availability is known.

Maintain an evidence table with claim, primary source, applicable assumptions,
proposed implementation, and validation requirement as these reviews proceed.
