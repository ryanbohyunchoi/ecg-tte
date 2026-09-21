# HF audit runtime and reuse plan

2026-09-21. Version 5 successfully scanned 83,987,596 medication, echo and DX data
rows. It did not record wall time, so no measured runtime or acceleration factor
is available. Do not repeat a completed audit just to benchmark.

Version 6 adds cumulative elapsed time and records/s at existing progress intervals,
per-source scan seconds, total elapsed seconds, bounded diagnosis-date caching
(32,768 values, each <=128 characters) and HF-code evidence caching (16,384 values,
each <=128 characters). Longer values use the same uncached functions. Caches
are in-memory only and cleared at run boundaries; no cache keys are reported.
All file parsing, failure conditions and cohort/phenotype definitions are unchanged.
24 HF/joint synthetic tests pass, including cached/uncached equivalence. No H100
end-to-end speedup has been measured. Clinical audit version 5 need not be rerun.

Runtime estimates should use stage rates: sum remaining medication/DX rows divided
by their measured rates, plus echo and final aggregation. Aggregate illustrations
for 84 million rows, excluding additional overhead: 5,000 rows/s ~4.7 h;
10,000 ~2.3 h; 20,000 ~1.2 h. These are arithmetic examples, not observed speeds.

Next architectural improvement (planned, NOT implemented): extract narrowly scoped
patient-key, medication, diagnosis and echo tables once into private RAID storage;
reuse them only under a source snapshot/schema/parser/extraction-version manifest.
Publish a completed stage atomically, retain explicit invalid/partial state, and
fail on stale or incompatible manifests. Preserve exact linkage and temporal
provenance. A completed medication/echo stage should survive a later DX failure
without being represented as a completed multi-source run. Restrict source columns
and predefine related questions so one pass serves several diagnostics. Parquet/
DuckDB or equivalent columnar processing is a candidate after synthetic and source
validation. Do not introduce unvalidated fast parsers, source copying, parallel
mount scans or unbounded worker counts merely to report faster execution.

The next scientific step remains diagnosis coverage/index contract then baseline
covariate availability; improving speed does not validate eligibility or MICE.
