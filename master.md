# Project operating instructions

## Cluster access and PHI boundary — user instruction, 2026-09-09

- The assistant works on code, documentation, and synthetic tests locally.
- The assistant must not SSH into the cluster or attempt direct remote access,
  including read-only file listings. Locally configured SSH credentials or aliases
  do not authorize cluster access.
- Ryan pulls the code onto the H100 and runs all cluster commands himself.
- Write source-discovery and profiling code for Ryan to run on the H100. Do not
  discover JDAT files by connecting to the cluster from this task.
- Patient-level data, clinical notes, identifiers, and raw profiling output remain
  on the cluster to protect PHI. Ryan may return reviewed, non-identifying file
  inventories and aggregate reports for further work.
- Never describe cluster files as verified until Ryan provides the resulting
  inventory or report. Paths in legacy documentation are unverified leads.

This replaces earlier suggestions that the assistant might directly access the
cluster. Read this file before planning source access or implementing cluster jobs.

## Existing bb2238 OMOP boundary — user instruction, 2026-09-16

- Inspect the existing bb2238 OMOP mapping only; do not change, rerun, remap,
  overwrite or repair that dataset. Ryan wants its input lineage and mapping resolution.
- Any inspection reports go to a new directory under Ryan's own home, outside
  the bb2238 output. The assistant still never accesses the cluster directly.
