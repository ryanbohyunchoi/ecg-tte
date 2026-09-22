# Build and audit separately selected2025sources

User-approved next phase: build two2025diagnosis tables separately, and assess
baseline lab feasibility using only the2025outpatient lab file. No damaged
hospital shard is opened; failed snapshot stages are not promoted. Limited lab
coverage is explicit. Builds preserve raw values, hash sources, enforce schema/
UTF8/1MiB record width, count all records, and optionally permit one exact empty
terminal line only at EOF. Any other malformed row stops the build.

Run this complete block on H100. It stops dependent steps on failure. Each source
selection has its own fresh snapshot, so a lab failure does not erase the diagnosis
build. No old snapshot or patient cohort is overwritten.

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_RAW=/home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG
COMET_SHARED=/mnt/raid0/rbc58/ecg-tte/shared
COMET_AUDITS=/mnt/raid0/rbc58/ecg-tte/audits
mkdir -p "$COMET_SHARED" "$COMET_AUDITS"
DX25_RUN=$(mktemp -d "$COMET_SHARED/diagnoses-2025-XXXXXXXX")
LAB25_RUN=$(mktemp -d "$COMET_SHARED/outpatient-labs-2025-XXXXXXXX")
AUDIT25_RUN=$(mktemp -d "$COMET_AUDITS/comet-2025-feasibility-XXXXXXXX")
printf 'Diagnosis snapshot: %s\nLab snapshot: %s\nAudit: %s\n' "$DX25_RUN" "$LAB25_RUN" "$AUDIT25_RUN"
PYTHONDONTWRITEBYTECODE=1 python scripts/build_comet_2025_sources.py \
  --root "$COMET_RAW" --domain diagnoses --allow-terminal-empty-line \
  --output-dir "$DX25_RUN/snapshot"
PYTHONDONTWRITEBYTECODE=1 python scripts/build_comet_2025_sources.py \
  --root "$COMET_RAW" --domain outpatient-labs --allow-terminal-empty-line \
  --output-dir "$LAB25_RUN/snapshot"
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_2025_sources.py \
  --cohort-report "$COMET_AUDITS/comet-broad-excluded-cnG52aaY/report" \
  --dx-snapshot "$DX25_RUN/snapshot" --lab-snapshot "$LAB25_RUN/snapshot" \
  --clinical-snapshot "$COMET_SHARED/clinical-sources-v1-t9ZGomLT/snapshot" \
  --output-dir "$AUDIT25_RUN/report"
cat "$AUDIT25_RUN/report/summary.json"
)
```

Allow roughly30–60minutes for first conversion plus audit, a rough estimate based
on prior throughput and52.3GBinput, not a benchmark. Completed snapshots make
subsequent audits faster. Preserve printed directories. Resume a failed/interrupted
build only with its exact original arguments/path plus `--resume`; no resume of
the old globally failed PSM snapshot. Corrected inputs need new provenance.

The fixed-cohort audit reports same-patient/CSN matches to unambiguous2025inpatient
keys, diagnosis flags in days1–365, and any strictly prior diastolic/HFpEF exclusion
signals separately. It does not enforce exclusions, add candidates, or reinstate
the HF hospitalization predictor. A later cohort re-evaluation would need explicit
new versioning and include potential entries as well as exclusions.

Lab coverage is **any result-dated record within prior90days**, not usable
creatinine/potassium/sodium/hemoglobin completeness. The local restricted component
catalog enables the next mapping step; it contains labels and must stay on H100
until reviewed. No numeric results are exported. Missing aggregate flags mean0;
patient counts overlap across flags/sources. RESULT_DATEclinical/availability
semantics remain unvalidated. MICE/PSM and unit assumptions remain unchanged.
