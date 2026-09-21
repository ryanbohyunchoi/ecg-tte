# Bounded PSM source profiling before extension builds

Run on H100; no shared snapshot is rebuilt. This reads the first 10,000 records
from each of the 19 verified demographic/encounter/vital/lab paths (at most 190,000
records). The missing 2026 patient file is explicitly omitted. Reviewed schema
hashes are pinned. These are nonrandom prefixes, not representative coverage or
clinical missingness estimates. A 1-MiB physical-line limit and literal-tab
hypothesis are enforced without skips/repairs; the new domains' full formats are
not yet validated. A failure is reported per source while other files are checked.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
PSM_PROFILE_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/psm-source-profile-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/profile_psm_sources.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG \
  --output-dir "$PSM_PROFILE_OUT/report" \
  --max-rows-per-file 10000
cat "$PSM_PROFILE_OUT/report/summary.json"
```

Review aggregate summary.json before sharing. It contains per-source rows/scope,
key-presence, date/numeric formats, unit-column presence and catalog-omission counts.
No patient N, patient-specific dates, identifiers, raw values, categorical labels
or clinical thresholds are printed. Numeric sign/format is not clinical validity;
clock-only values are not silently combined with another date field. Missing-value
markers are candidate interpretations, preserved in sources. BP-like slash pairs
and inequality-qualified measurements are counted, not converted.

`restricted_measurement_catalog.json` stays on H100. It contains local component
IDs/names/base names for labs and local flowsheet IDs/names/display labels/units for
vitals. Those values could contain unexpected sensitive text. Review locally and
return only approved relevant mapping findings (e.g., component ID, verified
analyte identity and source of unit definition), never the entire unreviewed file.
Catalogs retain at most 2,000 combinations per source and omit values over 256
characters; omissions are explicitly counted. Absence in a prefix/catalog is not
proof a clinical variable is unavailable. Lab value text, comments and narratives
are never cataloged. No explicit lab unit column exists in the reviewed schemas;
component catalog review is only a lead to source-specific unit verification.

After review: define numeric/date contracts and unit lookup provenance, investigate
2025/2026 overlap and row formats, then build separately versioned extension tables.
Do not combine deliveries or impute missing units to produce a clinical value.
Source files and the completed four-table snapshot are unchanged.

Verification: four new synthetic tests cover bounded scope, privacy separation,
schema/width failure, catalog omissions and output safeguards.
