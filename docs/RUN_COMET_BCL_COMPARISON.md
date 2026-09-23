# BCL versus clinical PSM on the ECG-available cohort

H100 full report comet-bcl-full-lMQtaSyg produced6,103 finite nonzero256D vectors,
zero load errors,660.588seconds. These are user-reported technical results.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
bash scripts/run_comet_bcl_comparison_h100.sh
```

No GPU or re-encoding needed. Uses mosaic Python and the existing isolated R
runtime. Output is fresh under RAID. The linkage adapter checks full output again,
verifies input and selection digests, maps relative fileIDs to patient keys,
checks arm/index against the unchanged baseline and strictly pre-index1–365days.
It records current vector hashes; full-run v1 did not persist vector-content hashes,
so byte identity to the original run cannot be retrospectively proved.

Explicit BCL comparison input contract:256D backbone before projection head,
checkpoint hash traced to successful full run. Not a CLMBR checkpoint or format
claim. Original/default CLMBR input contract remains unchanged. Both use shared
outcome-blind matching/evaluation code. BCL populations are not directly comparable
to earlier7,498-person CLMBR results; any direct BCL/CLMBR comparison requires an
additional verified common-population run.

All three methods start with the same BCL-available patients (expected C3,561,
T2,542). Original clinical PSM is primary; previously refined PSM is disclosed
secondary. Saved five MICE datasets are subset without refitting. Evaluation
includes original missingness and observed-only balance with fixed common-cohort
pre-match denominators. Baseline order/identity and baseline hash are checked.

BCL matching uses L2-normalized cosine distance and global optimal1:1 assignment
without replacement or a cosine caliper, matching all2,542 metoprolol patients
with a jointly selected carvedilol subset if linkage confirms those counts.
Clinical PSM retains its0.2 pooled within-arm logit-SD caliper and original/refined
formulas. Differences in retention/support are reported, not presented as an
isolated metric comparison. No feature selection, outcome tuning, or fine-tuning.
Caliper sensitivities can be separate explicitly reported analyses, not chosen
for favorable balance. No causal effects computed by this run.

Outputs include summary.json, comparison_balance.csv,
comparison_observed_balance.csv, per-method balance/retention files and
comparison_love_plots.pdf. Raw pair/score data and engine logs stay on H100.
The PDF uses generic cosine labeling; its representation is identified by this
run's contract.json. Review clinical and missingness balance and retention together.
