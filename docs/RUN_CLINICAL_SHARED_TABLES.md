# Independent demographics, encounters and vitals snapshot

The previous PSM extension failed on a lab source. Its completed stages remain part of a globally failed snapshot and are not promoted or bypassed. This build creates a fresh, independently complete snapshot from eight explicitly selected raw sources. No lab source is opened, repaired, copied or skipped by the parser. Existing core and failed extension snapshots remain unchanged.

## Selection

- Data-2025-04-03: Patients, Hosp_Enc, Outpatient_Enc, Outpatient_Enc_Flo_Vitals.
- Data-2026-04-15: Hosp_Enc, Outpatient_Enc, Hosp_Enc_Flo_Vitals, Outpatient_Enc_Flo_Vitals.

There is no known available 2026 Patients file in the approved inventory. Missing demographic refresh remains a limitation, especially for death capture. Each delivery has its own table; overlapping records are not unioned or deduplicated. This is source conversion only, not a baseline feature extractor, a validated encounter-setting map or a final clinical cohort.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/shared
CLINICAL_SHARED_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-XXXXXXXX)
echo "Clinical run: $CLINICAL_SHARED_RUN"
PYTHONDONTWRITEBYTECODE=1 python scripts/build_clinical_shared_tables.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG \
  --output-dir "$CLINICAL_SHARED_RUN/snapshot" \
  --allow-terminal-empty-line
cat "$CLINICAL_SHARED_RUN/snapshot/summary.json"
```

Use the PyArrow environment from the prior shared builds. All new output is on RAID, not HOME. Record the printed run path in case shell variables are lost. Return the reviewed summary only; patient tables remain on H100.

Runtime for this complete selection is unmeasured. The four 2025 stages previously took approximately12.6 minutes altogether; the four 2026 stages add time. Do not interpret that subtotal as the total estimate. Each stage prints progress and completion timing. This reprocesses raw sources once to obtain an independently valid snapshot; it does not reuse unverified files from the failed build.

## Integrity and resumption

All selected headers are checked before building. The parser preserves raw fields, adds normalized keys and parsed dates with QC, enforces1MiB record limits, and fails on malformed clinical records. The terminal-empty option allows only one exact empty physical line at EOF per file and accounts for it; it is not permission to skip malformed lines. All eight stages must finish before normal shared-table readers accept the snapshot.

A same-run restart may use `--resume` with exactly the printed clinical snapshot path and the same flags/environment. Do not create a new temporary directory for a resume. Never point this command at the older PSM snapshot; the source/driver/runtime contract differs and must be rejected. Resume validates completed source and output hashes and can take time. The selection driver's hash is part of each source specification; the shared builder implementation and its previous contracts are unchanged.

Synthetic checks verify the exact eight-file inventory, no lab-header access, fail-closed schema/inventory changes, complete source conversion despite absent lab files, output non-overwrite, compatible resume, incompatible-driver rejection and rejection of malformed clinical rows.

## Next gate

After completion, audit exact patient linkage, DOB consistency and pre-index encounter coverage by arm and delivery. Then review vital measurement IDs/names/units and select validated pre-index measurements. The global completion status alone does not validate clinical semantics. Do not classify missing BP/pulse as normal or infer hospital admission from the source filename. The labs, outcome ascertainment and complete eligibility protocol remain separate unresolved requirements. No new cohort exclusions or PSM run are introduced here.
