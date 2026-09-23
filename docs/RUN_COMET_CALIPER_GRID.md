# CLMBR cosine caliper sensitivity: explicit v4

User requested cosine calipers and selected the grid **0.20, 0.30, 0.40** after
reviewing no-caliper balance. These are exploratory thresholds, not validated
clinical cutoffs or equivalents of the PSM caliper. They correspond to minimum
cosine similarities 0.80, 0.70, 0.60. Publish/report all three, including failures,
and retain prior no-caliper results. Do not select the threshold that produces
the best balance and present it as independently evaluated.

## Matching and evaluation contract

`--global-optimal --cosine-caliper VALUE` selects
`comet_cosine_comparison_v4_caliper`. A caliper is inclusive: only distance <=
VALUE edges are allowed. Uses the same frozen vectors, L2 normalization, lexical
matrix axes, no replacement and 1:1 matching. Both arms may now lose patients.

First maximize the number of feasible pairs, then minimize their total cosine
distance. This is NOT deleting long pairs from a no-caliper assignment: alternatives
are considered jointly. Implementation augments the cost matrix with one unmatched
dummy column per metoprolol patient and penalty P=2*n_metoprolol+1 per dummy.
Cosine distances lie in [0,2], so P exceeds any possible total real-cost difference;
therefore fewer unmatched patients always wins before optimizing real distance.
Forbidden edges have infinite cost, and dummy edges always allow an assignment.
No heuristic threshold on clinical covariates is used.

Diagnostics include feasible edge count, patients with no eligible partner,
matched count, unmatched counts in both arms, distance total, and retention.
Unmatched counts may exceed no-eligible-partner counts because patients compete
for the same partners. Fewer than two pairs produces a structured failure with
matching diagnostics; balance is not manufactured for an empty/tiny matched set.

The full common pre-match cohort and SMD denominators remain fixed at the same
7,498 source patients; we do not redefine the denominator after caliper exclusions.
Original/refined PSM are unchanged, with their own 0.2 pooled within-arm SD(logit)
calipers. Original observations, five saved MICE datasets, model checkpoint and
feature set are unchanged. No new inference or imputation. Saved plots show each
cutoff against the same clinical comparators. Causal estimands/outcomes and trace
review are not approved by this diagnostic exercise.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
bash scripts/run_comet_caliper_grid_h100.sh
```

The launcher checks the SciPy runtime with the previously successful environment
C++ preload. It runs the three cutoffs sequentially into fresh RAID directories,
continues to the next cutoff if one fails, and prints the combined
`grid_summary.json`. All outputs and temporary files are under
`/mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-caliper-grid-*`.
No source data or older reports are overwritten. Patient-level pairs/logs remain
restricted on H100. Share only reviewed aggregate summaries.

Each `caliper-0.XX/report/` includes feature-level completed and observed-only
balance tables plus `comparison_love_plots.pdf`. A Cursor socket/IPC connection
error concerns the remote editor session, not generation of these PDF files.
Open them through a functioning remote editor file explorer after reconnecting.
