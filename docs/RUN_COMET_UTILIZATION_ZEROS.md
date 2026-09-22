# Apply recorded utilization zeros to completed COMET staging v3

User approved0 for no qualifying recorded utilization. This creates staging v4
from the completed v3 patient and status tables, with no raw-source rescan. It
retains32covariates, cohort/index, all positive counts and technical nulls. Zero
means no qualifying **dated** encounter recorded within days1–365 before index,
not complete observation or absence of care elsewhere. Undated encounters do not
enter this dated count; no claim is made about their timing.

The converter checks parent checksums, feature specification, unique roster,
complete patient/feature statuses and aggregate reconciliation. Only null cells
with `zero_coverage_unvalidated` in the three utilization columns become0 and
`no_qualifying_record`. Conflicting keys/settings remain null. Recorded zeros
are not imputed. Labs and vital measurement contracts remain unresolved; this
is not MICE/PSM execution or a change of eligibility/endpoints.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_V3_REPORT=$(python - <<'PY'
import json
from pathlib import Path
root = Path('/mnt/raid0/rbc58/ecg-tte/audits')
reports = []
for p in root.glob('comet-baseline-v3-*/report/summary.json'):
    s = json.loads(p.read_text())
    if s.get('version') == 'comet_baseline_staging_v3' and s.get('status') == 'complete_baseline_staging' and s.get('counts_valid') is True:
        reports.append(p.parent)
if len(reports) != 1:
    raise SystemExit('Expected one completed v3 report; set COMET_V3_REPORT to the intended absolute report directory instead.')
print(reports[0])
PY
)
if [ -n "$COMET_V3_REPORT" ]; then
  COMET_V4_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-baseline-v4-XXXXXXXX)
  PYTHONDONTWRITEBYTECODE=1 python scripts/finalize_comet_utilization.py \
    --source-report "$COMET_V3_REPORT" \
    --output-dir "$COMET_V4_RUN/report"
  cat "$COMET_V4_RUN/report/summary.json"
fi
```

Expected conversion totals from reviewed v3:1,169inpatient,1,692ED and2,771
outpatient null counts become recorded zeros. These groups overlap. Other
feature counts must remain unchanged. Runtime should be seconds for6,530rows,
not another multi-minute raw scan; actual H100 timing is pending. The HF linkage
diagnostic stays in the parent report, referenced through lineage. Fresh output
only; old runs are preserved.
