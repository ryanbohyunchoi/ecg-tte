# Reusable candidate event cache

Implemented locally and synthetically tested; cluster performance is unmeasured.
This is a downstream cache of complete shared snapshots, not a replacement for
those trial-independent snapshots. Raw files and existing snapshots stay unchanged.

## What changes

The diagnosis reassessment, baseline staging, vital extraction and 2025 source audit
now filter exact patient keys in Arrow before converting selected rows to Python.
This reduces Python work even without a cache; it does not guarantee less disk I/O.
No date, eligibility, feature, endpoint or matching rule changes.

`candidate_event_cache.py` additionally writes reusable compressed Parquet containing
all events for the **original broader medication candidate roster**, including people
not currently selected by the HF definition. It retains all columns and dates,
including undated and post-index events. It is a warehouse extract, **not a baseline
feature table**. Every consumer must still apply its own pre-index restrictions;
representations must never consume the entire all-date cache without those cutoffs.

Sources remain separate by source-manifest hash and table name. No cross-delivery
deduplication or clinical unit mapping is implied. Other trials can reuse a cache
only when their entire candidate roster is a subset and the source manifests match;
otherwise build a new cache for their broader candidate roster.

## Build once on H100

Do not rerun the completed shared-table builds or lab recovery. This new pass reads
those completed Parquet tables. It can still take substantial time on its first run;
we will use per-table retained rows, sizes and times to measure the benefit.
Run this in a persistent terminal session. All output stays under RAID.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/shared
CACHE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/shared/comet-event-cache-XXXXXXXX)
python scripts/candidate_event_cache.py \
  --candidate-report /mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-c2FSBqdW/report \
  --source-snapshot /mnt/raid0/rbc58/ecg-tte/shared/source-v1-9Ka1kA0i/snapshot \
  --source-snapshot /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot \
  --source-snapshot /mnt/raid0/rbc58/ecg-tte/shared/diagnoses-2025-nauv2IgF/snapshot \
  --source-snapshot /mnt/raid0/rbc58/ecg-tte/shared/outpatient-labs-2025-fOMEo0i1/snapshot \
  --source-snapshot /mnt/raid0/rbc58/ecg-tte/shared/hospital-labs-limited-PSRQd0Ue/snapshot \
  --output-dir "$CACHE_RUN/cache" > "$CACHE_RUN/build.log" 2>&1
cat "$CACHE_RUN/cache/summary.json"
```

The manifest persists all source paths and identities, so a lost shell variable does
not lose provenance. Find saved summaries with:

```bash
find /mnt/raid0/rbc58/ecg-tte/shared -maxdepth 3 -type f \
  -path '*/comet-event-cache-*/cache/summary.json' -print
```

A complete manifest is required. A failed build cannot be consumed; this first
version does not resume partial cache builds. Logs contain aggregate progress only.
Review summaries on the cluster before sharing.

## Reader integration and remaining work

`reassess_comet_diagnoses.py` accepts `--candidate-cache /absolute/path/to/cache`;
it verifies source identity, requested population coverage, cached part checksums,
rows and schema before reading. Synthetic cached/direct cohort and transition
results agree. **Do not repeat the already completed reassessment just to use this
option.** The shared `open_cached` reader is available for the next feature extractor.
Cache adoption by that refreshed extractor remains to be implemented.

Existing vital/baseline scripts receive the early Arrow filter but still enforce
their existing cohort/version contracts. They are not yet a refreshed baseline for
the 9,735-person expanded cohort, and must not be used as if they were. Next combine
both diagnosis deliveries, the selected lab sources and clinical tables in a single
versioned baseline extraction using the cache. Keep mapping/QC and feature extraction
in that same pass where possible. Then freeze eligibility/features/outcomes, assess
missingness on the final cohort, run MICE and PSM. No imputation or effect estimation
is added by this performance change.
