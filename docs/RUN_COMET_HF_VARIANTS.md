# Count broader COMET HF/EF variants

This is a count-only sensitivity audit on the completed, fixed candidate roster.
It does not create a new eligible cohort, change treatment anchors, impose a
washout, impute EF, or estimate effects. It reads diagnosis and echo columns from
the complete core snapshot. Neither medication rescanning nor labs are needed.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_HF_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-hf-variants-XXXXXXXX)
echo "Report: $COMET_HF_RUN/report/summary.json"
nice -n 10 env PYTHONDONTWRITEBYTECODE=1 python scripts/count_comet_hf_variants.py \
  --audit-root /mnt/raid0/rbc58/ecg-tte/audits \
  --output-dir "$COMET_HF_RUN/report"
cat "$COMET_HF_RUN/report/summary.json"
```

The script requires exactly one verified completed candidate run under the audit
root; otherwise use --candidate-report with its exact report directory. It never
selects the newest run automatically. It checks the candidate file hash/footer and
core manifest lineage, uses the complete shared reader, and checks input stability
at completion. Input parts are not all rehashed; snapshots must remain immutable.
One scanner thread; no measured H100 runtime for this version. Output is aggregate
only, restricted until reviewed locally. No diagnosis names or patient keys are
exported. Saved candidate files and the failed lab extension remain untouched.

## Six scenarios and their differences

Let S be any strictly prior systolic/combined code evidence, H any strictly prior
provisional I50 HF code, and E latest strictly prior numeric EF >1 and <40 within
365 days. Scale/units and clinical timing are still unvalidated hypotheses. EF=40
is counted separately, not admitted by E. Latest invalid/missing/conflicting EF
has no older-value fallback. Unknown echo dates are flagged in aggregate.

- Baseline: S OR E.
- Broad comparison: H OR E (no exclusions).
- General HF with isolated diastolic/HFpEF excluded from the code pathway, OR E.
- Same isolated diastolic/HFpEF exclusion applied to the entire patient, including E.
- General HF excluding any explicit diastolic/HFpEF signal from the code pathway, OR E.
- Same any-diastolic/HFpEF exclusion applied to the entire patient, including E.

Each scenario has a count by arm/date view and an explicit difference from S OR E.
The code-branch variants allow low EF to qualify a person despite an exclusion
flag. Entire-patient variants do not. Exclusions are evaluated across the patient's
strictly prior diagnosis history, not by dropping only an offending row. They do
not use same-day or later diagnoses. An old diastolic diagnosis can coexist with
later reduced EF; this is why both exclusion interpretations are reported.

Isolated diastolic codes: I50.3 and I50.30–I50.33. Combined systolic/diastolic:
I50.4 and I50.40–I50.43. The existing provisional general/systolic search sets are
retained to keep the comparison traceable; parent code validity, year coverage,
ICD9 and other HF families remain unresolved. General I50 includes other HF
subtypes and is not a validated HFrEF phenotype after these exclusions.

Name flags search DX_NAME for HFpEF, preserved EF/ejection fraction, or the word
'diastolic', case-insensitively. Isolated exclusion uses isolated diastolic codes
or HFpEF/preserved-EF wording. Any-diastolic exclusion additionally uses combined
codes or any diastolic wording. This latter rule intentionally implements the
literal request and may capture diastolic dysfunction/pressure or negated terms.
This is lexical sensitivity analysis, not negation-aware NLP or review of notes.
No positive phenotype is inferred from name text alone. A malformed code list
produces no partial code acceptance; unresolved-code flags are counted separately.

DX_DATE and CALC_DX_DATE are independent views with no fallback or preferred date
inferred. The time window for prior codes remains unrestricted before anchor, as
in the current roster. All counts include separate unresolved treatment-tie rows;
those ties are never silently assigned to an arm. Scenario counts overlap and
must not be summed. Evidence strata reconcile separately to each arm denominator.
General-code inclusion may add patients, while literal diastolic exclusions may
remove combined systolic/diastolic cases. Neither larger N nor this audit validates
clinical eligibility, treatment initiation or complete observation.
