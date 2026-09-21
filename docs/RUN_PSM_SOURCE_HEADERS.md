# Next shared domains: PSM source header check

The medication/DX/echo shared snapshot is complete and must remain unchanged.
Before adding demographics, labs, vitals and encounters, inspect the exact RBC
schemas. T2DM headers and old OMOP mappings do not establish these source contracts.

This command reads at most one bounded 64-KiB candidate header from each of 20
explicit paths across the 2025/2026 deliveries. It does not scan patient rows,
rebuild the shared snapshot or combine overlapping deliveries. Grouping headers
reduces repetitive output but does not prove records are equivalent/disjoint.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
PSM_HEADERS_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/psm-source-headers-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/inspect_psm_source_headers.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG \
  --output-dir "$PSM_HEADERS_OUT/report"
cat "$PSM_HEADERS_OUT/report/schema_groups.json"
```

Review output locally before sharing the column names/schema groups and unavailable
file statuses. A 2026 patient file is deliberately probed because only the 2025
patient file was established by prior lineage. Missing candidates yield incomplete
status/exit 2 but available headers remain useful. Do not substitute or union files
automatically. If the source root is unavailable, no headers have been inspected.

Expected work: demographics (birth/sex and death freshness), laboratory values,
component identities/units and clinical/availability times, vital/flowsheet units
and timestamps, encounter IDs and care setting/admission/discharge fields. Header
presence alone does not validate any numerical measure or baseline feature.

After review, build additional source tables in a separately versioned extension
with source/parser/row-accounting gates. The original four-table snapshot is not
rewritten or modified. Extension source selection and overlap resolution remain
pending. Existing source builder dependencies are unchanged by this header helper,
so its new files do not change the completed builder's implementation fingerprint.
