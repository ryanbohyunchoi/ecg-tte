# COMET and PARADIGM-HF medication feasibility screen

2026-09-17. Ryan runs this on H100. Standard-library Python only, no GPU. Read-only
source scan; fresh reports and temporary restricted SQLite storage in Ryan's home.
This is a **lexical medication candidate screen**, not a validated drug mapping,
HF cohort, initiation definition, dispensing audit or effect estimate.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
HF_MED_OUT=$(mktemp -d "$HOME/hf-medication-screen-XXXXXXXX")
python scripts/audit_hf_medications.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$HF_MED_OUT/report" \
  --expected-schema-sha256 61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8 \
  --full-scan
cat "$HF_MED_OUT/report/summary.json"
```

For a bounded smoke check, replace `--full-scan` with `--max-rows 500000` in a fresh
directory. Prefix counts are not population estimates. The full scan processes
31 million source rows and needs time and disk space, although only target-name
candidates enter patient/date tables. Progress prints record counts every 100,000
rows, not source values. Malformed rows, schema changes or source size/mtime changes
invalidate the audit; no rows are skipped. Interruption can leave private scratch
files on H100; keep them there and remove only after the process has stopped.

## Interpretation of summary.json

Each candidate bucket reports record counts and distinct nonmarker patient keys:

1. All name-matched records, including history, any route and mode.
2. Records labeled ORDERING_MODE=Outpatient and ORDER_CLASS=Normal or Print.
3. The same exploratory stratum with an order date usable for calendar comparison.

Names are searched in MEDICATION_NAME, GENERIC_NAME and SIMPLE_GENERIC with
case-insensitive whole tokens. No NLP, external vocabulary or ingredient-ID mapping
is used. Drug/formulation code sets are **not yet clinically reviewed**. Some
valid drugs may be missed, and lexical candidates may not be suitable treatments.
Do not equate these counts with complete arm coverage or eligible initiators.

- Carvedilol not explicitly marked extended release is a candidate, not verified
  immediate release. Explicit ER/CR/phosphate indicators form a review bucket.
- Metoprolol tartrate, succinate and unspecified are separate. Conflicting salt or
  release signals are quarantined rather than resolved by choosing one name field.
- Sacubitril/valsartan requires both generic ingredient tokens. Sacubitril alone
  is unresolved; valsartan alone does not enter the ARNI candidate bucket.
- Enalapril candidates are distinct from enalaprilat; recognized additional-drug
  combination signals go to a review bucket. This screen cannot prove absence of
  unrecognized combination ingredients.
- Brand-only matches remain a review bucket and do not populate either arm.

No route, dose, status or HF-eligibility filter is applied. In particular, no
later discontinuation or future refill determines entry. The Normal/Print stratum
is a planning comparison, not a frozen inclusion rule. Dates have the same explicit
format hypotheses as the date audit; offset-bearing/ambiguous slash dates are not
used for calendar comparisons. Null-marker patient keys are excluded, so the
identity policy is explicit and differs from the earlier whitespace-only audit.

For each bucket, earlier observed same-bucket order dates are summarized relative
to its first candidate prescription order. This is limited **recorded medication
history**, not continuous observation, absence of prior treatment, a washout, or a
new-user count. It does not reconcile history across metoprolol formulations or
unresolved brand names. No particular washout length is imposed.

Pair summaries count patients present in both dated candidate buckets and patients
with same-calendar-day candidate orders in both. The latter covers any such date,
not necessarily initial treatment assignment. Overlap may represent switching,
reconciliation or concurrent prescribing and needs review; it is not automatically
an exclusion. Do not sum patients across buckets. HF diagnosis, EF, calendar overlap,
background treatment, safety labs, endpoints and observation history remain separate
feasibility gates before choosing a trial cohort.

## Local mapping review

`restricted_mapping_review.json` contains candidate medication-ID/name/route
combinations and mode/class/route record strata. Keep it on H100; it can contain
unexpected sensitive values. Review locally and return only approved aggregate
mapping findings, never identifiers, free text or raw catalog contents. Patient
IDs and dates are never exported into either report. The exact dictionaries stay
within the approved environment for clinician/source review before cohort building.

Each catalog retains at most 2,000 distinct combinations and reports records omitted
from the catalog. This cap does not limit full-source bucket/patient/overlap counts.
Omissions still limit mapping review: do not mark mappings validated when variants
have not been checked. A new, reviewed mapping should be versioned separately.

Reference distinctions checked against official labeling for this screen:
[COREG CR](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d3625d78-6eb6-41fe-8f6f-664965c104c4),
[TOPROL XL](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=496ddfaa-7c9c-4888-b747-a210249b367a),
[ENTRESTO](https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=14bf8041-0b7f-9acb-e063-6294a90a8256).
These support formulation distinctions, not the meaning or validity of any JDAT row.
