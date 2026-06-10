"""
ecg-tte-prep/stage3_filter.py

Stage 3: Fast filter — apply configurable I/E criteria, adherence,
and ECG selection to the cached pool. Runs in < 1 minute. No OMOP reads.
Template for 32-trial pipeline; override arm names and criteria per trial via YAML.

Output goes to --output-dir/runs/{run_name}/:
  comet_cohort.parquet — filtered cohort with SMD-ready covariate columns
  attrition.csv        — n-after each filter step
  filter_manifest.json — all CLI args, seed, git SHA, timestamp

Can also accept --config path/to/yaml (CLI args override YAML values).

Usage:
    python trialemulation/methods/comet/filter_comet.py \\
        --pool-dir  /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/pool \\
        --output-dir /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet \\
        --run-name  default

Sensitivity (no CCB exclusion, looser EF):
    python ... --config configs/comet_lenient.yaml

All knobs are documented in the argparser help strings.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml  # PyYAML

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cohort_utils import METOPROLOL, drug_mask, safe_hr_from_rr


# ── Attrition logger ─────────────────────────────────────────────────────────

class Attrition:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def log(self, df: pd.DataFrame, step: str) -> pd.DataFrame:
        counts = df["arm"].value_counts().to_dict() if "arm" in df.columns else {}
        row = {"step": step, "n_total": len(df)}
        row.update({f"n_{arm}": int(n) for arm, n in counts.items()})
        self.rows.append(row)
        count_str = "  ".join(f"{arm}={n:>6,}" for arm, n in counts.items())
        print(f"  [{step:<45}] n={len(df):>7,}  {count_str}")
        return df

    def to_csv(self, path: Path) -> None:
        pd.DataFrame(self.rows).to_csv(path, index=False)


# ── ECG selection ─────────────────────────────────────────────────────────────

def select_ecg(
    pool: pd.DataFrame,
    ecg_cands: pd.DataFrame,
    window_days: int,
    mode: str,           # "before" or "symmetric"
    forward_days: int = 30,
) -> pd.DataFrame:
    """
    Select one ECG per patient from ecg_candidates.
    Returns pool with added columns: selected_ecg_fileID, selected_ecg_days_from_index,
    and updated RR_Interval, PR_Interval, QRS_Duration, hr_at_index.

    mode='before':    select nearest ECG in [-window_days, 0]
    mode='symmetric': select nearest ECG in [-window_days, +forward_days]
    """
    cands = ecg_cands.copy()
    if mode == "before":
        cands = cands[
            (cands["days_from_index"] >= -window_days) &
            (cands["days_from_index"] <= 0)
        ]
    else:  # symmetric
        cands = cands[
            (cands["days_from_index"] >= -window_days) &
            (cands["days_from_index"] <= forward_days)
        ]

    if cands.empty:
        pool["selected_ecg_fileID"]             = pd.NA
        pool["selected_ecg_days_from_index"]    = pd.NA
        return pool

    # Nearest = minimal |days_from_index|
    cands = cands.copy()
    cands["abs_days"] = cands["days_from_index"].abs()
    best = (cands.sort_values("abs_days")
            .groupby("MRN", sort=False)
            .first()
            .reset_index()
            .rename(columns={"fileID": "selected_ecg_fileID",
                              "days_from_index": "selected_ecg_days_from_index"}))

    # Drop old ECG columns from pool (will be replaced by selected values)
    drop_cols = ["ecg_file_id", "ecg_days_from_index",
                 "RR_Interval", "PR_Interval", "QRS_Duration", "hr_at_index"]
    pool = pool.drop(columns=[c for c in drop_cols if c in pool.columns])

    ecg_cols = ["MRN", "selected_ecg_fileID", "selected_ecg_days_from_index"]
    for col in ["RR_Interval", "PR_Interval", "QRS_Duration",
                "QTc", "QT_Interval", "QRS_Axis", "P_Axis", "T_Axis"]:
        if col in best.columns:
            ecg_cols.append(col)

    pool = pool.merge(best[ecg_cols], on="MRN", how="left")
    pool["hr_at_index"] = safe_hr_from_rr(pool.get("RR_Interval"))
    return pool


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="COMET Stage 3: fast filter on cached pool"
    )
    p.add_argument("--pool-dir",   required=True,
                   help="Directory containing pool.parquet + ecg_candidates.parquet")
    p.add_argument("--output-dir", required=True,
                   help="Base output dir; results go to <output-dir>/runs/<run-name>/")
    p.add_argument("--run-name",   default="default")
    p.add_argument("--config",     default=None,
                   help="Optional YAML config; CLI args override YAML values")
    p.add_argument("--cohort-filename", default="comet_cohort.parquet",
                   help="Output cohort filename (default: comet_cohort.parquet). "
                        "Use {trial_key}_cohort.parquet for multi-trial runs.")

    # Inclusion
    inc = p.add_argument_group("Inclusion criteria")
    inc.add_argument("--require-hfref",  type=lambda s: s.lower() != "false",
                     default=True,
                     help="Require HFrEF (EF≤lvef-max OR ICD I50.2x/I50). "
                          "COMET-specific — non-HF trials should set "
                          "'require-hfref: false' in their YAML config.")
    inc.add_argument("--lvef-max",       type=float, default=40.0)
    inc.add_argument("--ef-source",      default="echo_or_icd",
                     choices=["echo_or_icd", "echo_only"])
    inc.add_argument("--age-min",        type=float, default=18.0)
    inc.add_argument("--age-max",        type=float, default=80.0)
    inc.add_argument("--min-index-date", default="1997-09-01",
                     help="Earliest allowable index date (default 1997-09-01: FDA carvedilol "
                          "HF approval). Pass '' to disable.")
    inc.add_argument("--require-hf-proxy", type=lambda s: s.lower() != "false",
                     default=False,
                     help="Require NYHA proxy (I50 in 12m OR loop diuretic in 90d). "
                          "Disabled by default: HFrEF criterion (EF≤lvef-max OR I50.2x) "
                          "already guarantees HF diagnosis.")
    inc.add_argument("--require-acei-arb", type=lambda s: s.lower() != "false",
                     default=False,
                     help="Require ACEi or ARB in 90d before index (COMET criterion I4)")
    inc.add_argument("--meto-formulation", default="all",
                     choices=["all", "tartrate_only"],
                     help="'tartrate_only' requires metoprolol tartrate vs succinate")

    # Adherence
    adh = p.add_argument_group("Drug adherence")
    adh.add_argument("--min-fills",             type=int,   default=2)
    adh.add_argument("--persistence-days",      type=int,   default=90)
    adh.add_argument("--drugclass-lookback-days", type=int, default=365,
                     help="Naive new-user lookback: no carv/meto in prior N days")
    adh.add_argument("--drop-early-adverse-disc", type=lambda s: s.lower() != "false",
                     default=True)

    # Exclusions
    exc = p.add_argument_group("Exclusion criteria")
    exc.add_argument("--exclude-ccb",            type=lambda s: s.lower() != "false",
                     default=True,
                     help="Exclude concurrent verapamil/diltiazem (COMET E7). "
                          "DEFAULT TRUE — faithful to COMET. Use --exclude-ccb false "
                          "for sensitivity analysis.")
    exc.add_argument("--exclude-other-bb",       type=lambda s: s.lower() != "false",
                     default=True)
    exc.add_argument("--exclude-recent-mi",      type=lambda s: s.lower() != "false",
                     default=True)
    exc.add_argument("--exclude-av-block",       type=lambda s: s.lower() != "false",
                     default=True)
    exc.add_argument("--exclude-esrd",           type=lambda s: s.lower() != "false",
                     default=True)
    exc.add_argument("--exclude-hepatic-failure", type=lambda s: s.lower() != "false",
                     default=True)
    exc.add_argument("--exclude-valvular",       type=lambda s: s.lower() != "false",
                     default=False)

    # ECG selection
    ecg = p.add_argument_group("ECG selection")
    ecg.add_argument("--ecg-window-days",  type=int,   default=60,
                     help="ECG window in days relative to index date (default 60)")
    ecg.add_argument("--ecg-window-mode",  default="before",
                     choices=["before", "symmetric"],
                     help="'before': ECG in [-window, 0]; "
                          "'symmetric': ECG in [-window, +30d]")
    ecg.add_argument("--ecg-required",     type=lambda s: s.lower() != "false",
                     default=False,
                     help="Drop patients without an ECG in the window (default False)")

    # Misc
    p.add_argument("--followup-days", type=int, default=1825)
    p.add_argument("--seed",          type=int, default=42)

    # Outcome recompute (Lever 2)
    out_grp = p.add_argument_group("Outcome recompute (requires death_date in pool)")
    out_grp.add_argument("--censor-date", default="",
                         help="Administrative censor date (YYYY-MM-DD). If set, recomputes "
                              "event_death/time_to_death from death_date using this cutoff. "
                              "Default '' = use pool values as-is. Set to death-table max date "
                              "to recover deaths missed by the hardcoded 2024-12-31 cutoff.")
    out_grp.add_argument("--max-followup-days", type=int, default=0,
                         help="Override follow-up cap (days). 0 = keep pool value. If > 0 and "
                              "--censor-date is set, applied after date-based censoring. "
                              "Run a sweep (1095/1825/2555/3650) to test HR stability.")
    return p.parse_args()


def _merge_yaml(args: argparse.Namespace, config_path: str) -> argparse.Namespace:
    """Merge YAML defaults under CLI values (CLI wins on conflict)."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}
    defaults = vars(args)
    cli_provided = set(sys.argv)
    for k, v in cfg.items():
        key = k.replace("-", "_")
        # Only apply YAML value if the user didn't explicitly pass the flag on CLI
        flag_str = f"--{k}"
        if flag_str not in cli_provided and key in defaults:
            setattr(args, key, v)
    args._yaml_cfg = cfg
    return args


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    if args.config:
        args = _merge_yaml(args, args.config)

    pool_dir = Path(args.pool_dir)
    run_dir  = Path(args.output_dir) / "runs" / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── Load pool ─────────────────────────────────────────────────────────────
    pool_path = pool_dir / "pool.parquet"
    if not pool_path.exists():
        raise FileNotFoundError(f"pool.parquet not found at {pool_path}. "
                                "Run make_comet.py first.")
    pool = pd.read_parquet(pool_path)
    pool["index_date"] = pd.to_datetime(pool["index_date"])
    print(f"Pool loaded: {len(pool):,} candidates")

    cands_path = pool_dir / "ecg_candidates.parquet"
    ecg_cands = pd.read_parquet(cands_path) if cands_path.exists() else pd.DataFrame()

    attrition = Attrition()
    attrition.log(pool, "Pool (pre-filter)")

    # ── 1. Age ────────────────────────────────────────────────────────────────
    pool = pool[(pool["age_at_index"] >= args.age_min) &
                (pool["age_at_index"] <= args.age_max)]
    attrition.log(pool, f"Age {int(args.age_min)}–{int(args.age_max)}")

    # ── 1b. Calendar time gate ────────────────────────────────────────────────
    if args.min_index_date:
        pool = pool[pool["index_date"] >= pd.Timestamp(args.min_index_date)]
        attrition.log(pool, f"Index date >= {args.min_index_date}")

    # ── 1c. Required ICD inclusion (trial population gate, e.g. dm_icd_ever) ──
    # Computed as columns by stage1_build_pool.py from inclusion.required_icd;
    # ANDed here. Column-existence-guarded since not every pool has every flag.
    required_icd = getattr(args, "_yaml_cfg", {}).get("inclusion", {}).get("required_icd", [])
    for icd_spec in required_icd:
        col = icd_spec["name"]
        if col not in pool.columns:
            print(f"  NOTE: {col} not in pool — required_icd inclusion skipped")
            continue
        pool = pool[pool[col] == 1]
        attrition.log(pool, f"Required ICD: {col}")

    # ── 2. Naive new-user lookback ─────────────────────────────────────────────
    # For each arm: no dispense of any OTHER arm's drug in prior lookback_days.
    # prior_<other_arm>_days columns are produced by identify_arms_generic (Stage 1)
    # for every arm pair, keyed by the actual arm names from the trial config.
    lookback = args.drugclass_lookback_days
    arm_values = pool["arm"].dropna().unique().tolist()
    keep = pd.Series(False, index=pool.index)
    for arm_val in arm_values:
        ok = pool["arm"] == arm_val
        for other in arm_values:
            if other == arm_val:
                continue
            col = f"prior_{other}_days"
            if col in pool.columns:
                ok = ok & (pool[col].isna() | (pool[col] > lookback))
        keep = keep | ok
    pool = pool[keep]
    attrition.log(pool, f"Naive new-user lookback ≤ {lookback}d")

    # ── 3. Drug adherence ──────────────────────────────────────────────────────
    pd_days = args.persistence_days
    if pd_days in (90, 180, 365):
        refill_col = f"n_refills_assigned_{pd_days}d"
    else:
        # Nearest pre-computed window (conservative: round down)
        nearest = max(w for w in [90, 180, 365] if w <= pd_days) if pd_days > 90 else 90
        refill_col = f"n_refills_assigned_{nearest}d"
        print(f"  NOTE: persistence_days={pd_days} not pre-computed; "
              f"using {refill_col} as proxy (conservative)")

    if refill_col in pool.columns:
        pool = pool[pool[refill_col] >= args.min_fills]
        attrition.log(pool, f"Adherence ≥{args.min_fills} fills in {pd_days}d")
    else:
        print(f"  WARNING: {refill_col} not in pool — adherence filter skipped")

    # ── 3b. Early adverse discontinuation ─────────────────────────────────────
    if args.drop_early_adverse_disc and "early_adverse_disc" in pool.columns:
        pool = pool[pool["early_adverse_disc"] == 0]
        attrition.log(pool, "Drop early adverse discontinuation")

    # ── 4. HFrEF inclusion (COMET-specific; non-HF trials set require-hfref: false) ──
    # Mirrors PARADIGM: EF ≤ lvef_max OR I50.2x (systolic HF subcoded).
    # Pool has hfref_icd_subcoded_i502_24m (I50.2x, 24m) — nearest available to
    # PARADIGM's 5yr window; falls back to hfref_icd_5y (any I50) if absent.
    if not args.require_hfref:
        print("  NOTE: require_hfref=False — HFrEF inclusion criterion skipped")
    elif args.ef_source == "echo_only":
        ef_mask = pool["ef_at_index"].notna() & (pool["ef_at_index"] <= args.lvef_max)
        pool = pool[ef_mask]
        attrition.log(pool, f"HFrEF EF≤{args.lvef_max}% (echo only)")
    else:  # echo_or_icd
        echo_ok = pool["ef_at_index"].notna() & (pool["ef_at_index"] <= args.lvef_max)
        if "hfref_icd_subcoded_i502_24m" in pool.columns:
            icd_ok = pool["hfref_icd_subcoded_i502_24m"] == 1
            icd_label = "I50.2x 24m"
        elif "hfref_icd_5y" in pool.columns:
            icd_ok = pool["hfref_icd_5y"] == 1
            icd_label = "I50 5yr"
            print("  NOTE: hfref_icd_subcoded_i502_24m not in pool — "
                  "falling back to hfref_icd_5y (any I50, 5yr)")
        else:
            icd_ok = pd.Series(False, index=pool.index)
            icd_label = "no ICD column"
            print("  NOTE: no hfref_icd_* column in pool — ICD arm of "
                  "HFrEF criterion skipped (echo only)")
        pool = pool[echo_ok | icd_ok]
        attrition.log(pool, f"HFrEF EF≤{args.lvef_max}% OR {icd_label} (echo_or_icd)")

    # ── 5. HF proxy (NYHA surrogate) ──────────────────────────────────────────
    if args.require_hf_proxy:
        hf_proxy = (pool["prior_hf_code_1yr"] == 1) | (pool["loop_diuretic_90d"] == 1)
        pool = pool[hf_proxy]
        attrition.log(pool, "HF proxy (I50 in 12m OR loop diuretic in 90d)")

    # ── 6. ACEi/ARB requirement (optional) ────────────────────────────────────
    if args.require_acei_arb:
        pool = pool[pool["acei_arb_90d"] == 1]
        attrition.log(pool, "ACEi or ARB in 90d (COMET I4)")

    # ── 7. Metoprolol formulation ──────────────────────────────────────────────
    # tartrate_only: read drug_master_pool.parquet (saved by Stage 1) and
    # determine each metoprolol patient's index-date fill formulation.
    # Succinate = drug_upper contains SUCCINATE, TOPROL, or word-boundary XL.
    # Tartrate  = metoprolol fill that is NOT succinate.
    if args.meto_formulation == "tartrate_only":
        dm_pool_path = pool_dir / "drug_master_pool.parquet"
        if not dm_pool_path.exists():
            print("  WARNING: drug_master_pool.parquet not found in pool_dir — "
                  "tartrate_only filter skipped. Ensure Stage 1 completed successfully.")
        else:
            import re as _re
            dm_pool = pd.read_parquet(dm_pool_path)
            dm_pool["_date"] = pd.to_datetime(dm_pool["_date"], errors="coerce")

            def _is_succinate(s: pd.Series) -> pd.Series:
                return (
                    s.str.contains("SUCCINATE", regex=False, na=False) |
                    s.str.contains("TOPROL",    regex=False, na=False) |
                    s.str.contains(r"\bXL\b",   regex=True,  na=False)
                )

            meto_pool = dm_pool[drug_mask(dm_pool["drug_upper"], METOPROLOL)].copy()
            meto_patients = pool.loc[pool["arm"] == "metoprolol", ["MRN", "index_date"]].copy()
            meto_patients["MRN"] = meto_patients["MRN"].astype(str)
            meto_pool["MRN"]     = meto_pool["MRN"].astype(str)

            # Join on MRN; keep only fills on the index date (= first meto fill by construction)
            merged = meto_patients.merge(
                meto_pool[["MRN", "drug_upper", "_date"]], on="MRN", how="left"
            )
            idx_fills = merged[merged["_date"] == merged["index_date"]].copy()

            # A patient is "succinate" if any index-date fill matches the succinate pattern
            succ_mrns = set(
                idx_fills.loc[_is_succinate(idx_fills["drug_upper"]), "MRN"].unique()
            )
            n_succ = len(succ_mrns)
            n_tart = int((pool["arm"] == "metoprolol").sum()) - n_succ
            print(f"  Metoprolol formulation: tartrate={n_tart:,}  succinate={n_succ:,}")

            pool = pool[~(
                (pool["arm"] == "metoprolol") &
                pool["MRN"].astype(str).isin(succ_mrns)
            )]
            attrition.log(pool, "Metoprolol tartrate only (excl. succinate/Toprol/XL)")

    # ── 8. Exclusions (COMET-specific cardiac covariates; skipped with NOTE if
    #      a trial's pool doesn't carry the column) ────────────────────────────
    def _exclude(flag: bool, cols: list[str], mask_fn, label: str) -> None:
        nonlocal pool
        if not flag:
            return
        missing = [c for c in cols if c not in pool.columns]
        if missing:
            print(f"  NOTE: {', '.join(missing)} not in pool — '{label}' exclusion skipped")
            return
        pool = pool[mask_fn(pool)]
        attrition.log(pool, label)

    _exclude(args.exclude_ccb, ["had_ccb_nondihydro_pm30d"],
             lambda p: p["had_ccb_nondihydro_pm30d"] == 0,
             "Exclude CCB (verapamil/diltiazem ±30d)")

    _exclude(args.exclude_other_bb, ["had_other_bb_pm30d"],
             lambda p: p["had_other_bb_pm30d"] == 0,
             "Exclude other β-blocker ±30d")

    _exclude(args.exclude_recent_mi, ["recent_mi_acs_60d", "recent_revasc_60d"],
             lambda p: (p["recent_mi_acs_60d"] == 0) & (p["recent_revasc_60d"] == 0),
             "Exclude recent MI/ACS/revasc (60d)")

    _exclude(args.exclude_av_block, ["av_block_2_3_24m"],
             lambda p: p["av_block_2_3_24m"] == 0,
             "Exclude 2nd/3rd-degree AV block (24m)")

    _exclude(args.exclude_esrd, ["esrd_5y"],
             lambda p: p["esrd_5y"] == 0,
             "Exclude ESRD/advanced CKD (5yr)")

    _exclude(args.exclude_hepatic_failure, ["hepatic_failure_5y"],
             lambda p: p["hepatic_failure_5y"] == 0,
             "Exclude severe hepatic failure (5yr)")

    _exclude(args.exclude_valvular, ["valvular_disease_5y"],
             lambda p: p["valvular_disease_5y"] == 0,
             "Exclude valvular heart disease (5yr)")

    # ── 9. ECG selection ──────────────────────────────────────────────────────
    if not ecg_cands.empty:
        # Restrict ecg_cands to current pool only
        pool_mrns = set(pool["MRN"].astype(str).unique())
        ecg_pool  = ecg_cands[ecg_cands["MRN"].astype(str).isin(pool_mrns)]
        pool = select_ecg(
            pool, ecg_pool,
            window_days=args.ecg_window_days,
            mode=args.ecg_window_mode,
        )
        n_ecg = pool["selected_ecg_fileID"].notna().sum()
        print(f"  ECG matched within {args.ecg_window_mode} {args.ecg_window_days}d: "
              f"{n_ecg:,}/{len(pool):,}")

    if args.ecg_required:
        pool = pool[pool["selected_ecg_fileID"].notna()]
        attrition.log(pool, f"ECG required within {args.ecg_window_days}d ({args.ecg_window_mode})")

    # ── 9b. Outcome recompute (if --censor-date or --max-followup-days set) ──────
    # Mirrors the make_comet.py death block exactly — safe to re-run because
    # death_date (raw) is always in the pool. This lets us extend the follow-up
    # window or correct a stale censor cutoff without a full Stage-1 re-run.
    if (args.censor_date or args.max_followup_days > 0) and "death_date" in pool.columns:
        pool["death_date"] = pd.to_datetime(pool["death_date"], errors="coerce")
        if args.censor_date:
            end_date = pd.Timestamp(args.censor_date)
        else:
            # No explicit date provided — derive from pool's current event_death
            # to keep censoring consistent; only cap changes.
            end_date = pool["death_date"].max()
            if pd.isna(end_date):
                end_date = pd.Timestamp("2024-12-31")
        pool["event_death"] = pool["death_date"].notna().astype(int)
        pool["death_date_censored"] = pool["death_date"].fillna(end_date)
        pool["time_to_death"] = (
            pool["death_date_censored"] - pool["index_date"]
        ).dt.days.clip(lower=0)
        cap = args.max_followup_days if args.max_followup_days > 0 else 1825
        pool.loc[pool["time_to_death"] > cap, "event_death"]   = 0
        pool.loc[pool["time_to_death"] > cap, "time_to_death"] = cap
        n_ev = int(pool["event_death"].sum())
        print(f"  [outcome recompute] censor={end_date.date()}  cap={cap}d  "
              f"events={n_ev:,}/{len(pool):,}")

    # ── 10. Build clean covariate columns for analysis ─────────────────────────
    # Rename pool columns to match SMD_COLS / analyze_comet.py expectations
    rename_map = {
        "loop_diuretic_90d":     "loop_diuretic",
        "acei_arb_90d":          "acei_arb",
        "aldosterone_antag_90d": "aldosterone_antag",
    }
    for old, new in rename_map.items():
        if old in pool.columns and new not in pool.columns:
            pool = pool.rename(columns={old: new})

    # sex_binary: needed by analyze_comet.py (computed from sex if not present)
    if "sex_binary" not in pool.columns:
        pool["sex_binary"] = (pool["sex"] == "F").astype(int)

    # hr_at_index: compute/recompute to ensure no inf values
    if "RR_Interval" in pool.columns:
        pool["hr_at_index"] = safe_hr_from_rr(pool["RR_Interval"])

    # ── 11. Final column selection ─────────────────────────────────────────────
    OUTPUT_COLS = [
        "person_id", "MRN", "arm", "index_date",
        # Demographics
        "age_at_index", "sex", "sex_binary", "race_black",
        # Echo
        "ef_at_index",
        # ECG
        "RR_Interval", "PR_Interval", "QRS_Duration", "hr_at_index",
        # Comorbidities
        "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
        # Medications
        "loop_diuretic", "acei_arb", "aldosterone_antag",
        # HF severity
        "prior_hf_code_1yr",
        # Therapy
        "days_on_therapy",
        # ECG selection
        "selected_ecg_fileID", "selected_ecg_days_from_index",
        # Outcomes
        "event_death", "time_to_death", "death_date",
    ]
    out_cols = [c for c in OUTPUT_COLS if c in pool.columns]
    cohort = pool[out_cols].drop_duplicates("person_id").reset_index(drop=True)

    attrition.log(cohort, "Final cohort")

    # ── Save ──────────────────────────────────────────────────────────────────
    cohort_filename = getattr(args, "cohort_filename", "comet_cohort.parquet")
    cohort_path = run_dir / cohort_filename
    cohort.to_parquet(cohort_path, index=False)

    attrition_path = run_dir / "attrition.csv"
    attrition.to_csv(attrition_path)

    # ── Manifest ──────────────────────────────────────────────────────────────
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        git_sha = "unknown"

    arm_counts = cohort["arm"].value_counts().to_dict()
    manifest = {
        "filtered_at": datetime.now().isoformat(),
        "git_sha":     git_sha,
        "run_name":    args.run_name,
        "args":        vars(args),
        "final_n":     len(cohort),
        "arm_counts":  {arm: int(n) for arm, n in arm_counts.items()},
        "n_events":     int(cohort["event_death"].sum()),
        "n_with_ecg":   int(cohort["selected_ecg_fileID"].notna().sum()) if "selected_ecg_fileID" in cohort.columns else 0,
    }
    with open(run_dir / "filter_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Filtered cohort — run: {args.run_name}")
    for arm, n in arm_counts.items():
        print(f"  {arm:<12}: {n:,}")
    print(f"  Events     : {manifest['n_events']:,}")
    print(f"  With ECG   : {manifest['n_with_ecg']:,}")
    print(f"  Saved → {run_dir}")
    print(f"{'='*60}")
    print("\nNext: run analyze_comet.py with --cohort and --embed-dir")


if __name__ == "__main__":
    main()
