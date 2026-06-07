"""
trialemulation/make_baseline_table.py

Generate baseline characteristics (Table 1) for each emulated trial cohort.
Reads Stage 3 cohort parquets. Produces per-trial CSVs with 4 columns:
  Variable | Treated (n=X) | Control (n=X) | p-value

Usage:
    python trialemulation/make_baseline_table.py \
        --paradigm  .../paradigm/runs/paradigm_810d/paradigm_cohort.parquet \
        --aristotle .../aristotle/runs/aristotle_660d/aristotle_cohort.parquet \
        --dig       .../dig/runs/dig_1095d/dig_cohort.parquet \
        --rales     .../mra/rales/runs/rales_730d/rales_cohort.parquet \
        --out-dir   .../baseline_tables
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ── Arm label map per trial ────────────────────────────────────────────────────

TRIAL_META = {
    "paradigm":  {"treated": "arnii",    "control": "acei",    "label": "PARADIGM-HF"},
    "aristotle": {"treated": "apixaban", "control": "warfarin","label": "ARISTOTLE"},
    "dig":       {"treated": "treated",  "control": "control", "label": "DIG"},
    "rales":     {"treated": "treated",  "control": "control", "label": "RALES"},
}

TREATED_LABELS = {
    "paradigm":  "Sacubitril/valsartan",
    "aristotle": "Apixaban",
    "dig":       "Digoxin",
    "rales":     "Spironolactone",
}

CONTROL_LABELS = {
    "paradigm":  "ACEi",
    "aristotle": "Warfarin",
    "dig":       "No digoxin",
    "rales":     "No MRA",
}

# Medication columns to suppress per trial: treatment-defining drugs (100/0% by
# design) or universal inclusion criteria (100% both arms, uninformative).
TRIAL_MED_EXCLUSIONS: dict[str, set[str]] = {
    # control arm = ACEi by definition → 100% is arm-defining, not a covariate
    "paradigm": {"acei_arb_90d", "acei_arb"},
    # treatment = digoxin
    "dig":      {"digoxin_90d"},
    # treatment = spironolactone (aldosterone antag); loop diuretic = inclusion criterion (100% both arms)
    "rales":    {"aldosterone_antag_90d", "aldosterone_antag", "loop_diuretic_90d", "loop_diuretic"},
}


# ── Stat helpers ───────────────────────────────────────────────────────────────

def _smd(a: pd.Series, b: pd.Series, binary: bool) -> float:
    """Standardised mean difference."""
    if binary:
        p1, p2 = a.mean(), b.mean()
        denom = np.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2)
        return abs(p1 - p2) / denom if denom > 0 else np.nan
    else:
        denom = np.sqrt((a.std() ** 2 + b.std() ** 2) / 2)
        return abs(a.mean() - b.mean()) / denom if denom > 0 else np.nan


def _fmt_cont(s: pd.Series) -> str:
    return f"{s.mean():.1f} ± {s.std():.1f}" if s.notna().sum() > 0 else "—"


def _fmt_median(s: pd.Series) -> str:
    if s.notna().sum() == 0:
        return "—"
    q1, q2, q3 = s.quantile([0.25, 0.50, 0.75])
    return f"{q2:.1f} [{q1:.1f}–{q3:.1f}]"


def _fmt_bin(s: pd.Series) -> str:
    n = s.notna().sum()
    k = int(s.sum()) if n > 0 else 0
    pct = 100 * k / n if n > 0 else 0
    return f"{k:,} ({pct:.1f}%)"


def _pval_cont(a: pd.Series, b: pd.Series) -> str:
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        return "—"
    _, p = stats.ttest_ind(a, b, equal_var=False)
    return f"{p:.3f}" if p >= 0.001 else "<0.001"


def _pval_bin(a: pd.Series, b: pd.Series) -> str:
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        return "—"
    ct = np.array([[a.sum(), len(a) - a.sum()],
                   [b.sum(), len(b) - b.sum()]])
    if ct.min() < 5:
        return "—"
    _, p, _, _ = stats.chi2_contingency(ct)
    return f"{p:.3f}" if p >= 0.001 else "<0.001"


# ── Row builders ───────────────────────────────────────────────────────────────

def _row_cont(name: str, col: str, t: pd.DataFrame, c: pd.DataFrame,
              fmt: str = "mean") -> dict | None:
    if col not in t.columns and col not in c.columns:
        return None
    ts = t[col] if col in t.columns else pd.Series(dtype=float)
    cs = c[col] if col in c.columns else pd.Series(dtype=float)
    f = _fmt_median if fmt == "median" else _fmt_cont
    return {
        "Variable": name,
        "Treated":  f(ts),
        "Control":  f(cs),
        "p-value":  _pval_cont(ts, cs),
        "SMD":      f"{_smd(ts, cs, binary=False):.3f}",
    }


def _resolve_col(col: str, df: pd.DataFrame) -> str:
    """Try col, then strip _90d suffix as fallback (old cohort parquets use short names)."""
    if col in df.columns:
        return col
    short = col.removesuffix("_90d")
    if short != col and short in df.columns:
        return short
    return col


def _row_bin(name: str, col: str, t: pd.DataFrame, c: pd.DataFrame) -> dict | None:
    col_t = _resolve_col(col, t)
    col_c = _resolve_col(col, c)
    if col_t not in t.columns and col_c not in c.columns:
        return None
    ts = t[col_t] if col_t in t.columns else pd.Series(dtype=float)
    cs = c[col_c] if col_c in c.columns else pd.Series(dtype=float)
    return {
        "Variable": name,
        "Treated":  _fmt_bin(ts),
        "Control":  _fmt_bin(cs),
        "p-value":  _pval_bin(ts, cs),
        "SMD":      f"{_smd(ts, cs, binary=True):.3f}",
    }


def _row_header(name: str) -> dict:
    return {"Variable": name, "Treated": "", "Control": "", "p-value": "", "SMD": ""}


# ── Per-trial table builder ────────────────────────────────────────────────────

def build_table(cohort: pd.DataFrame, trial_key: str) -> pd.DataFrame:
    meta = TRIAL_META[trial_key]
    t = cohort[cohort["arm"] == meta["treated"]].copy()
    c = cohort[cohort["arm"] == meta["control"]].copy()

    rows: list[dict] = []

    # ── Sample size ────────────────────────────────────────────────────────────
    rows.append(_row_header("Sample size"))
    rows.append({
        "Variable": "  N",
        "Treated":  f"{len(t):,}",
        "Control":  f"{len(c):,}",
        "p-value":  "",
        "SMD":      "",
    })

    # ── Demographics ───────────────────────────────────────────────────────────
    rows.append(_row_header("Demographics"))
    r = _row_cont("  Age at index, years (mean ± SD)", "age_at_index", t, c)
    if r: rows.append(r)
    r = _row_bin("  Female sex", "sex_binary", t, c)
    if r: rows.append(r)
    r = _row_bin("  Black race", "race_black", t, c)
    if r: rows.append(r)

    # ── Cardiovascular comorbidities ───────────────────────────────────────────
    rows.append(_row_header("Cardiovascular comorbidities"))
    r = _row_bin("  Atrial fibrillation", "afib", t, c)
    if r: rows.append(r)
    r = _row_bin("  Hypertension", "htn", t, c)
    if r: rows.append(r)
    r = _row_bin("  Diabetes mellitus", "dm", t, c)
    if r: rows.append(r)
    r = _row_bin("  Coronary artery disease / prior MI", "cad_mi", t, c)
    if r: rows.append(r)
    r = _row_bin("  Hyperlipidemia", "hyperlipidemia", t, c)
    if r: rows.append(r)
    r = _row_bin("  COPD", "copd", t, c)
    if r: rows.append(r)
    r = _row_bin("  Stroke", "stroke", t, c)
    if r: rows.append(r)
    r = _row_bin("  HF diagnosis in prior year", "prior_hf_code_1yr", t, c)
    if r: rows.append(r)

    # ── HF / disease severity ─────────────────────────────────────────────────
    rows.append(_row_header("Disease severity"))
    if "ef_at_index" in cohort.columns and cohort["ef_at_index"].notna().sum() > 0:
        r = _row_cont("  Ejection fraction (%) — median [IQR]", "ef_at_index", t, c, fmt="median")
        if r: rows.append(r)
    r = _row_bin("  HFrEF ICD code (5 yr)", "hfref_icd_5y", t, c)
    if r: rows.append(r)
    r = _row_bin("  HFrEF ICD code (24 mo)", "hfref_icd_24m", t, c)
    if r: rows.append(r)
    r = _row_bin("  HFrEF I50.2 subcoded (24 mo)", "hfref_icd_subcoded_i502_24m", t, c)
    if r: rows.append(r)

    # ── Additional cardiac / other conditions ─────────────────────────────────
    rows.append(_row_header("Additional conditions"))
    r = _row_bin("  Valvular heart disease (5 yr)", "valvular_disease_5y", t, c)
    if r: rows.append(r)
    r = _row_bin("  Recent MI / ACS (60 d)", "recent_mi_acs_60d", t, c)
    if r: rows.append(r)
    r = _row_bin("  Recent revascularization (60 d)", "recent_revasc_60d", t, c)
    if r: rows.append(r)
    r = _row_bin("  AV block 2°/3° (24 mo)", "av_block_2_3_24m", t, c)
    if r: rows.append(r)
    r = _row_bin("  ESRD (5 yr)", "esrd_5y", t, c)
    if r: rows.append(r)
    r = _row_bin("  Hepatic failure (5 yr)", "hepatic_failure_5y", t, c)
    if r: rows.append(r)
    r = _row_bin("  Asthma (5 yr)", "asthma_5y", t, c)
    if r: rows.append(r)

    # ── Baseline medications ───────────────────────────────────────────────────
    _med_excl = TRIAL_MED_EXCLUSIONS.get(trial_key, set())
    rows.append(_row_header("Baseline medications (90-day lookback)"))
    for label, col in [
        ("  Loop diuretic",        "loop_diuretic_90d"),
        ("  ACEi or ARB",          "acei_arb_90d"),
        ("  Aldosterone antagonist","aldosterone_antag_90d"),
        ("  Digoxin",              "digoxin_90d"),
        ("  Statin",               "statin_90d"),
        ("  Nitrate",              "nitrate_90d"),
    ]:
        if col in _med_excl:
            continue
        r = _row_bin(label, col, t, c)
        if r: rows.append(r)

    # ── ECG features ──────────────────────────────────────────────────────────
    rows.append(_row_header("ECG features at index"))
    r = _row_cont("  Heart rate (bpm)", "hr_at_index", t, c)
    if r: rows.append(r)
    r = _row_cont("  PR interval (ms)", "PR_Interval", t, c)
    if r: rows.append(r)
    r = _row_cont("  QRS duration (ms)", "QRS_Duration", t, c)
    if r: rows.append(r)
    r = _row_cont("  QTc (ms)", "QTc", t, c)
    if r: rows.append(r)

    # ── Outcomes ──────────────────────────────────────────────────────────────
    rows.append(_row_header("Outcome"))
    r = _row_bin("  All-cause death", "event_death", t, c)
    if r: rows.append(r)
    r = _row_cont("  Follow-up time (days) — median [IQR]", "time_to_death", t, c, fmt="median")
    if r: rows.append(r)

    df = pd.DataFrame(rows)
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate baseline characteristics tables")
    p.add_argument("--paradigm",  default=None, help="Path to paradigm_cohort.parquet")
    p.add_argument("--aristotle", default=None, help="Path to aristotle_cohort.parquet")
    p.add_argument("--dig",       default=None, help="Path to dig_cohort.parquet")
    p.add_argument("--rales",     default=None, help="Path to rales_cohort.parquet")
    p.add_argument("--out-dir",   required=True, help="Output directory for CSVs")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    trial_paths = {
        "paradigm":  args.paradigm,
        "aristotle": args.aristotle,
        "dig":       args.dig,
        "rales":     args.rales,
    }

    combined_dfs: list[pd.DataFrame] = []

    for trial_key, path in trial_paths.items():
        if not path:
            print(f"  [{trial_key}] skipped (no path provided)")
            continue
        p = Path(path)
        if not p.exists():
            print(f"  [{trial_key}] NOT FOUND: {p}")
            continue

        meta  = TRIAL_META[trial_key]
        label = meta["label"]
        print(f"\n{'='*60}")
        print(f"  {label}")

        cohort = pd.read_parquet(p)
        cohort["index_date"] = pd.to_datetime(cohort["index_date"])

        t_label = TREATED_LABELS[trial_key]
        c_label = CONTROL_LABELS[trial_key]
        n_t = int((cohort["arm"] == meta["treated"]).sum())
        n_c = int((cohort["arm"] == meta["control"]).sum())
        print(f"  {t_label}: {n_t:,}   {c_label}: {n_c:,}")

        table = build_table(cohort, trial_key)

        # Rename Treated/Control columns with arm labels + N
        table = table.rename(columns={
            "Treated": f"{t_label} (n={n_t:,})",
            "Control": f"{c_label} (n={n_c:,})",
        })

        csv_path = out_dir / f"baseline_{trial_key}.csv"
        table.to_csv(csv_path, index=False)
        print(f"  Saved → {csv_path}")
        print(table.to_string(index=False))

        # Tag for combined output
        table.insert(0, "Trial", label)
        combined_dfs.append(table)

    if combined_dfs:
        combined = pd.concat(combined_dfs, ignore_index=True)
        combined_path = out_dir / "baseline_all_trials.csv"
        combined.to_csv(combined_path, index=False)
        print(f"\nCombined table → {combined_path}")


if __name__ == "__main__":
    main()
