# Review observed balance and representation limitations

This reads saved aggregate balance CSVs, verifying their hashes against each
comparison manifest. It does not read patient-level files or rescan raw sources,
refit models, or rerun matching. Fresh restricted RAID output preserves sources.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
bash scripts/run_comet_observed_review_h100.sh
```

The printed table compares completed versus observed-only median absolute SMD and
observed measurement counts. It shows clinical PSM once and cosine at every cutoff.
`all_feature_review.json` keeps all features/methods, signed observed SMD ranges,
pre-match SMDs, completed group means, observed fractions and missingness SMDs.
`summary.json` holds the declared focus set across all methods and cutoffs.
The focus is descriptive, selected after seeing prior results, not a new evaluation
feature set. No feature is removed from the full report. Counts/summary output must
remain restricted until locally reviewed.

## Verified from implementation and prior aggregate reports

- CLMBR extraction used codes-only inputs: measurement identities can be present,
  but numeric measurement values are omitted at model input. MEDS retains raw
  values separately. No direct EF-number representation from those numeric fields.
- No explicit static sex/race tokens were inserted; sex remains in the roster.
  Other history may indirectly carry related information; this is not proof that
  the representation contains zero information about sex.
- Exact birth and dated events provide temporal/age information, but do not
  enforce balance in age at index.
- Full extraction encoded7,498/7,499;102 histories were truncated to the latest
 4,096 token positions. Aggregate event-token acceptance was79.69%; this does not
  establish AF-specific or other concept-specific coverage. Domain mapping losses
  were reported previously, notably procedures. These are limitations, not a
  demonstrated explanation for any specific imbalance.
- Clinical PSM directly uses the32 declared clinical covariates; this is not an
  equal-input architecture-only experiment. All variants share evaluation variables,
  but embedding numeric/demographic content differs and source mapping is distinct.

## Interpreting observed-only diagnostics

The existing R evaluator masks originally missing values back out of each completed
dataset, then calculates available-case means/SMDs. It reports observed counts in
both arms. Its denominator comes from observed pre-match values in the common
cohort. The completed-data denominator comes from completed pre-match values;
therefore differences between the two SMDs are not solely caused by imputed means.
Available-case balance is not whole-cohort balance and does not validate MAR.

Cosine pairs are fixed across imputations. Observed-only cosine measurements/counts
should therefore be fixed as well; PSM pairs can change across imputations. The six
undefined constant missingness flags must remain undefined, not treated as perfect
balance. Missingness balance and observed sample fractions need joint review.

Prior aggregate imbalance identifies EF, AF and age as important review targets.
This audit does not infer which arm is higher from absolute SMDs, does not infer
numeric units or clinical validity, and does not authorize native numeric encoding
until its mapping/unit contract is separately reviewed. No new caliper tuning or
outcome-based selection is performed.
