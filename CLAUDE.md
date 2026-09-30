# Active project guidance

## Write access (mandatory, applies to every agent)

- **Never write, modify, move or delete anything outside `/mnt/raid0/rbc58`**, except this git repository (`/home/rbc58/github/ecg-tte`: code and docs only, committed to `main`).
- **Everything else is read-only.** That includes:
  - `/mnt/nfs_*` (e.g. `nfs_yale_ecg`, `nfs_yale_ecg_signals`, `nfs_yale_echo`, `nfs_model_saves`);
  - other users' folders under `/mnt/raid0`;
  - all S3 buckets (e.g. `ukb-s3`, `biobank-mri-1`);
  - any other mounted data.
- **Where outputs go:** new directories under `/mnt/raid0/rbc58/ecg-tte/audits/<name>`, with umask 077.
- **Copying source data:** only into `/mnt/raid0/rbc58` and only when needed. Otherwise read it in place.
- **Patient data:** report aggregates only. Never print patient-level rows or identifiers, and suppress counts of 1–10. Restricted outputs (CSV/parquet with patient data) are never committed.

Follow [AGENTS.md](AGENTS.md), [README.md](README.md), and the
[restart plan](docs/RESTART_PLAN.md).

The previous implementation and its instructions are archived under
`archive/2026-09-09-legacy-v1/` for historical reference. The active project is a
new raw-JDAT-based multimodal trial-emulation benchmark. Do not resume the old
PARADIGM or 32-trial scripts as the new workflow.
