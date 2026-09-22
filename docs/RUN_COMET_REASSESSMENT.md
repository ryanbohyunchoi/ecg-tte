# Reassess diagnosis evidence and verify limited hospital-lab reuse

The user approved a reassessment after2025DXrevealed missed HF/exclusion evidence.
This starts from the original medication candidate roster, not only6,530previous
members. Medication anchors, echo selection, arm ties and clinical rule are fixed.
Boolean HF/exclusion evidence is unioned across2025and2026diagnoses; duplicate
records cannot inflate Boolean evidence. This is not a complete recheck of other
medication deliveries or first-ever use. Same/future/undatedDXdoes not qualify.

Fresh output reports retained/entered/removed/not-selected counts by arm and saves
restricted transitions and a new candidate table. It does not overwrite the old
cohort or baseline. Other inherited candidate fields keep original source meaning;
DX_DATE_prior_hf_evidence is explicitly refreshed. Old downstream cohort readers
reject this new version until adapters and clinical extraction are updated.

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
AUDITS=/mnt/raid0/rbc58/ecg-tte/audits
SHARED=/mnt/raid0/rbc58/ecg-tte/shared
REASSESS_RUN=$(mktemp -d "$AUDITS/comet-expanded-dx-XXXXXXXX")
LAB_REUSE_RUN=$(mktemp -d "$SHARED/hospital-labs-limited-XXXXXXXX")
printf 'Reassessment: %s\nLimited labs: %s\n' "$REASSESS_RUN" "$LAB_REUSE_RUN"
PYTHONDONTWRITEBYTECODE=1 python scripts/reassess_comet_diagnoses.py \
  --candidate-report "$AUDITS/comet-candidates-c2FSBqdW/report" \
  --previous-report "$AUDITS/comet-broad-excluded-cnG52aaY/report" \
  --dx-2025-snapshot "$SHARED/diagnoses-2025-nauv2IgF/snapshot" \
  --output-dir "$REASSESS_RUN/report"
cat "$REASSESS_RUN/report/summary.json"
PYTHONDONTWRITEBYTECODE=1 python scripts/reuse_comet_hospital_labs.py \
  --source-snapshot "$SHARED/psm-sources-v1-0815146D/snapshot" \
  --output-dir "$LAB_REUSE_RUN/snapshot"
cat "$LAB_REUSE_RUN/snapshot/summary.json"
)
```

Hospital lab reuse is an explicit limited-source migration, not promotion of the
failed parent. Exactly2025hospital shards1/2are verified against parent stage
manifests, copied independently and revalidated using the unchanged source engine,
including full raw-file checksums/fingerprints, Parquet checksums/row counts/schema.
Parent remains failed and untouched; shard3is not read. New manifest/summary state
that complete applies only to the two selected shards. No hard links or manual
edits to the original manifests. Any verification failure marks new output failed.
No clinical lab availability, numeric interpretation or imputation is inferred.

Reassessment may take several minutes to tens of minutes for expanded source
scans. Lab verification reads roughly132GBraw input plus saved partitions, so allow
tens of minutes depending on storage throughput. It avoids reparsing/rebuilding
232million records but does not skip integrity checks. Needs space for independent
copies of two compressed lab stages. Preserve printed paths. No source repair,
MICE/PSM, HF hospitalization predictor reinstatement or outcome changes.

After reviewed counts, update cohort-dependent feature adapters and map labs from
the limited hospital snapshots plus the independent outpatient snapshot. Previous
baseline values must not be reused for newly entered patients or wrong roster hashes.
