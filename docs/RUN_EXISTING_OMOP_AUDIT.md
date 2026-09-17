# Read-only inspection of the existing bb2238 OMOP output

Ryan's instruction: assess the existing bb2238 mapping without changing it. Do not
run ETL, gold remapping, staging, repair, or cache-clearing commands against it.
The assistant never accesses the cluster. Ryan runs the following on the H100.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation

umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
OMOP_AUDIT_OUT="/mnt/raid0/rbc58/ecg-tte-audits/existing-omop-audit-$(date +%Y%m%d-%H%M%S)"
python scripts/audit_existing_omop.py \
  --omop-root /mnt/raid0/bb2238/omop \
  --output-dir "$OMOP_AUDIT_OUT"

cursor "$OMOP_AUDIT_OUT/summary.json"
```

The input path is from cards-misc documentation; it has not been independently
verified on the cluster. The script fails safely if unavailable. Output is a new
restricted directory under `/mnt/raid0/rbc58/ecg-tte-audits`, entirely outside the existing OMOP tree.

The script reads only existing run manifests, directory entries, and parquet
footer/schema metadata. It never reads patient rows or writes to the existing
OMOP root. It does not execute/import cards-misc ETL code or change any source
configuration. It skips symlinks; no log files or raw exception strings are copied.

`summary.json` contains:

- The newest 20 manifest files by filesystem mtime (not automatically assumed to
  be successful or complete), with explicit selected/total counts. It retains
  source-file lists, stage counts, mapping rates when recorded, missing columns,
  run timestamps and failing step IDs. It omits error text and top-unmapped values.
- Presence and parquet-file counts for ten expected gold tables; the first three
  parquet files in lexical order per table have their column names/types and
  footer row counts reported. These are samples, not whole-table row counts or
  exhaustive schema validation.
- Explicit limitations: no patient-level coverage or matching validation, and
  manifest history alone cannot prove which run last wrote each current partition.

Python's standard library is enough for manifests. Parquet metadata needs
`pyarrow`; if unavailable, the report explicitly says `pyarrow_not_installed` and
still reports manifest evidence. Use an existing research environment with
pyarrow for that portion; the script does not install anything.

Review the report before sharing it. Paths, column names and aggregates remain
restricted until reviewed. Do not send original logs, parquet files, rejects,
patient records or database credentials. A still-running or interrupted report
is incomplete. A completed metadata inspection is not approval to start a trial.

This report will distinguish main's ATC-only, limited-measurement output from an
expanded feature-branch output (e.g., presence of drug_concept_id, visits and
procedures). Missing mapping-rate fields mean unavailable evidence, not 0% or
100% coverage. Actual mapping correctness, measured-value resolution and cohort
coverage will require subsequent targeted read-only aggregate checks.
