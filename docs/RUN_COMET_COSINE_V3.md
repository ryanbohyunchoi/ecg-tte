# Global optimal cosine matching: explicit v3

User approved after reviewing greedy v2. `--global-optimal` selects
`comet_cosine_comparison_v3_global_optimal`; v1/v2 remain available and their
saved outputs are preserved. All existing source, MICE and PSM rules are unchanged.

Minimize the sum of cosine distances across all 2,960 metoprolol patients and
2,960 distinct selected carvedilol patients. Use float64 L2-normalized vectors
and distance 1 minus dot product, clipped to numerical cosine bounds. The
rectangular assignment has all metoprolol patients as rows and all carvedilol
patients as columns. Stop if the metoprolol arm exceeds the carvedilol pool.
Pair labels and SMD direction remain carvedilol versus metoprolol.

Use SciPy's `linear_sum_assignment`, not a sequence of greedy decisions. Both
matrix axes have lexical patient-key order; no random ordering or epsilon cost
perturbation. The solver chooses among equal-cost optima. Its version is recorded;
identical tie resolution across SciPy versions is not promised. See the
[official solver documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html).

There is **no cosine caliper**. Original and refined PSM retain their existing
caliper: 0.2 times pooled within-arm pre-match SD of propensity-score logits.
That is not 0.2 propensity probability and is not transferable to cosine units.
No empirically justified cosine cutoff has been frozen. This run isolates global
versus greedy assignment without changing retention. A later caliper sensitivity
would need an explicit threshold-selection rationale and partial-matching policy;
no threshold may be selected to force these clinical balance results to improve.

The run recomputes greedy v2 pairs as a distance reference and requires global
cost <= greedy cost within numerical tolerance, with the same number of pairs.
Both totals and solver versions are reported; reference pairs remain restricted.
This check is not proof of clinical balance or causal effect accuracy. Global
optimization can lower total distance while leaving an individual pair worse.
All three methods are evaluated on the same saved imputations/common population;
clinical PSM still differs in support rules and retention. No effects estimated.

## H100 run

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
bash scripts/run_comet_cosine_v3_h100.sh
```

The launcher checks SciPy using the previously successful interpreter-derived
C++ runtime preload. It creates a fresh RAID `comet-cosine-comparison-v3-*` report,
reusing all existing embeddings and imputations. No GPU inference or MICE rerun.
The 2,960 by 4,538 float64 distance matrix is approximately 107 MB, with additional
working memory. No H100 timing claim is made before execution.

Review `summary.json` assignment_objective, balance and retention; use
`comparison_love_plots.pdf` and feature-level/observed-only tables as before.
Compare with saved v2 `comet-cosine-comparison-v2-wiph2eZH/report`. Preserve both
results regardless of which has better measured clinical balance.
