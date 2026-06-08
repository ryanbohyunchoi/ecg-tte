"""
scripts/stage0_feasibility.py

Stage 0: Per-trial feasibility checker.

Read-only. No patient-level data is written — all output is aggregate-only.
Outputs a per-trial JSON report and an appended summary CSV.

Purpose:
  Pre-flight check before running Stage 1. Identifies trials that are
  NO-GO (too few arm initiators, missing required data fields, zero endpoint events)
  so Stage 1 is only run for viable trials.

Per-trial checks:
  1. Field presence — required columns in OMOP tables / local tables
  2. Arm size — N initiators per arm via identify_arms_generic on a person slice
  3. ICD coverage — % of arm patients with required/exclusion ICD codes
  4. EF coverage — % with echo EF within lookback window
  5. ECG pairable — % with an ECG within ecg.window_days (< 90d) of index
  6. Endpoint event counts — crude event rate in arm population
  7. Covariate completeness — % non-null per flag
  8. GO/NO-GO verdict — uses feasibility.min_n_per_arm threshold

Usage:
    # One trial
    python scripts/stage0_feasibility.py \\
        --config           configs/comet.yaml \\
        --person-parquet   /path/to/person.parquet \\
        --condition-dir    /path/to/condition_occurrence \\
        --drug-master      /path/to/drug_master.parquet \\
        --echo-meta        /path/to/echo_accession_number.parquet \\
        --ecg-meta         /path/to/ecg_metadata.parquet \\
        --death-parquet    /path/to/death.parquet \\
        --output-dir       /home/rbc58/mnt/ecg-tte/_feasibility

    # All trials in configs/ directory
    python scripts/stage0_feasibility.py \\
        --config-dir       configs/ \\
        ... \\
        --output-dir       /home/rbc58/mnt/ecg-tte/_feasibility

    # Smoke test (small person slice)
    python scripts/stage0_feasibility.py --config configs/comet.yaml \\
        ... --limit-persons 5000

Output files (aggregate-only, no patient rows):
    {output-dir}/feasibility_{trial_key}.json   — per-trial full report
    {output-dir}/feasibility_summary.csv        — one row per trial, appended on each run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cohort_utils import (
    COMORBIDITY_ICD, KEYWORD_REGISTRY,
    conds_within,
    identify_arms_generic,
    load_conditions_with_dates, load_death, load_drug_master,
    load_echo_meta, load_ecg_meta,
    load_trial_config, load_visit_occurrence,
    parse_person_table, resolve_keywords, validate_config,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total > 0 else 0.0


def _arm_init_counts(
    dm_full: pd.DataFrame,
    arms_spec: list[dict],
    index_definition: str = "first_ever_arm_dispense",
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Run arm identification; return (arm_df, {arm_name: count})."""
    try:
        arm_df = identify_arms_generic(dm_full, arms_spec, index_definition=index_definition)
    except NotImplementedError as e:
        return pd.DataFrame(), {"error": str(e)}
    counts = {a["name"]: int((arm_df["arm"] == a["name"]).sum()) for a in arms_spec}
    return arm_df, counts


def _check_omop_fields(
    parquet_or_dir: str,
    expected_cols: list[str],
    *,
    is_dir: bool = False,
    glob: str = "*.parquet",
) -> dict[str, bool]:
    """
    Return {col: bool_present} by reading one parquet file from path / dir.
    Never loads data — uses read_parquet with columns= to probe schema.
    """
    try:
        if is_dir:
            shards = sorted(Path(parquet_or_dir).glob(glob))
            if not shards:
                return {c: False for c in expected_cols}
            path = shards[0]
        else:
            path = Path(parquet_or_dir)
        import pyarrow.parquet as pq
        schema = pq.read_schema(str(path))
        avail = set(schema.names)
        return {c: c in avail for c in expected_cols}
    except Exception as e:
        return {c: f"error: {e}" for c in expected_cols}


def _ef_coverage(
    echo: pd.DataFrame,
    arm_df: pd.DataFrame,
    lookback_days: int,
) -> dict:
    idx = arm_df[["MRN", "index_date"]].drop_duplicates("MRN")
    joined = echo.merge(idx, on="MRN", how="inner")
    window = (
        (joined["EchoDate"] <= joined["index_date"]) &
        (joined["EchoDate"] >= joined["index_date"] - pd.Timedelta(days=lookback_days))
    )
    has_ef = int(joined[window]["MRN"].nunique())
    total  = len(idx)
    return {"n_with_ef": has_ef, "n_total": total, "pct": _pct(has_ef, total)}


