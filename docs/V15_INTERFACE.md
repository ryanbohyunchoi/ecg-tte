# v1.5 per-trial file interface (MIMIC-IV and UK Biobank)

Every trial directory is `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-<cohort>-<trial>/`, where
`cohort` is `mimic` or `ukb`. It is private (umask 077) and contains restricted data. The
directory holds these files:

| File | Content |
|---|---|
| `cohort.parquet` | `pid` (string), `treated` (int: 1 = first arm as listed in `rct.json`), `index_day` (float: days from an arbitrary per-person origin; only differences are used), `index_year` (int or float; MIMIC: anchor-year group midpoint) |
| `baseline.parquet` | `pid` plus covariate columns (float; NaN = missing) |
| `roles.json` | `{"demo": [...], "dx": [...], "meds": [...], "labs_vitals": [...], "util": [...], "phys": [...]}`. **Sparse** = demo + dx. **Clinical** = demo + dx + meds + labs_vitals + util. **phys** is the subset of labs_vitals treated as physiology in the plasmode. |
| `panel.parquet` | `pid` plus count features in the 365 days before index (index-day orders are excluded for rx). Column names use the prefixes `dx_` (3-character ICD-10, or ICD-9 mapped), `rx_` (lower-case ingredient token), `px_` (procedure code) and `lab_` (lab-test-ordered flag). **Exposure-defining tokens of either arm must NOT appear.** |
| `panel_dictionary.csv` | `feature, domain`; domain ∈ `dx, rx, px, lab` |
| `ecg_embedding.parquet` | `pid`, `embedding` (list of 256 floats from the BCL checkpoint), `lag_days` (index minus ECG day, ≥ 0). One row per pid, the latest ECG in the window. |
| `outcomes.parquet` | `pid`, `t` (days, > 0; index-day events at 0.5), `e` (0/1), for the primary outcome **already truncated at the protocol horizon**. Optional: `t_nco_<name>`, `e_nco_<name>`. |
| `rct.json` | `{"trial": ..., "key": <trial_specs key or null>, "arms": [first, second], "hr": ..., "lo": ..., "hi": ..., "ci_level": 0.95, "our_orientation": <HR expressed as first-arm vs second-arm>, "horizon_days": ..., "endpoint": ..., "notes": ...}` |
| `summary.json` | **Aggregate only:** attrition (cells < 11 suppressed), arm sizes, event counts (suppressed), ECG coverage, date ranges, notes |
| `clmbr_embedding.parquet` | Optional (UKB): `pid`, `embedding` |

**Status markers.** The cohort agent writes `READY_COHORT` after cohort, baseline, roles, panel,
dictionary and `summary.json`. The ECG agent writes `READY_ECG` after `ecg_embedding.parquet`.
Outcomes are written, and `READY_OUTCOMES` set, only after the feasibility rule has passed
(≥ 200 per arm with an ECG). The analysis engine (`scripts/v15/v15_analyze.py`) consumes the
directory once all three markers are present.
