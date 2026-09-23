# Project operating instructions

## Primary workspace: HIPAA Claude Code container — user instruction, 2026-09-23

**Supersedes the 2026-09-09 access rule below for sessions in the HIPAA-compliant
Claude Code container.** Ryan: "we will mainly be working on this container".
- The assistant may read all mounted data and run analyses and GPU jobs directly.
- Writes go only under `/mnt/raid0/rbc58` and `/home/rbc58/github`. Run outputs go to
  fresh `/mnt/raid0/rbc58/ecg-tte/audits/<name>/` directories (`umask 077`), and
  never overwrite existing runs.
- Chat, logs and Git still get aggregates only. No identifiers, note text, record
  examples or patient-specific dates.
- Repository: `/home/rbc58/github/ecg-tte`. The remote uses SSH
  (`git@github.com:ryanbohyunchoi/ecg-tte.git`); the Cursor HTTPS askpass socket is
  not available in the container. **Push working branches regularly.** Treat the
  container home as potentially non-persistent; `/mnt/raid0` is persistent.
- Python envs: analysis `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`;
  BCL/torch `/mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-zZ5FVVsd/env/bin/python`;
  R `/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env`. micromamba is at
  `/mnt/raid0/rbc58/ecg-tte/software/mm/bin/micromamba`.
- Check `nvidia-smi` before GPU jobs and use only idle devices.

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

- Ryan's specified project output root is `/mnt/raid0/rbc58/ecg-tte/`.
  Audit runs use its `audits/` subdirectory. This replaces the assistant-proposed
  sibling directory `ecg-tte-audits`; do not use that older location for new runs.
- Write all new project audit reports and run-specific temporary counting databases
  beneath `/mnt/raid0/rbc58/ecg-tte/audits/`, not directly in `$HOME`.
- Create a fresh private subdirectory for each run (`umask 077`); never overwrite
  an existing run or mix reports with raw JDAT or existing OMOP datasets.
- This supersedes the earlier home-directory report destination. Source paths and
  the repository checkout location are unchanged.
- Ryan performs cluster relocation and execution. Move only known project audit
  directories, after their jobs stop; skip symlinks and existing destinations.

## Shared source snapshots — user direction, 2026-09-21

- Build trial-independent source tables under `/mnt/raid0/rbc58/ecg-tte/shared/`.
  Each build uses a new private snapshot directory. This is separate from audits.
- Preserve all source rows/values and raw files; cohort filters belong downstream.
- Reuse completed tables only through compatible manifests and integrity checks.
  No patient-level tables or raw values enter Git or chat.
