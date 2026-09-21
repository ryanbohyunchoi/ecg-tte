# Build provisional COMET candidates while lab conversion runs

This job reads only the completed medication/DX/echo core snapshot. It does not
read the unfinished extension, scan raw JDAT or change the lab builder. It can run
in a second tmux window. It adds CPU/storage load, so it may slow the conversion;
it uses one scanner thread and the command below lowers CPU scheduling priority.
Runtime has not been measured on H100; no fixed speedup is promised.

## Run now

The selector discovers exactly one completed snapshot containing all four core
tables. It ignores the building PSM extension. If more than one completed core
snapshot exists it stops; specify the intended exact path with --snapshot instead
of --shared-root. It never chooses the newest directory implicitly.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_CANDIDATE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-XXXXXXXX)
echo "Candidate report: $COMET_CANDIDATE_RUN/report/summary.json"
nice -n 10 env PYTHONDONTWRITEBYTECODE=1 python scripts/build_comet_candidates.py \
  --shared-root /mnt/raid0/rbc58/ecg-tte/shared \
  --output-dir "$COMET_CANDIDATE_RUN/report"
cat "$COMET_CANDIDATE_RUN/report/summary.json"
```

This release does not alter any of the running builder's implementation-hash
files. No restart of the lab job is needed. Outputs use a new private RAID audit
directory and cannot overwrite an existing run. No partial-output reuse is offered.

## What this creates

- `restricted_candidates.parquet`: one record per exact patient key with a dated
  lexical candidate, provisional arm/date, medication source-row lineage, prior
  carvedilol/metoprolol family evidence and latest-prior echo/HF-code evidence.
- `restricted_candidates.sqlite`: retained medication-family evidence, including
  source ordinals and dates, for local review. This is sensitive patient data.
- `restricted_manifest.json`: core manifest/output hashes and rule identifiers.
- `summary.json`: aggregate counts and separate HF/EF evidence groups by arm and
  diagnosis-date view. Review this locally before sharing. Small-cell release
  decisions remain on H100; the report is marked restricted.

Only the reviewed summary should return to chat. No identifiers, patient dates,
Parquet, SQLite or raw catalogs should be pasted. Failed runs have invalid counts;
partial patient files are not usable.

## Explicit provisional rules

The earliest dated lexical outpatient Normal/Print order is selected jointly across
carvedilol-not-marked-extended and metoprolol-tartrate buckets. These are the existing
name-screen hypotheses, not approved drug mappings. There is no route, dose,
status, clinical HF or new-use qualification. Earlier anchors counted separately
per arm in the old audits are therefore not the denominator of this new output.
Same-day competing arms form a separate unresolved group. Later switching does not
remove earlier candidates; no future visit/refill is required. No clinical index
rule is frozen by this exploratory output.

History counts cover lexical carvedilol/metoprolol families in the 365 days before
anchor, including other order classes/formulations. They are row counts, not fills,
unique events or adherence, and do not cover all beta-blockers. Undated family
records are flagged. Neither history result excludes a patient. Broader validated
class mapping and observation coverage are still required for new prescribing.

Echo uses latest strictly prior day, with no older fallback for missing/invalid
latest values. Report missing, stale (>365 days), same-latest-day disagreement,
scale/range ambiguity, EF (1,35), EF=35 and EF (35,100] separately. Numeric units
and report availability remain unvalidated. Undated echo presence is an additional
flag; no eligibility decision can use it as resolved prior evidence.

HF evidence uses the existing provisional I50 token search. DX_DATE and
CALC_DX_DATE remain independent, without fallback; ICD9/other code families and
historical mappings are unassessed. Prior, same-day, later and undated HF flags
are for temporal QC. Same/later flags must never become baseline model features.
No diagnosis availability or phenotype validation is claimed. Generic HF, systolic
code and no-prior-code-found groups remain separate.

This output is a reusable **candidate roster**, not a final COMET cohort. Final
eligibility, all-beta-blocker history, encounter observation, demographics,
contraindications, index semantics and endpoint capture remain gated in
COMET_COHORT_DRAFT.md. Labs are not the sole remaining eligibility issue. Covariate
availability and MICE/PSM follow after source and cohort contracts are resolved.

## Integrity and verification

The shared reader requires a globally complete core snapshot and checks stage
manifests, sizes, schemas and Parquet footers. This job records the core manifest
hash and checks it plus part sizes/mtimes again at completion. It does not rehash
all input parts or raw sources; completed snapshots must remain immutable. Output
Parquet row count and hash are recorded. Clinical maps and identity are not
validated by these integrity checks. Synthetic tests cover arm ties, future
switching, prior/undated history, echo fallback prevention, date-view separation,
EF=35, discovery ambiguity, incomplete cores, changed manifests and output overlap.

## Find out whether a candidate run already finished

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/check_comet_runs.py \
  --audit-root /mnt/raid0/rbc58/ecg-tte/audits
```

This read-only check lists saved candidate-run directories without launching a new
job. Completed runs must have matching summary/manifest counts and source-manifest
references, a matching candidate-file SHA-256 and matching Parquet footer count.
No patient records are printed. `complete_candidate_artifact_verified` means the
provisional artifact passes those checks, not that clinical eligibility is
validated. `not_complete_process_state_unknown` does not distinguish a live job
from an interrupted one. Zero matching directories means no runs found under this
specific naming/location convention, not proof that no job ever ran elsewhere.
