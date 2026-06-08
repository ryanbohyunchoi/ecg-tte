"""
scripts/stage1_build_pool.py

Stage 1: Wide Candidate Pool Builder — config-driven, multi-trial.

Builds a maximally permissive pool of all arm-drug initiators with every
covariate and flag needed for downstream filtering and analysis.
Run ONCE per trial per data refresh. Output cached in pool/ directory.

Architecture:
  Driven by a per-trial YAML config (--config). Trial-specific arm definitions,
  I/E criteria, covariates, and endpoint are declared in the config. Shared
  helpers live in cohort_utils.py.

  Config-driven stage1 supports any two-arm active-comparator design.
  "drug_vs_no_drug" (placebo control) is NOT YET supported (requires a
  non-drug index anchor; raises NotImplementedError).

Output directory: {--output-root}/{trial.key}/pool/
  pool.parquet                — full candidate pool with all covariates
  drug_master_pool.parquet    — drug records for pool patients
  conditions_pool.parquet     — condition records for pool patients
  ecg_candidates.parquet      — all ECGs within ±pool_window_days of index
  build_manifest.json         — run metadata (git SHA, paths, arm counts, etc.)

Backward-compatibility (COMET):
  Running with configs/comet.yaml produces output columns identical to the
  original COMET-specific stage1. Columns first_carv_date, prior_meto_days, etc.
  are preserved via stage3_alias in the YAML.

Usage:
    python scripts/stage1_build_pool.py \\
        --config           configs/comet.yaml \\
        --person-parquet   /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \\
        --condition-dir    /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \\
        --drug-master      /mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet \\
        --echo-meta        /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \\
        --ecg-meta         /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \\
        --death-parquet    /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \\
        --output-root      /home/rbc58/mnt/ecg-tte

    # With composite endpoint (visit/procedure tables):
    python scripts/stage1_build_pool.py \\
        --config configs/paradigm.yaml \\
        ... \\
        --visit-dir     /home/rbc58/mnt/ascvd/omop_database/visit_occurrence \\
        --procedure-dir /home/rbc58/mnt/ascvd/omop_database/procedure_occurrence

    # Smoke test (sample N persons):
    python scripts/stage1_build_pool.py --config configs/comet.yaml ... --limit-persons 5000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cohort_utils import (
    COMORBIDITY_ICD, MEDICATION_KEYWORDS,
    add_comorbidities, add_medication_flags, add_medication_flags_generic,
    build_composite_endpoint, conds_within,
    compute_adherence_metrics_generic,
    drug_mask,
    identify_arms_generic,
    load_conditions_with_dates, load_death, load_drug_master,
    load_echo_meta, load_ecg_meta,
    load_trial_config, load_visit_occurrence, load_procedure_occurrence,
    on_drug_at_index, parse_person_table, resolve_keywords, safe_hr_from_rr,
)


# ── Private helpers (unchanged from original) ─────────────────────────────────

def _best_ef(
    echo: pd.DataFrame,
    cohort: pd.DataFrame,
    lookback_days: int = 1825,
) -> pd.DataFrame:
    """Most recent qualifying echo EF within lookback_days before index."""
    idx = cohort[["MRN", "index_date"]].drop_duplicates("MRN")
    joined = echo.merge(idx, on="MRN", how="inner")
    window = (
        (joined["EchoDate"] <= joined["index_date"]) &
        (joined["EchoDate"] >= joined["index_date"] - pd.Timedelta(days=lookback_days))
    )
    valid = joined[window].copy()
    if valid.empty:
        return pd.DataFrame(
            columns=["MRN", "ef_at_index", "echo_date_at_index", "ef_lookback_days"]
        )
    best = (valid.sort_values("EchoDate")
            .groupby("MRN", sort=False)
            .agg(ef_at_index=("EF", "last"),
                 echo_date_at_index=("EchoDate", "last"))
            .reset_index())
    best = best.merge(idx[["MRN", "index_date"]], on="MRN", how="left")
    best["ef_lookback_days"] = (best["index_date"] - best["echo_date_at_index"]).dt.days
    return best.drop(columns=["index_date"])


def _build_ecg_candidates(
    ecg_meta: pd.DataFrame,
    cohort: pd.DataFrame,
    window_days: int = 365,
) -> pd.DataFrame:
    """All ECGs within ±window_days of each patient's index date."""
    idx = cohort[["MRN", "person_id", "index_date"]].drop_duplicates("MRN")
    joined = ecg_meta.merge(idx, on="MRN", how="inner")
    lo = joined["index_date"] - pd.Timedelta(days=window_days)
    hi = joined["index_date"] + pd.Timedelta(days=window_days)
    cands = joined[(joined["ECGDate"] >= lo) & (joined["ECGDate"] <= hi)].copy()
    cands["days_from_index"] = (cands["ECGDate"] - cands["index_date"]).dt.days
    keep = ["person_id", "MRN", "fileID", "ECGDate", "days_from_index"]
    for col in ["RR_Interval", "PR_Interval", "QRS_Duration"]:
        if col in cands.columns:
            keep.append(col)
    return cands[keep].reset_index(drop=True)