def _ecg_coverage(
    ecg_meta: pd.DataFrame,
    arm_df: pd.DataFrame,
    window_days: int,
) -> dict:
    idx = arm_df[["MRN", "index_date"]].drop_duplicates("MRN")
    joined = ecg_meta.merge(idx, on="MRN", how="inner")
    in_window = (
        (joined["ECGDate"] >= joined["index_date"] - pd.Timedelta(days=window_days)) &
        (joined["ECGDate"] <= joined["index_date"])
    )
    has_ecg = int(joined[in_window]["MRN"].nunique())
    total   = len(idx)
    return {"n_with_ecg_in_window": has_ecg, "n_total": total,
            "window_days": window_days, "pct": _pct(has_ecg, total)}


def _event_counts(
    arm_df: pd.DataFrame,
    death: pd.DataFrame,
    followup_days: int,
) -> dict:
    """Crude all-cause mortality event count within follow-up."""
    if arm_df.empty:
        return {"n_events": 0, "n_total": 0, "crude_rate": 0.0}
    merged = arm_df[["person_id", "index_date"]].merge(
        death.rename(columns={"person_id": "person_id"}),
        on="person_id", how="left"
    )
    total = len(merged)
    within = (
        merged["death_date"].notna() &
        (merged["death_date"] >= merged["index_date"]) &
        (merged["death_date"] <= merged["index_date"] + pd.Timedelta(days=followup_days))
    )
    n_ev = int(within.sum())
    return {"n_events": n_ev, "n_total": total,
            "crude_rate": round(100 * n_ev / total, 2) if total else 0.0}


def _icd_coverage(
    conditions: pd.DataFrame,
    arm_df: pd.DataFrame,
    icd_spec: dict,
) -> dict:
    if arm_df.empty:
        return {"n": 0, "pct": 0.0}
    idx_pid = arm_df[["person_id", "index_date"]].copy()
    idx_pid["person_id"] = idx_pid["person_id"].astype(str)
    hits = conds_within(
        conditions, icd_spec["codes"], idx_pid,
        days_before=icd_spec.get("lookback_days", 1825),
        use_4char=(icd_spec.get("char", 3) == 4),
    )
    n = len(hits)
    return {"n": n, "pct": _pct(n, len(arm_df))}


# ── Per-trial feasibility run ─────────────────────────────────────────────────

