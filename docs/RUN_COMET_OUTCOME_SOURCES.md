# Run the COMET outcome-source audit on H100

Ryan runs this code in the approved research environment. The assistant does not access H100. This first audit uses the **provisional** existing 6,530 candidate roster solely to assess source quality. Rerun with Track 1's final versioned roster before an outcome attachment. It does not choose an endpoint or estimate effects.

```bash
(
set -e
umask 077
COMET_REPO="$HOME/github/ecg-tte"
COMET_CODE="$HOME/github/ecg-tte-comet-outcomes"
COMET_AUDITS=/mnt/raid0/rbc58/ecg-tte/audits
COMET_SHARED=/mnt/raid0/rbc58/ecg-tte/shared
COMET_ROSTER="$COMET_AUDITS/comet-broad-excluded-cnG52aaY/report/restricted_broad_candidates.parquet"
COMET_CLINICAL="$COMET_SHARED/clinical-sources-v1-t9ZGomLT/snapshot"
test ! -e "$COMET_CODE"
git -C "$COMET_REPO" fetch origin codex/comet-outcomes
git -C "$COMET_REPO" worktree add --detach "$COMET_CODE" origin/codex/comet-outcomes
COMET_RUN=$(mktemp -d "$COMET_AUDITS/comet-outcome-source-XXXXXXXX")
printf 'Private outcome audit: %s\n' "$COMET_RUN"
cd "$COMET_CODE"
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_outcome_sources.py \
  --roster-parquet "$COMET_ROSTER" \
  --clinical-snapshot "$COMET_CLINICAL" \
  --output-dir "$COMET_RUN/report"
)
```

Inspect `report/summary.json` **on H100** first. It is marked restricted until reviewed. Keep `report/restricted_patient_qc.parquet` and all patient-specific dates/keys on H100. Return only reviewed, non-identifying aggregate findings. A failed audit has `counts_valid=false`; do not use partial counts. The audit needs a fresh output path and does not modify source snapshots or the cohort.

The reported number of inpatient candidates is only keyed, dated, `INP_YN=1` record presence after index. It does not identify distinct clinical admissions. A death date's absence does not prove survival. Maximum event years show observed records, not a valid administrative censor date.

## Next pooled follow-up feasibility run

After updating the detached outcomes worktree, run a fresh aggregate-only job. It does not read treatment arm and does not assign censoring or outcomes.

```bash
(
set -e
umask 077
COMET_REPO="$HOME/github/ecg-tte"
COMET_CODE="$HOME/github/ecg-tte-comet-outcomes"
COMET_AUDITS=/mnt/raid0/rbc58/ecg-tte/audits
COMET_SHARED=/mnt/raid0/rbc58/ecg-tte/shared
COMET_ROSTER="$COMET_AUDITS/comet-broad-excluded-cnG52aaY/report/restricted_broad_candidates.parquet"
COMET_CLINICAL="$COMET_SHARED/clinical-sources-v1-t9ZGomLT/snapshot"
git -C "$COMET_REPO" fetch origin codex/comet-outcomes
git -C "$COMET_CODE" checkout --detach origin/codex/comet-outcomes
FOLLOWUP_RUN=$(mktemp -d "$COMET_AUDITS/comet-followup-feasibility-XXXXXXXX")
printf 'Private follow-up audit: %s\n' "$FOLLOWUP_RUN"
cd "$COMET_CODE"
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_followup_feasibility.py \
  --roster-parquet "$COMET_ROSTER" \
  --clinical-snapshot "$COMET_CLINICAL" \
  --output-dir "$FOLLOWUP_RUN/report"
cat "$FOLLOWUP_RUN/report/summary.json"
)
```

The summary contains pooled aggregates and source hashes. Review it on H100 before sharing. Encounter-at-landmark counts measure recorded contact only; do not use them to require future contact, declare survival, set loss to follow-up or select a horizon.