def _nearest_ecg_before(
    ecg_candidates: pd.DataFrame,
    window_days: int = 365,
) -> pd.DataFrame:
    """Nearest ECG on/before index date, within window_days."""
    before = ecg_candidates[
        (ecg_candidates["days_from_index"] >= -window_days) &
        (ecg_candidates["days_from_index"] <= 0)
    ].copy()
    if before.empty:
        return pd.DataFrame(
            columns=["MRN", "ecg_file_id", "ecg_days_from_index",
                     "RR_Interval", "PR_Interval", "QRS_Duration"]
        )
    best = (before.sort_values("days_from_index", ascending=False)
            .groupby("MRN", sort=False).first().reset_index())
    best = best.rename(columns={"fileID": "ecg_file_id",
                                  "days_from_index": "ecg_days_from_index"})
    keep = ["MRN", "ecg_file_id", "ecg_days_from_index"]
    for col in ["RR_Interval", "PR_Interval", "QRS_Duration"]:
        if col in best.columns:
            keep.append(col)
    return best[keep]


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 1: build maximally permissive candidate pool (config-driven)"
    )
    # Required
    p.add_argument("--config",           required=True,
                   help="Path to per-trial YAML config (e.g. configs/comet.yaml)")
    p.add_argument("--person-parquet",   required=True)
    p.add_argument("--condition-dir",    required=True)
    p.add_argument("--drug-master",      required=True)
    p.add_argument("--echo-meta",        required=True)
    p.add_argument("--ecg-meta",         required=True)
    p.add_argument("--death-parquet",    required=True)

    # Output
    p.add_argument("--output-root",      default="/home/rbc58/mnt/ecg-tte",
                   help="Root output dir. Pool written to {output-root}/{trial.key}/pool/")
    p.add_argument("--output-dir",       default=None,
                   help="Override full output path (ignores --output-root / trial key)")

    # Optional OMOP tables (for composite endpoints)
    p.add_argument("--visit-dir",        default=None,
                   help="OMOP visit_occurrence shard dir (required for inpatient_icd endpoints)")
    p.add_argument("--procedure-dir",    default=None,
                   help="OMOP procedure_occurrence shard dir (required for procedure endpoints)")

    # Tuning
    p.add_argument("--ecg-window-pool-days", type=int, default=365,
                   help="ECG pool window (default 365d; keep ≥ Stage-3 ECG window)")
    p.add_argument("--ef-lookback-days",     type=int, default=1825,
                   help="Max echo EF lookback (default 5yr = 1825d)")
    p.add_argument("--max-followup-days",    type=int, default=1825,
                   help="Outcome censoring window (default 5yr)")
    p.add_argument("--censor-date",          default="",
                   help="Administrative censor date YYYY-MM-DD (default: death-table max)")
    p.add_argument("--limit-persons",        type=int, default=None,
                   help="Limit to first N persons (smoke test only)")
    p.add_argument("--seed",                 type=int, default=42)
    return p.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    # ── Load + validate trial config ──────────────────────────────────────────
    print(f"Loading trial config: {args.config}")
    cfg = load_trial_config(args.config)
    trial_key  = cfg["trial"]["key"]
    trial_name = cfg["trial"]["name"]
    print(f"  Trial: {trial_name}  ({trial_key})")

    # ── Output directory ──────────────────────────────────────────────────────
    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        out_dir = Path(args.output_root) / trial_key / "pool"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output: {out_dir}")

    # ── Resolve arms spec (keyword_const → literal lists) ─────────────────────
    arms_spec = []
    for arm in cfg["arms"]:
        resolved = dict(arm)
        resolved["keywords"] = resolve_keywords(arm.get("keywords") or
                                                arm.get("keyword_const"))
        ff = arm.get("formulation_filter") or {}
        if ff:
            resolved["formulation_filter"] = {
                "require": resolve_keywords(ff.get("require", [])),
                "exclude": resolve_keywords(ff.get("exclude", [])),
            }
        arms_spec.append(resolved)
    arm_names = [a["name"] for a in arms_spec]

    # ── Person table ──────────────────────────────────────────────────────────
    print("\nLoading person table …")
    person = parse_person_table(args.person_parquet)
    if args.limit_persons:
        person = person.head(args.limit_persons)
        print(f"  [smoke test] limited to {len(person):,} persons")
    print(f"  {len(person):,} persons loaded")

    # ── Drug master ───────────────────────────────────────────────────────────
    print("\nLoading drug master …")
    person_mrns = set(person["MRN"].astype(str))
    dm_full = load_drug_master(args.drug_master, mrns=person_mrns)
    print(f"  {len(dm_full):,} drug records, {dm_full['MRN'].nunique():,} unique patients")

    # ── Arm identification ─────────────────────────────────────────────────────
    print(f"\nIdentifying {trial_name} arm initiators (naive new-user) …")
    arm_df = identify_arms_generic(
        dm_full, arms_spec,
        index_definition=cfg["design"].get("index_definition", "first_ever_arm_dispense"),
    )
    for a in arms_spec:
        n = (arm_df["arm"] == a["name"]).sum()
        print(f"  {a['name']} arm ({a['role']}): {n:,}")

    # ── Join demographics ──────────────────────────────────────────────────────
    pool = arm_df.merge(person, on="MRN", how="inner")
    pool["person_id"] = pool["person_id"].astype(str)
    pool["age_at_index"] = (pool["index_date"] - pool["birth_date"]).dt.days / 365.25
    pool["sex_binary"] = (pool["sex"] == "F").astype(int)
    print(f"\nAfter person join: {len(pool):,} patients")

    # ── Drug master filtered to pool ──────────────────────────────────────────
    pool_mrns = set(pool["MRN"].astype(str).unique())
    dm = dm_full[dm_full["MRN"].isin(pool_mrns)].copy()
    print(f"  Drug master filtered to pool: {len(dm):,} records")

    # ── Adherence metrics ─────────────────────────────────────────────────────
    print("\nComputing adherence metrics (90d / 180d / 365d refill counts) …")
    pool = compute_adherence_metrics_generic(
        dm, pool, arms_spec,
        windows=(90, 180, 365),
        max_followup_days=args.max_followup_days,
    )
    for w in (90, 180, 365):
        col = f"n_refills_assigned_{w}d"
        if col in pool.columns:
            print(f"  {col}: median={pool[col].median():.1f}  "
                  f"≥2: {(pool[col] >= 2).sum():,}/{len(pool):,}")

    # ── Drug exclusion flags ──────────────────────────────────────────────────
    print("\nComputing concurrent drug flags …")
    idx_mrn = pool[["MRN", "index_date"]]
    for drug_spec in cfg.get("exclusion", {}).get("drug", []):
        raw_kw = drug_spec.get("keywords") or drug_spec.get("keyword_const")
        kw = resolve_keywords(raw_kw)
        if not kw:
            continue
        pool[drug_spec["name"]] = pool["MRN"].isin(
            on_drug_at_index(dm, kw, idx_mrn,
                             window_days=drug_spec.get("window_days", 30))
        ).astype(int)
        print(f"  {drug_spec['name']}: {pool[drug_spec['name']].sum():,}")

    # Also include required_drug flags (informational)
    for drug_spec in cfg.get("inclusion", {}).get("required_drug", []):
        raw_kw = drug_spec.get("keywords") or drug_spec.get("keyword_const")
        kw = resolve_keywords(raw_kw)
        if not kw:
            continue
        pool[drug_spec["name"]] = pool["MRN"].isin(
            on_drug_at_index(dm, kw, idx_mrn,
                             window_days=drug_spec.get("window_days", 90))
        ).astype(int)

    # ── Echo EF ───────────────────────────────────────────────────────────────
    ef_cfg        = cfg.get("inclusion", {}).get("ef", {})
    ef_lookback   = ef_cfg.get("lookback_days", args.ef_lookback_days)
    print(f"\nLoading echo metadata (EF lookback {ef_lookback}d) …")
    echo = load_echo_meta(args.echo_meta, mrns=pool_mrns)
    print(f"  {len(echo):,} echo records, {echo['MRN'].nunique():,} unique patients")
    ef_df = _best_ef(echo, pool, lookback_days=ef_lookback)
    pool  = pool.merge(ef_df, on="MRN", how="left")
    n_echo = pool["ef_at_index"].notna().sum()
    print(f"  EF at index: {n_echo:,}/{len(pool):,} have echo EF")
    if n_echo > 0:
        ef_thr = ef_cfg.get("threshold", 40.0)
        ef_dir = ef_cfg.get("direction", "<=")
        n_qual = (pool["ef_at_index"] <= ef_thr).sum() if ef_dir == "<=" else \
                 (pool["ef_at_index"] >= ef_thr).sum()
        print(f"  EF {ef_dir}{ef_thr}%: {n_qual:,}  "
              f"EF median={pool['ef_at_index'].median():.1f}")

    # ── Condition occurrences ─────────────────────────────────────────────────
    pool_pids = set(pool["person_id"].astype(str).unique())
    print("\nLoading condition occurrences …")
    conditions = load_conditions_with_dates(args.condition_dir, pool_pids)
    print(f"  {len(conditions):,} condition records loaded")

    idx_pid = pool[["person_id", "index_date"]].copy()
    idx_pid["person_id"] = idx_pid["person_id"].astype(str)
    print("\nComputing condition-based flags …")

    # Inclusion required_icd flags
    for icd_spec in cfg.get("inclusion", {}).get("required_icd", []):
        pool[icd_spec["name"]] = pool["person_id"].astype(str).isin(
            conds_within(conditions, icd_spec["codes"], idx_pid,
                         days_before=icd_spec.get("lookback_days", 365),
                         use_4char=(icd_spec.get("char", 3) == 4))
        ).astype(int)
        print(f"  {icd_spec['name']}: {pool[icd_spec['name']].sum():,}")

    # Exclusion condition flags
    for icd_spec in cfg.get("exclusion", {}).get("icd", []):
        pool[icd_spec["name"]] = pool["person_id"].astype(str).isin(
            conds_within(conditions, icd_spec["codes"], idx_pid,
                         days_before=icd_spec.get("lookback_days", 1825),
                         use_4char=(icd_spec.get("char", 3) == 4))
        ).astype(int)

    # Additional condition_flags from covariates
    for icd_spec in cfg.get("covariates", {}).get("condition_flags", []):
        pool[icd_spec["name"]] = pool["person_id"].astype(str).isin(
            conds_within(conditions, icd_spec["codes"], idx_pid,
                         days_before=icd_spec.get("lookback_days", 1825),
                         use_4char=(icd_spec.get("char", 3) == 4))
        ).astype(int)

    # Print exclusion summary
    excl_flags = [s["name"] for s in cfg.get("exclusion", {}).get("icd", [])]
    if excl_flags:
        print("  Exclusion ICD flags: " +
              "  ".join(f"{f}={pool[f].sum():,}" for f in excl_flags if f in pool.columns))

    # Comorbidities
    comorbidity_keys = cfg.get("covariates", {}).get(
        "comorbidities", list(COMORBIDITY_ICD.keys())
    )
    pool = add_comorbidities(pool, conditions, keys=comorbidity_keys)

    # Medication flags (90d lookback) — config-driven via add_medication_flags_generic
    med_names = cfg.get("covariates", {}).get(
        "medications_90d",
        ["loop_diuretic", "acei_arb", "aldosterone_antag", "digoxin", "statin", "nitrate"],
    )
    print("\nAdding medication flags (90d lookback) …")
    pool = add_medication_flags_generic(pool, dm, med_names, window_days=90)
    for med in med_names:
        col = med if med.endswith("_90d") else f"{med}_90d"
        if col in pool.columns:
            print(f"  {col}: {pool[col].sum():,}")

    # ── ECG candidates ────────────────────────────────────────────────────────
    pool_ecg_days = cfg["ecg"].get("pool_window_days", args.ecg_window_pool_days)
    print(f"\nLoading ECG metadata (pool window ±{pool_ecg_days}d) …")
    ecg_meta = load_ecg_meta(args.ecg_meta, mrns=pool_mrns)
    print(f"  {len(ecg_meta):,} ECG records, {ecg_meta['MRN'].nunique():,} unique patients")

    ecg_cands = _build_ecg_candidates(ecg_meta, pool, window_days=pool_ecg_days)
    print(f"  ecg_candidates: {len(ecg_cands):,} rows, "
          f"{ecg_cands['MRN'].nunique():,} patients")

    ecg_at_idx = _nearest_ecg_before(ecg_cands, window_days=pool_ecg_days)
    pool = pool.merge(ecg_at_idx, on="MRN", how="left")
    pool["hr_at_index"] = safe_hr_from_rr(pool["RR_Interval"] if "RR_Interval" in pool.columns else pd.Series(dtype=float))
    print(f"  ECG at index: {pool['ecg_file_id'].notna().sum():,}/{len(pool):,} matched")

    # ── Death table ───────────────────────────────────────────────────────────
    print("\nLoading death table …")
    death = load_death(args.death_parquet, person_ids=pool_pids)
    print(f"  {len(death):,} death records")
    pool = pool.merge(death, on="person_id", how="left")

    if args.censor_date:
        end_date = pd.Timestamp(args.censor_date)
    else:
        end_date = (death["death_date"].max()
                    if not death.empty else pd.Timestamp("2024-12-31"))
        if pd.isna(end_date):
            end_date = pd.Timestamp("2024-12-31")
    print(f"  Censor date: {end_date.date()}")

    # Backward-compat all-cause mortality columns (always produced)
    pool["event_death"] = pool["death_date"].notna().astype(int)
    pool["death_date_censored"] = pool["death_date"].fillna(end_date)
    pool["time_to_death"] = (
        pool["death_date_censored"] - pool["index_date"]
    ).dt.days.clip(lower=0)
    max_d = args.max_followup_days
    pool.loc[pool["time_to_death"] > max_d, "event_death"]   = 0
    pool.loc[pool["time_to_death"] > max_d, "time_to_death"] = max_d
    print(f"  Events (death): {pool['event_death'].sum():,}/{len(pool):,}")

    # ── Primary endpoint (config-driven composite) ────────────────────────────
    endpoint_spec = cfg["endpoint"]["primary"]
    comp_types = [c.get("type") for c in endpoint_spec.get("components", [])]
    needs_visits = "inpatient_icd" in comp_types
    needs_procs  = "procedure" in comp_types

    visit_data = proc_data = None
    if needs_visits:
        if args.visit_dir:
            print("\nLoading visit_occurrence …")
            visit_data = load_visit_occurrence(args.visit_dir, pool_pids)
            print(f"  {len(visit_data):,} visit records")
        else:
            print("  WARNING: endpoint has inpatient_icd component but --visit-dir not provided. "
                  "Falling back to condition-date only (no inpatient gate).")
    if needs_procs:
        if args.procedure_dir:
            print("\nLoading procedure_occurrence …")
            proc_data = load_procedure_occurrence(args.procedure_dir, pool_pids)
            print(f"  {len(proc_data):,} procedure records")
        else:
            print("  WARNING: endpoint has procedure component but --procedure-dir not provided. "
                  "Procedure component will emit all-NaN.")

    print(f"\nBuilding composite endpoint '{endpoint_spec['name']}' …")
    ep_df = build_composite_endpoint(
        pool[["person_id", "index_date", "MRN"]],
        endpoint_spec,
        death=death,
        conditions=conditions,
        visits=visit_data,
        procedures=proc_data,
        end_date=end_date,
    )
    pool = pool.merge(ep_df, on="person_id", how="left")
    print(f"  event_primary: {pool['event_primary'].sum():,}/{len(pool):,}")

    # ── Column ordering / cleanup ─────────────────────────────────────────────
    # Fixed identity + demographics + adherence + outcomes (COMET-compat ordering)
    first_date_cols = [f"first_{n}_date" for n in arm_names]
    prior_days_cols = [f"prior_{n}_days" for n in arm_names]

    # Stage3 alias columns (e.g. first_carv_date, prior_meto_days for COMET)
    alias_cols: list[str] = []
    for arm in arms_spec:
        alias = arm.get("stage3_alias")
        if alias:
            alias_cols += [f"first_{alias}_date", f"prior_{alias}_days"]

    POOL_COLS_FIXED = (
        # Identity
        ["person_id", "MRN", "arm", "index_date"] +
        # Demographics
        ["birth_date", "age_at_index", "sex", "sex_binary", "race_black"] +
        # Arm dates + prior exposure (generic names)
        first_date_cols + prior_days_cols +
        # Stage3 aliases (COMET: first_carv_date, first_meto_date, prior_meto_days, etc.)
        alias_cols +
        # Adherence
        ["n_refills_assigned_90d", "n_refills_assigned_180d", "n_refills_assigned_365d",
         "days_on_therapy", "early_adverse_disc"] +
        # Echo EF
        ["ef_at_index", "echo_date_at_index", "ef_lookback_days"] +
        # ECG at index
        ["ecg_file_id", "ecg_days_from_index",
         "RR_Interval", "PR_Interval", "QRS_Duration", "hr_at_index"] +
        # Backward-compat outcomes (all-cause mortality, always)
        ["death_date", "death_date_censored", "event_death", "time_to_death"] +
        # Primary endpoint (config-driven; aliases mortality if mortality-only)
        ["event_primary", "time_to_primary", "primary_event_date"]
    )

    # Config-named flag columns (exclusion + inclusion + covariates)
    config_flag_cols = (
        [s["name"] for s in cfg.get("exclusion",  {}).get("drug", [])] +
        [s["name"] for s in cfg.get("exclusion",  {}).get("icd",  [])] +
        [s["name"] for s in cfg.get("inclusion",  {}).get("required_icd", [])] +
        [s["name"] for s in cfg.get("inclusion",  {}).get("required_drug", [])] +
        [s["name"] for s in cfg.get("covariates", {}).get("condition_flags", [])] +
        list(COMORBIDITY_ICD.keys()) +
        [f"{m}_90d" for m in cfg.get("covariates", {}).get("medications_90d", [])]
    )

    POOL_COLS = list(dict.fromkeys(POOL_COLS_FIXED + config_flag_cols))  # dedup order
    pool_cols_available = [c for c in POOL_COLS if c in pool.columns]

    # Append any extra endpoint flag columns not already in POOL_COLS
    extra_cols = [c for c in pool.columns
                  if c.startswith("flag_") and c not in pool_cols_available]
    pool = pool[pool_cols_available + extra_cols].drop_duplicates("person_id")

    # ── Save artifacts ────────────────────────────────────────────────────────
    pool_path = out_dir / "pool.parquet"
    pool.to_parquet(pool_path, index=False)
    print(f"\npool.parquet → {pool_path}  ({len(pool):,} rows, {len(pool.columns)} cols)")

    dm_pool_path = out_dir / "drug_master_pool.parquet"
    dm.to_parquet(dm_pool_path, index=False)
    print(f"drug_master_pool.parquet → {dm_pool_path}")

    conds_pool_path = out_dir / "conditions_pool.parquet"
    conditions.to_parquet(conds_pool_path, index=False)
    print(f"conditions_pool.parquet → {conds_pool_path}")

    cands_path = out_dir / "ecg_candidates.parquet"
    ecg_cands.to_parquet(cands_path, index=False)
    print(f"ecg_candidates.parquet → {cands_path}  ({len(ecg_cands):,} rows)")

    # ── Build manifest ─────────────────────────────────────────────────────────
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        git_sha = "unknown"

    arm_counts = {f"n_{a['name']}": int((pool["arm"] == a["name"]).sum())
                  for a in arms_spec}
    # COMET backward-compat manifest keys
    if "n_carvedilol" not in arm_counts and "carvedilol" in [a["name"] for a in arms_spec]:
        arm_counts["n_carvedilol"] = arm_counts.get("n_carvedilol", 0)
    if "n_metoprolol" not in arm_counts and "metoprolol" in [a["name"] for a in arms_spec]:
        arm_counts["n_metoprolol"] = arm_counts.get("n_metoprolol", 0)

    manifest = {
        "built_at":              datetime.now().isoformat(),
        "git_sha":               git_sha,
        "command":               " ".join(sys.argv),
        "trial_key":             trial_key,
        "trial_name":            trial_name,
        "arms":                  [a["name"] for a in arms_spec],
        "endpoint_name":         endpoint_spec.get("name"),
        "pool_rows":             len(pool),
        "ecg_candidates_rows":   len(ecg_cands),
        **arm_counts,
        "n_events":              int(pool["event_death"].sum()),
        "n_events_primary":      int(pool["event_primary"].sum() if "event_primary" in pool.columns else 0),
        "ecg_window_pool_days":  pool_ecg_days,
        "ef_lookback_days":      ef_lookback,
        "max_followup_days":     args.max_followup_days,
        "input_paths": {
            "config":            args.config,
            "person_parquet":    args.person_parquet,
            "condition_dir":     args.condition_dir,
            "drug_master":       args.drug_master,
            "echo_meta":         args.echo_meta,
            "ecg_meta":          args.ecg_meta,
            "death_parquet":     args.death_parquet,
        },
    }
    manifest_path = out_dir / "build_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"build_manifest.json → {manifest_path}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  {trial_name} pool build complete")
    print(f"  Total candidates : {len(pool):,}")
    for a in arms_spec:
        print(f"    {a['name']} ({a['role']}) : {(pool['arm']==a['name']).sum():,}")
    print(f"  Events (death)   : {pool['event_death'].sum():,}")
    print(f"  Events (primary) : {pool['event_primary'].sum() if 'event_primary' in pool.columns else 0:,}")
    print(f"  Have ECG in pool : {pool['ecg_file_id'].notna().sum():,}")
    print(f"  Have echo EF     : {pool['ef_at_index'].notna().sum():,}")
    print(f"  Output           : {out_dir}")
    print(f"{'='*60}")
    print("\nNext: run stage2_embed.py to embed pool ECGs, then stage3_filter.py")


if __name__ == "__main__":
    main()