def run_feasibility(
    cfg: dict,
    *,
    person_parquet: str,
    condition_dir: str,
    drug_master: str,
    echo_meta: str,
    ecg_meta: str,
    death_parquet: str,
    visit_dir: str | None,
    limit_persons: int | None,
) -> dict:
    """
    Run all feasibility checks for one trial config.
    Returns a report dict (aggregate only, no patient rows).
    """
    trial_key  = cfg["trial"]["key"]
    trial_name = cfg["trial"]["name"]
    arms_spec  = []
    for arm in cfg["arms"]:
        resolved = dict(arm)
        resolved["keywords"] = resolve_keywords(arm.get("keywords") or arm.get("keyword_const"))
        arms_spec.append(resolved)

    min_n     = cfg.get("feasibility", {}).get("min_n_per_arm", 200)
    ecg_win   = cfg["ecg"]["window_days"]
    ecg_pool  = cfg["ecg"].get("pool_window_days", 365)
    ef_cfg    = cfg.get("inclusion", {}).get("ef", {})
    ef_lb     = ef_cfg.get("lookback_days", 1825)
    ep        = cfg["endpoint"]["primary"]
    followup  = ep.get("followup_days", 1825)

    report: dict = {
        "trial_key":   trial_key,
        "trial_name":  trial_name,
        "checked_at":  datetime.now().isoformat(),
        "go_nogo":     "UNKNOWN",
        "go_reasons":  [],
        "nogo_reasons": [],
    }

    # ── 1. Schema field presence ──────────────────────────────────────────────
    report["field_presence"] = {}

    person_fields = _check_omop_fields(
        person_parquet,
        ["person_id", "year_of_birth", "birth_datetime", "gender_concept_id",
         "race_concept_id", "person_source_value"],
    )
    report["field_presence"]["person"] = person_fields

    cond_fields = _check_omop_fields(
        condition_dir,
        ["person_id", "condition_source_value", "condition_start_date", "visit_occurrence_id"],
        is_dir=True, glob="condition_occurrence*.parquet",
    )
    report["field_presence"]["condition_occurrence"] = cond_fields

    death_fields = _check_omop_fields(
        death_parquet,
        ["person_id", "death_date", "cause_concept_id"],
    )
    report["field_presence"]["death"] = death_fields

    if visit_dir:
        visit_fields = _check_omop_fields(
            visit_dir,
            ["person_id", "visit_concept_id", "visit_start_date",
             "visit_end_date", "visit_occurrence_id"],
            is_dir=True, glob="visit_occurrence*.parquet",
        )
        report["field_presence"]["visit_occurrence"] = visit_fields

    # ── 2. Person + drug load ─────────────────────────────────────────────────
    print(f"  [{trial_key}] Loading persons …")
    person = parse_person_table(person_parquet)
    if limit_persons:
        person = person.head(limit_persons)
    report["n_persons_sampled"] = len(person)

    print(f"  [{trial_key}] Loading drug master …")
    person_mrns = set(person["MRN"].astype(str))
    dm = load_drug_master(drug_master, mrns=person_mrns)

    # ── 3. Arm identification ─────────────────────────────────────────────────
    print(f"  [{trial_key}] Identifying arm initiators …")
    index_def = cfg["design"].get("index_definition", "first_ever_arm_dispense")
    arm_df, arm_counts = _arm_init_counts(dm, arms_spec, index_definition=index_def)
    report["arm_counts"] = arm_counts

    if arm_df.empty or "error" in arm_counts:
        report["go_nogo"] = "NO-GO"
        report["nogo_reasons"].append(f"arm_identification_failed: {arm_counts.get('error', 'empty')}")
        return report

    # Join person_id for downstream checks
    arm_df = arm_df.merge(person[["MRN", "person_id"]], on="MRN", how="left")
    arm_df["person_id"] = arm_df["person_id"].astype(str)

    # GO/NO-GO: arm size check
    for a in arms_spec:
        n = arm_counts.get(a["name"], 0)
        if n < min_n:
            report["nogo_reasons"].append(
                f"arm_{a['name']}_too_small: {n} < min_n={min_n}"
            )
        else:
            report["go_reasons"].append(f"arm_{a['name']}_ok: n={n}")

    # ── 4. ICD coverage ───────────────────────────────────────────────────────
    pool_pids = set(arm_df["person_id"].astype(str).unique())
    print(f"  [{trial_key}] Loading conditions ({len(pool_pids):,} pool pids) …")
    conditions = load_conditions_with_dates(condition_dir, pool_pids)
    report["n_conditions"] = len(conditions)

    report["icd_coverage"] = {}
    for icd_spec in cfg.get("inclusion", {}).get("required_icd", []):
        report["icd_coverage"][icd_spec["name"]] = _icd_coverage(conditions, arm_df, icd_spec)
    for icd_spec in cfg.get("exclusion", {}).get("icd", []):
        report["icd_coverage"][icd_spec["name"]] = _icd_coverage(conditions, arm_df, icd_spec)
    for icd_spec in cfg.get("covariates", {}).get("condition_flags", []):
        report["icd_coverage"][icd_spec["name"]] = _icd_coverage(conditions, arm_df, icd_spec)

    # ── 5. EF coverage ────────────────────────────────────────────────────────
    print(f"  [{trial_key}] Loading echo meta …")
    pool_mrns = set(arm_df["MRN"].astype(str).unique())
    try:
        echo = load_echo_meta(echo_meta, mrns=pool_mrns)
        report["ef_coverage"] = _ef_coverage(echo, arm_df, ef_lb)
    except Exception as e:
        print(f"  [{trial_key}] WARNING: echo meta load failed: {e}")
        report["ef_coverage"] = {"error": str(e)}

    # ── 6. ECG coverage (strict window) ──────────────────────────────────────
    print(f"  [{trial_key}] Loading ECG meta …")
    try:
        ecg_meta_df = load_ecg_meta(ecg_meta, mrns=pool_mrns)
        report["ecg_coverage"] = _ecg_coverage(ecg_meta_df, arm_df, window_days=ecg_win)
    except Exception as e:
        print(f"  [{trial_key}] WARNING: ECG meta load failed: {e}")
        report["ecg_coverage"] = {"error": str(e)}

    # GO/NO-GO: ECG coverage
    ecg_cov = report.get("ecg_coverage", {})
    if "error" in ecg_cov:
        report["nogo_reasons"].append(f"ecg_load_error: {ecg_cov['error']}")
    else:
        ecg_pct = ecg_cov.get("pct", 0)
        if ecg_pct < 5:
            report["nogo_reasons"].append(
                f"ecg_coverage_too_low: {ecg_pct:.1f}% within {ecg_win}d window"
            )
        else:
            report["go_reasons"].append(f"ecg_coverage_ok: {ecg_pct:.1f}%")

    # ── 7. Endpoint event counts ──────────────────────────────────────────────
    print(f"  [{trial_key}] Loading death …")
    death = load_death(death_parquet, person_ids=pool_pids)
    report["event_counts"] = _event_counts(arm_df, death, followup_days=followup)

    # GO/NO-GO: event count
    n_ev = report["event_counts"]["n_events"]
    if n_ev == 0:
        report["nogo_reasons"].append("zero_events_in_pool")
    else:
        report["go_reasons"].append(f"events_ok: n={n_ev}")

    # ── 8. Covariate comorbidity completeness (spot check) ───────────────────
    # Any-comorbidity ICD completeness = % pool with any I-/E- code ever
    if not conditions.empty:
        has_any_cond = int(conditions["person_id"].astype(str).isin(pool_pids).sum())
        pct_any = _pct(
            conditions["person_id"].astype(str).isin(pool_pids).nunique()
            if has_any_cond else 0,
            len(arm_df),
        )
        report["pct_with_any_condition_code"] = pct_any
    else:
        report["pct_with_any_condition_code"] = 0.0

    # ── 9. Final verdict ──────────────────────────────────────────────────────
    if report["nogo_reasons"]:
        report["go_nogo"] = "NO-GO"
    else:
        report["go_nogo"] = "GO"

    return report


