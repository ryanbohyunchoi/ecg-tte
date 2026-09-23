# Corrected CLMBR selection comparison: v2

User approved this correction after reviewing v1. V1 matched majority-arm
carvedilol patients in fixed order until all metoprolol patients were consumed.
The retained sets were therefore independent of embedding distances; their
marginal SMDs could not evaluate embedding-based selection. Preserve v1 and its
results; do not describe this correction as prespecified before seeing v1.

## Explicit contract

`--metoprolol-anchor` selects `comet_cosine_comparison_v2_metoprolol_anchor`.
Without that flag, the historical v1 behavior remains available.

- Start with all metoprolol patients, in SHA256(`comet_cosine_v1|patient_key`)
  order, lexical patient key breaking hash ties. The prefix is unchanged.
- For each, select the nearest unused carvedilol patient by cosine distance on
  L2-normalized frozen vectors. Lexical carvedilol key breaks exact distance ties.
- 1:1, without replacement, no distance cutoff. Stop if metoprolol outnumbers
  carvedilol; do not silently reverse the anchor population.
- Preserve output labels: carvedilol_key remains carvedilol, metoprolol_key remains
  metoprolol. SMD direction remains carvedilol minus metoprolol.
- This should retain 2,960 per arm from the common 7,498, with carvedilol selection
  now depending on embeddings. It does not guarantee improved clinical balance.
- Original PSM remains primary and previously refined PSM secondary. Their
  formulas/calipers/orders remain unchanged. Saved MICE, common cohort, evaluation
  variables and pre-match denominators remain unchanged. No new inference.
- PSM and cosine still differ in support/order/retention; this is a method-bundle
  comparison. Retaining all metoprolol patients changes the represented population
  relative to caliper PSM. No common causal estimand or effects readiness is implied.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
bash scripts/run_comet_cosine_v2_h100.sh
```

The launcher uses the existing mosaic Python and isolated MICE R environment,
limits numerical library threads, and creates fresh outputs and temporary files
under `/mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-comparison-v2-*`.
It reads the existing full embeddings `comet-clmbr-full-NAyb4G2x/report` and
saved imputations `comet-mice-pilot-v2-w5ZRCHzh/report`. No home outputs or source
modifications. It prints the report directory and summary.

Inspect the summary for version, retention, distance quantiles and per-imputation
balance. `comparison_love_plots.pdf`, `comparison_balance.csv`, and
`comparison_observed_balance.csv` use the same reporting contract as v1.
Raw pairs, patient records and logs stay on H100. Computational completion is not
approval of imputation convergence, clinical source semantics, or causal effects.
