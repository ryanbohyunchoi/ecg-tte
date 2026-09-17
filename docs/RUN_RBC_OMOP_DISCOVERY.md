# Locate and compare existing RBC outputs without changing them

Ryan runs this on the H100. No assistant SSH. This is discovery and metadata
inspection only; it does not run the historical mapping scripts, scan patient
rows, remap, repair or write into any source/output dataset.

Local references identify candidate locations, not verified cluster paths:

- cards-misc feature branch: `mosaic/gold_rbc` and `bb2238/omop/gold_rbc`.
- Archived ecg-tte documentation: `~/mnt/ecg-tte/drugs`,
  `/mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet`, and older ASCVD OMOP.
- Use explicit data subdirectories. Do not scan the entire RAID user root or
  ecg-tte project root: the required report destination now lives beneath them,
  and the discovery tool correctly refuses overlapping source/output trees.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation

umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
RBC_AUDIT_OUT="/mnt/raid0/rbc58/ecg-tte/audits/rbc-output-discovery-$(date +%Y%m%d-%H%M%S)"
python scripts/discover_omop_outputs.py \
  --root /mnt/raid0/rbc58/mosaic \
  --root /mnt/raid0/rbc58/ecg-tte/drugs \
  --root /mnt/raid0/rbc58/omop \
  --root /mnt/raid0/rbc58/mm_vhd/drug \
  --root /mnt/raid0/bb2238/omop/gold_rbc \
  --root /mnt/raid0/bb2238/ecg_ascvd/omop_database \
  --root "$HOME/mnt/ascvd/omop_database" \
  --output-dir "$RBC_AUDIT_OUT"

cursor "$RBC_AUDIT_OUT/summary.json"
```

Each root is reported independently. Overlapping roots may rediscover the same
files; their counts must not be added as independent data. Reports stay outside
all source trees in a new private audit directory under `/mnt/raid0/rbc58/ecg-tte/audits`; existing outputs are refused.

The script uses breadth-first directory discovery, capped per root at depth 5,
50,000 directory entries and 40 schema samples. It records paths of table-like
directories, discovered manifest files and parquet schemas (one first-encountered
sample per table/filename family, so labs and vitals can both appear). It reports
missing paths, inaccessible directories, skipped symlinks and exhausted limits.
A bounded search cannot prove that an unfound output does not exist elsewhere.
Filesystem calls on shared mounts can still block. A killed report remains running.

Pyarrow is needed for parquet footer schemas; without it, discovery still works
and schema status says `pyarrow_not_installed`. Use an existing research environment
with pyarrow. The script never installs packages, reads parquet rows or imports
archived transformation code. Metadata row counts describe sampled files only.

Review before sharing the report. Filenames and schemas can be sensitive even
without patient rows. No raw tables, patient examples or clinical notes are needed.

Comparison with bb2238 will focus on which outputs exist, drug_concept_id versus
ATC-only coding, medication detail fields, visits/procedures, measurement units,
and whether each location is a complete set of tables or a supplement. Actual
concept distributions, mapping accuracy, patient coverage and file-to-run lineage
remain later checks; schema discovery cannot answer them.
