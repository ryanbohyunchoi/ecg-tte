# COMET with the project-wide index-date cut (index date ≤ 2024-06-30): sensitivity analysis

Written 2026-10-14.

- **Code:** `scripts/v1_comet_cut/comet_cut.py`. It imports the version 1 code unchanged: `scripts/v2_cohorts/grid.py`, `scripts/v1_ps10/ps10.py`, `scripts/v2_psclin_mi/psclin_mi.py` and `scripts/v21/paper2_grid.py`.
- **Outputs** (umask 077, not committed): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-comet-cut/`.
- No existing file was edited, and nothing was committed. This document reports aggregates only. Counts of 1–10 are suppressed.

## Plain-language summary

- **Why.** Every `trial_specs` cohort ends its index window on 2024-06-30. COMET's cohort comes from the JDAT roster (`claude-comet-progref-v1/roster`), not from a `trial_specs` builder, so this cut was never applied to it. Some COMET index dates fall after the end of the death data.
- **What was removed.** In the version 1 analysed COMET cohort (n = 6,381), the cut removes **78 patients (1.22%)**: 28 treated and 50 comparators. Fewer than 11 (< 0.17%) have an index date after 2024-12-31. In the roster (n = 7,499, before intersecting with the embeddings, phenotypes and panel), 111 patients (1.48%) fall after the cut.
- **Gate (exact).** With no cut, the code reproduces every version 1 COMET cell:
  - 220 cells: P1, P5, PS10, hdPS200 and clinical (with LVEF), each with 6 arms × 6 configurations, plus CLMBR32 in the main configuration, plus the 37 PS-Clinical (no LVEF) MI cells;
  - and the 185 per-draw MI cells;
  - in both PC modes;
  - 56,700 values, maximum deviation 0, 0 NaN mismatches.
- **Effect on the pooled results:** small. On paper 1's 32 trials (main configuration, 54 items), PS-CVD5 + ECG vs PS-CVD5 moves from 8.8% to **8.9%** with the version 1 PCs, or to **9.1%** with the PCs refit within the cut cohort. The other ladder rungs are unchanged at one decimal.
- **Lab deck.** Only the PS-CVD5 value changes at displayed precision: 8.8 → 8.9 (version 1 PCs) or 9.1 (refit PCs). PS-Demo 11.3, CVD10 5.0, hdPS 7.6 and PS-Clinical MI 3.2 are unchanged with version 1 PCs. With refit PCs PS-Demo becomes 11.4; the rest stay.

## 1. Design

| Element | Choice |
|---|---|
| Cut | `T.index_date <= 2024-06-30` (the roster index date), applied as a row subset of the version 1 analysed cohort `T.keys` |
| Other 37 trials | version 1 cells, unchanged |
| Rungs | P1 (PS-Demo), P5 (PS-CVD5, primary), PS10 (CVD10), hdPS200, clinical (with LVEF; gate only), clinical_nolvef 5-draw MI. Each design is built on the full cohort exactly as in version 1, then row-subset (as `grid.task`) |
| hdPS | `T.hd(200, t[rows], rows)`: levels re-ranked within the rows, as in the spec-v2 grid. 195 of the 200 selected levels are the same as in version 1 |
| MI | the existing version 1 imputed draws (`claude-v1-psclin-mi/imputation/restricted_completed_nolvef_v1_comet.parquet`; full-roster imputation, 5 draws) restricted to the kept rows. No re-imputation. Combined as `psclin_mi_v1.combine`: \|SMD\| averaged over draws, log HR by Rubin's rules |
| Arms | base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR × 6 configurations, plus CLMBR32 (main) for P1, P5, clinical and clinical_nolvef |
| PCs, variant 1 (`cut_v1pc`) | the version 1 PCs (`T.ecg_pc`, `T.clm_pc`) restricted to the kept rows |
| PCs, variant 2 (`cut_within`) | ECG 32 PCs and CLMBR-T 64 PCs refit within the cut cohort (`pcs(raw[rows], 64)`, memory layout kept as in `grid.subset`) |
| Placebo | the arm's PCs permuted within the rows, `default_rng(424242).permutation(len(rows))`. This equals `T.shuffle_perm` when nothing is removed (asserted) |
| Endpoints | as pipeline.md §6–7, via `paper2_grid._row` and `psclin_mi.load_F`, unchanged: leakage-corrected masks; 54 items; relative reduction with a 4,000-resample trial bootstrap (seed 20261001); exact sign-flip (one-sided for ECG vs base or placebo, two-sided for placebo vs base); \|Δ log HR\| sign-flip P and benchmark-permutation P (20,000 draws) |
| Sets | S32 (paper 1, primary), S38 |

## 2. Gate

| Check | Result |
|---|---|
| `gate_v1pc` and `gate_within` (no cut) vs the version 1 COMET cells: `claude-v21-paper2/core` (P1, P5, hdPS200, clinical), `claude-v1-ps10/cells` (PS10), clinical CLMBR32 from `claude-v1-psclin-nolvef`, MI from `claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet` | 220/220 cells each; **maximum deviation 0, 0 NaN mismatches**; key, ex58 and cell_failed identical |
| Per-draw MI cells vs `claude-v1-psclin-mi/cells/restricted_cells_v1.parquet` | 185/185 cells each; maximum deviation 0 |
| Pooled summary from the version 1 cells vs the existing `claude-v1-psclin-mi/summary/contrasts.csv` | 900 values; maximum deviation 1.8e-15 (floating-point round-off) |
| Pooled summary with the gate cells substituted for COMET vs version 1 | identical (deviation 0) |
| Privacy scan of the output csv/json files | clean |

Files: `cells/gate_status.json`, `cells/gate.csv`, `summary/summary_checks.json`, `privacy_scan.json`.

## 3. Share removed

| Population | n | Index date after 2024-06-30 | Index date after 2024-12-31 |
|---|---|---|---|
| Version 1 analysed COMET cohort | 6,381 | 78 (1.22%); treated 28, comparators 50 | < 11 (< 0.17%) |
| Roster (`claude-comet-progref-v1/roster`) | 7,499 | 111 (1.48%) | < 11 (< 0.15%) |

The analysed cohort's index years run from 2015 to 2025. The cut cohort has 6,303 patients (98.78%).

## 4. COMET itself (main configuration)

Mean \|SMD\| over the 54 items (45 for PS-Clinical, by its mask). RCT log HR = 0.187.

| Rung | Arm | mean \|SMD\| (v1 → cut v1 PCs / cut refit PCs) | log HR (v1 → cut v1 PCs / refit) | \|Δ log HR\| vs RCT (v1 → cut v1 PCs / refit) |
|---|---|---|---|---|
| PS-Demo | base | 0.147 → 0.149 / 0.149 | 0.180 → 0.165 / 0.165 | 0.007 → 0.021 / 0.021 |
| PS-Demo | + ECG | 0.114 → 0.117 / 0.111 | 0.225 → 0.199 / 0.190 | 0.038 → 0.013 / 0.003 |
| **PS-CVD5** | base | 0.147 → 0.158 / 0.158 | 0.186 → 0.174 / 0.174 | 0.000 → 0.012 / 0.012 |
| **PS-CVD5** | + ECG | 0.116 → 0.122 / 0.115 | 0.211 → 0.226 / 0.229 | 0.025 → 0.040 / 0.043 |
| CVD10 | base | 0.147 → 0.149 / 0.149 | 0.132 → 0.169 / 0.169 | 0.054 → 0.017 / 0.017 |
| CVD10 | + ECG | 0.115 → 0.118 / 0.119 | 0.245 → 0.224 / 0.178 | 0.059 → 0.037 / 0.008 |
| hdPS | base | 0.118 → 0.118 / 0.118 | 0.094 → 0.074 / 0.074 | 0.092 → 0.112 / 0.112 |
| hdPS | + ECG | 0.088 → 0.090 / 0.087 | 0.143 → 0.101 / 0.173 | 0.043 → 0.086 / 0.013 |
| PS-Clinical (no LVEF), MI | base | 0.150 → 0.151 / 0.151 | 0.119 → 0.128 / 0.128 | 0.067 → 0.059 / 0.059 |
| PS-Clinical (no LVEF), MI | + ECG | 0.109 → 0.110 / 0.109 | 0.193 → 0.180 / 0.193 | 0.007 → 0.007 / 0.007 |

COMET's own PS-CVD5 ECG gain grows from 21.0% to 22.9% (version 1 PCs) or 27.2% (refit PCs). Most of that comes from a worse-balanced PS-CVD5 base arm (0.147 → 0.158). The log HRs move by up to 0.07 (hdPS + ECG), which is the usual matching instability when 1% of rows are removed. Per-configuration values: `summary/per_trial_comet.csv`.

## 5. Pooled results (main configuration, 54 items; + ECG vs PS alone)

**S32 (paper 1's 32 trials, primary):**

| PS base | Cohort | mean \|SMD\| PS → + ECG | rel. reduction (95% CI) | better | P | \|Δ log HR\| PS → + ECG; closer; sign-flip P; perm. P |
|---|---|---|---|---|---|---|
| PS-Demo | v1 | 0.143 → 0.127 | 11.3% (6.0 to 16.1) | 26/32 | < .001 | 0.251 → 0.205; 20/32; .008; .26 |
| | cut, v1 PCs | 0.143 → 0.127 | 11.3% (6.0 to 16.0) | 26/32 | < .001 | 0.251 → 0.204; 21/32; .007; .25 |
| | cut, refit PCs | 0.143 → 0.127 | 11.4% (6.0 to 16.3) | 26/32 | < .001 | 0.251 → 0.204; 21/32; .007; .25 |
| **PS-CVD5** | v1 | 0.130 → 0.118 | **8.8% (4.4 to 13.3)** | 21/32 | < .001 | 0.226 → 0.196; 20/32; .049; .70 |
| | cut, v1 PCs | 0.130 → 0.119 | **8.9% (4.4 to 13.4)** | 21/32 | < .001 | 0.226 → 0.196; 20/32; .049; .68 |
| | cut, refit PCs | 0.130 → 0.118 | **9.1% (4.5 to 13.8)** | 21/32 | < .001 | 0.226 → 0.196; 20/32; .050; .68 |
| CVD10 | v1 | 0.121 → 0.115 | 5.0% (−0.8 to 10.3) | 23/32 | .051 | 0.208 → 0.171; 23/32; .008; .003 |
| | cut, v1 PCs | 0.121 → 0.115 | 5.0% (−0.8 to 10.3) | 23/32 | .051 | 0.207 → 0.170; 23/32; .009; .006 |
| | cut, refit PCs | 0.121 → 0.115 | 5.0% (−0.8 to 10.3) | 23/32 | .052 | 0.207 → 0.169; 24/32; .007; .006 |
| hdPS | v1 | 0.117 → 0.109 | 7.6% (1.7 to 13.0) | 22/32 | .008 | 0.181 → 0.167; 18/32; .20; .11 |
| | cut, v1 PCs | 0.117 → 0.109 | 7.6% (1.7 to 13.0) | 22/32 | .008 | 0.182 → 0.169; 18/32; .21; .14 |
| | cut, refit PCs | 0.117 → 0.109 | 7.6% (1.7 to 13.0) | 22/32 | .008 | 0.182 → 0.166; 18/32; .17; .073 |
| PS-Clinical (no LVEF), MI | v1 | 0.119 → 0.115 | 3.2% (−1.0 to 7.2) | 19/32 | .075 | 0.166 → 0.149; 22/32; .025; .002 |
| | cut, v1 PCs | 0.119 → 0.115 | 3.2% (−1.0 to 7.2) | 19/32 | .075 | 0.166 → 0.149; 22/32; .027; .003 |
| | cut, refit PCs | 0.119 → 0.115 | 3.2% (−1.0 to 7.3) | 19/32 | .075 | 0.166 → 0.149; 22/32; .027; .003 |

Unrounded PS-CVD5 values: 8.846% (v1), 8.950% (cut, v1 PCs), 9.112% (cut, refit PCs). hdPS with v1 PCs is 7.553%, which still rounds to 7.6.

**S38:** PS-CVD5 + ECG 9.0% (5.0 to 13.5) → 9.1% (5.1 to 13.6) / 9.3% (5.2 to 13.8). PS-Demo 12.6 → 12.6 / 12.7. CVD10 4.8 → 4.8 / 4.8. hdPS 7.6 → 7.6 / 7.6. PS-Clinical MI 3.6 → 3.6 / 3.7.

**Placebo contrasts (S32, main).**
- PS-CVD5, ECG vs permuted ECG: 8.0% → 7.9% / 8.1%.
- PS-CVD5, permuted ECG vs base: 1.0% → 1.2% / 1.1% (P ≥ .55).
- The other rungs' placebo contrasts move by ≤ 0.2 points.
- One CI bound crosses 0: CVD10's ECG vs permuted ECG goes from 6.1% (0.0 to 11.0) to 5.9% (−0.1 to 10.7). Its P stays at .021.

**PS-CVD5 + ECG in the other configurations (S32):**

| Configuration | v1 → cut v1 PCs / refit PCs |
|---|---|
| cal01 | 7.8 → 8.0 / 8.1 |
| 1:3 | 6.4 → 6.4 / 6.4 |
| IPTW | 4.8 → 4.9 / 4.9 |
| overlap | 7.4 → 7.4 / 7.4 |
| gbm | −1.1 → −1.0 / −0.9 |

All P values are essentially unchanged. Full table: `summary/contrasts.csv`, with columns `cohort` = v1 / gate_v1pc / cut_v1pc / cut_within.

## 6. Lab deck numbers

| Deck number | v1 | cut, v1 PCs | cut, refit PCs | Changes at displayed precision? |
|---|---|---|---|---|
| PS-CVD5 + ECG (headline) | 8.8 | 8.9 | 9.1 | **yes** (+0.1 / +0.3) |
| Ladder: PS-Demo | 11.3 | 11.3 | 11.4 | only with refit PCs |
| Ladder: PS-CVD5 | 8.8 | 8.9 | 9.1 | yes |
| Ladder: CVD10 | 5.0 | 5.0 | 5.0 | no |
| Ladder: hdPS | 7.6 | 7.6 | 7.6 | no |
| Ladder: PS-Clinical (no LVEF), MI | 3.2 | 3.2 | 3.2 | no |

None of the conclusions changes: no significance status flips, and the ladder ordering is unchanged.

## 7. Files

`/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-comet-cut/`:
- `share.json`;
- `cells/`:
  - `restricted_cells_<variant>.parquet`: 220 COMET cells per variant, in the version 1 column layout, MI in the v1 layout;
  - `restricted_cells_<variant>_draws.parquet`;
  - `log.json`, `gate.csv`, `gate_status.json`;
- `summary/`: `contrasts.csv`, `per_trial_comet.csv`, `ladder.csv`, `check_vs_v1_mi_summary.csv`, `summary_checks.json`;
- `privacy_scan.json`;
- `logs/`.