# ── Summary row ───────────────────────────────────────────────────────────────

def _summary_row(report: dict) -> dict:
    ac = report.get("arm_counts", {})
    ecg = report.get("ecg_coverage", {})
    ef  = report.get("ef_coverage", {})
    ev  = report.get("event_counts", {})
    row = {
        "trial_key":        report["trial_key"],
        "trial_name":       report["trial_name"],
        "go_nogo":          report["go_nogo"],
        "checked_at":       report["checked_at"],
        "n_persons_sampled": report.get("n_persons_sampled", ""),
    }
    for k, v in ac.items():
        if k != "error":
            row[f"n_{k}"] = v
    row["ecg_pct"]     = ecg.get("pct", "")
    row["ecg_window"]  = ecg.get("window_days", "")
    row["ef_pct"]      = ef.get("pct", "")
    row["n_events"]    = ev.get("n_events", "")
    row["crude_rate"]  = ev.get("crude_rate", "")
    row["nogo_reasons"] = " | ".join(report.get("nogo_reasons", []))
    return row


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 0: per-trial feasibility checker (aggregate-only outputs)"
    )
    # Config — mutually exclusive
    cfg_grp = p.add_mutually_exclusive_group(required=True)
    cfg_grp.add_argument("--config",     help="Path to single trial YAML config")
    cfg_grp.add_argument("--config-dir", help="Directory of YAML configs (runs all *.yaml)")

    # OMOP / local data paths
    p.add_argument("--person-parquet",  required=True)
    p.add_argument("--condition-dir",   required=True)
    p.add_argument("--drug-master",     required=True)
    p.add_argument("--echo-meta",       required=True)
    p.add_argument("--ecg-meta",        required=True)
    p.add_argument("--death-parquet",   required=True)

    # Optional
    p.add_argument("--visit-dir",    default=None,
                   help="OMOP visit_occurrence dir (needed for inpatient_icd endpoints)")
    p.add_argument("--output-dir",   default="/home/rbc58/mnt/ecg-tte/_feasibility",
                   help="Output directory for JSON/CSV reports")
    p.add_argument("--limit-persons", type=int, default=None,
                   help="Limit to first N persons (smoke test)")
    p.add_argument("--fail-on-nogo", action="store_true",
                   help="Exit non-zero if any trial is NO-GO")
    p.add_argument("--wandb", action="store_true",
                   help="Log feasibility results to Weights & Biases")
    p.add_argument("--wandb-project", default="ecg-tte",
                   help="W&B project name (default: ecg-tte)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect configs to run
    if args.config:
        config_paths = [Path(args.config)]
    else:
        config_paths = sorted(Path(args.config_dir).glob("*.yaml"))
        config_paths = [p for p in config_paths if not p.name.startswith("_")]
        print(f"Found {len(config_paths)} trial configs in {args.config_dir}")

    summary_rows: list[dict] = []
    any_nogo = False

    for cfg_path in config_paths:
        print(f"\n{'='*60}")
        print(f"  Feasibility: {cfg_path.stem}")

        try:
            cfg = load_trial_config(str(cfg_path))
        except (ValueError, Exception) as e:
            print(f"  ERROR loading config {cfg_path}: {e}")
            err_report = {
                "trial_key":    cfg_path.stem,
                "trial_name":   cfg_path.stem,
                "go_nogo":      "NO-GO",
                "nogo_reasons": [f"config_load_error: {e}"],
                "go_reasons":   [],
                "checked_at":   datetime.now().isoformat(),
            }
            json_path = out_dir / f"feasibility_{cfg_path.stem}.json"
            with open(json_path, "w") as f:
                json.dump(err_report, f, indent=2, default=str)
            summary_rows.append(_summary_row(err_report))
            any_nogo = True
            continue

        report = run_feasibility(
            cfg,
            person_parquet=args.person_parquet,
            condition_dir=args.condition_dir,
            drug_master=args.drug_master,
            echo_meta=args.echo_meta,
            ecg_meta=args.ecg_meta,
            death_parquet=args.death_parquet,
            visit_dir=args.visit_dir,
            limit_persons=args.limit_persons,
        )

        # Write per-trial JSON (aggregate-only)
        json_path = out_dir / f"feasibility_{report['trial_key']}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        verdict = report["go_nogo"]
        if verdict == "NO-GO":
            any_nogo = True
        print(f"\n  ── {report['trial_name']}: {verdict} ──")
        if report["nogo_reasons"]:
            for r in report["nogo_reasons"]:
                print(f"    ✗ {r}")
        for r in report["go_reasons"]:
            print(f"    ✓ {r}")

        arm_counts = report.get("arm_counts", {})
        for name, n in arm_counts.items():
            if name != "error":
                print(f"    n_{name} = {n:,}")
        ecg = report.get("ecg_coverage", {})
        if "error" in ecg:
            print(f"    ECG: ERROR — {ecg['error']}")
        else:
            print(f"    ECG within {ecg.get('window_days','')}d: "
                  f"{ecg.get('pct','')}% ({ecg.get('n_with_ecg_in_window','')})")
        ef = report.get("ef_coverage", {})
        if "error" in ef:
            print(f"    EF: ERROR — {ef['error']}")
        else:
            print(f"    EF coverage: {ef.get('pct','')}% ({ef.get('n_with_ef','')})")
        ev = report.get("event_counts", {})
        print(f"    Events (all-cause death): {ev.get('n_events','')} "
              f"({ev.get('crude_rate','')}%)")

        summary_rows.append(_summary_row(report))

        if args.wandb:
            try:
                import wandb
                run = wandb.init(
                    project=args.wandb_project,
                    name=f"stage0_{report['trial_key']}",
                    group="stage0_feasibility",
                    config={"trial_key": report["trial_key"], "trial_name": report["trial_name"]},
                    reinit=True,
                )
                row = _summary_row(report)
                wandb.summary.update({k: v for k, v in row.items() if v != ""})
                wandb.summary["go_nogo"] = report["go_nogo"]
                wandb.finish()
            except Exception as e:
                print(f"  [wandb] WARNING: logging failed: {e}")

    # Write/append summary CSV (aggregate-only)
    summary_path = out_dir / "feasibility_summary.csv"
    new_df = pd.DataFrame(summary_rows)
    if summary_path.exists():
        old_df = pd.read_csv(summary_path)
        # Replace rows for trials we just ran (by trial_key)
        old_df = old_df[~old_df["trial_key"].isin(new_df["trial_key"])]
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(summary_path, index=False)

    # Final summary
    print(f"\n{'='*60}")
    print(f"Feasibility sweep complete — {len(summary_rows)} trial(s) checked")
    go_n    = sum(1 for r in summary_rows if r["go_nogo"] == "GO")
    nogo_n  = sum(1 for r in summary_rows if r["go_nogo"] != "GO")
    print(f"  GO:    {go_n}")
    print(f"  NO-GO: {nogo_n}")
    print(f"Summary: {summary_path}")
    print(f"Reports: {out_dir}/feasibility_{{trial_key}}.json")

    if args.fail_on_nogo and any_nogo:
        sys.exit(1)


if __name__ == "__main__":
    main()
