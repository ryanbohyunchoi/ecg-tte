# Check reusable MEDS inputs for COMET

This read-only check uses the historical consolidated gold and remapped MEDS paths.
If the newly mapped gold has moved, change --gold-root to the actual snapshot.
The tool cannot prove that MEDS was built from the specified gold; lineage remains
an explicit requirement even when patient linkage succeeds.

It verifies the cleaned cohort manifest, scans person identity twice to detect
conflicting mappings outside the cohort, and reads only subject_id/time/code from
MEDS in bounded Arrow batches. Cohort filtering happens before conversion to Python
records. It reads no waveform, text note, numerical measurement values, raw JDAT,
or model tensors. It does not rebuild OMOP, run MICE or fit a model.

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
CLMBR_INPUT_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-clmbr-inputs-XXXXXXXX)
echo "Report directory: $CLMBR_INPUT_RUN/report"
python scripts/audit_comet_clmbr_inputs.py \
  --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report \
  --gold-root /mnt/raid0/rbc58/omop/gold \
  --meds-root /mnt/raid0/rbc58/mosaic/meds_extract_rbc_v2 \
  --model-root /mnt/raid0/eo287/clmbr \
  --output-dir "$CLMBR_INPUT_RUN/report" || {
    cat "$CLMBR_INPUT_RUN/report/summary.json"
    exit 1
  }
cat "$CLMBR_INPUT_RUN/report/summary.json"
)
```

Outputs stay private on H100. summary.json reports cohort counts, schema variants,
identity exclusions, dated pre-index code coverage, and fixed model-file presence.
restricted_person_linkage.parquet contains exact cohort linkage; do not share it.
restricted_source_inventory.json records partition size/mtime, not content hashes.
A file with the expected model name is not verified model identity. Missing fixed
filenames may mean a different model layout. No automatic downloads are attempted.

Undated codes (including legitimate static demographics) are reported separately;
they do not establish prior clinical history. Same-day events are excluded from
prior coverage. Birth-only histories may still count as dated-code coverage:
these counts must not be called model-eligible clinical histories. No temporal
availability, numeric-value, complete MEDS schema or tokenizer approval is implied.

After results: verify extraction lineage/model tokenizer and actual clinical-code
coverage. Reuse compatible prior events or build new cohort-specific MEDS from
gold where needed. Then run a small inference test before the full cohort.
