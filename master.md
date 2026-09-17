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
- Inspection reports stay outside the bb2238 output. Use the audit root below.
  The assistant still never accesses the cluster directly.

## Cluster output location — user instruction, 2026-09-17

- Write all new project audit reports and run-specific temporary counting databases
  beneath `/mnt/raid0/rbc58/ecg-tte-audits/`, not directly in `$HOME`.
- Create a fresh private subdirectory for each run (`umask 077`); never overwrite
  an existing run or mix reports with raw JDAT or existing OMOP datasets.
- This supersedes the earlier home-directory report destination. Source paths and
  the repository checkout location are unchanged.
- Ryan performs cluster relocation and execution. Move only known project audit
  directories, after their jobs stop; skip symlinks and existing destinations.
