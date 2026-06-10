# stage3_filter.py generalization (vero KeyError fix)

Crash: `KeyError: 'prior_meto_days'` at line 277. Root cause: stage3_filter.py
hardcodes COMET arm names ("carvedilol"/"metoprolol") and alias columns
(prior_meto_days/prior_carv_days), but identify_arms_generic() (stage1) only
produces those aliases for COMET — other trials get prior_<arm_name>_days
using their own arm names (e.g. prior_teriparatide_days).

## Fixes
- [x] Attrition.log(): count per actual `arm` value present in df (dynamic n_<arm> cols)
      instead of hardcoded carv/meto.
- [x] Step 2 naive new-user lookback (lines ~272-283): generalize using
      pool["arm"].unique() and prior_<other_arm>_days columns.
- [x] Manifest + final print block (lines ~521-540): dynamic per-arm counts.

## Verify
- [ ] Re-run `bash scripts/run_stage34.sh --trials "vero"` on cluster, confirm
      stage3 completes and produces comet_cohort.parquet + attrition.csv.

## Note
`--meto-formulation tartrate_only` path (lines ~344-384) still hardcodes
"metoprolol"/METOPROLOL — only triggers for non-default flag, COMET-only
analysis, left as-is.
