"""
scripts/stage5_meta.py

Stage 5: Cross-trial meta-analysis (RCT-DUPLICATE style).

For each trial, compares each comparator-ladder method's emulated HR
(from stage4's results_summary.csv) against the trial's published RCT HR
(configs/<trial>.yaml: trial.published_hr / published_hr_ci). Aggregates
across all trials, per method:

  - Pearson correlation (log HR_emulated vs log HR_published)
  - Mean / variance of log-HR difference vs published (bias + dispersion)
  - Standardized estimate difference (z-score, pooled SE) vs published
  - Regulatory agreement (same benefit/harm/null conclusion as the RCT)
  - CI overlap rate

Methods compared (matched by results_summary.csv "label"):
  Unadjusted Cox, Adjusted Cox (age,sex,race), Structured PSM,
  ECG-NN PRIMARY, PS+ECG-NN (hybrid).

Trials with published_hr/published_hr_ci == null (e.g. lead2) or missing
results_summary.csv (failed/skipped trials) are skipped with a NOTE.

Usage:
    python scripts/stage5_meta.py \\
        --output-root /home/rbc58/mnt/ecg-tte \\
        --config-dir configs \\
        --run-name default
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.stats import pearsonr

Z95 = 1.959963984540054

METHODS = [
    "Unadjusted Cox",
    "Adjusted Cox (age,sex,race)",
    "Structured PSM",
    "ECG-NN PRIMARY",
    "PS+ECG-NN",
]
SHORT = {
    "Unadjusted Cox": "Unadj",
    "Adjusted Cox (age,sex,race)": "Adj",
    "Structured PSM": "PSM",
    "ECG-NN PRIMARY": "ECG-NN",
    "PS+ECG-NN": "Hybrid",
}


def _match_method(label: str) -> str | None:
    if label == "Unadjusted Cox":
        return "Unadjusted Cox"
    if label == "Adjusted Cox (age,sex,race)":
        return "Adjusted Cox (age,sex,race)"
    if label == "Structured PSM":
        return "Structured PSM"
    if label == "PS+ECG-NN":
        return "PS+ECG-NN"
    if label.startswith("ECG-NN"):
        return "ECG-NN PRIMARY"
    return None


def _classify(ci_low: float, ci_high: float) -> str:
    """RCT-DUPLICATE-style direction-of-effect bucket from a 95% CI."""
    if ci_high < 1:
        return "benefit"
    if ci_low > 1:
        return "harm"
    return "null"


def load_trial_meta(cfg_path: Path) -> dict | None:
    cfg = yaml.safe_load(cfg_path.read_text())
    trial = cfg.get("trial", {})
    hr = trial.get("published_hr")
    ci = trial.get("published_hr_ci")
    if hr is None or ci is None:
        return None
    return {
        "trial_key":       trial["key"],
        "trial_name":      trial["name"],
        "published_hr":      float(hr),
        "published_ci_low":  float(ci[0]),
        "published_ci_high": float(ci[1]),
    }


def collect_results(output_root: Path, cfg_paths: list[Path], run_name: str) -> pd.DataFrame:
    rows = []
    for cfg_path in cfg_paths:
        meta = load_trial_meta(cfg_path)
        if meta is None:
            print(f"  SKIP {cfg_path.stem}: no published_hr/published_hr_ci")
            continue

        rs_path = output_root / meta["trial_key"] / "runs" / run_name / "results_summary.csv"
        if not rs_path.is_file():
            print(f"  SKIP {meta['trial_key']}: no results_summary.csv ({rs_path})")
            continue

        rs = pd.read_csv(rs_path)
        log_pub   = np.log(meta["published_hr"])
        se_pub    = (np.log(meta["published_ci_high"]) - np.log(meta["published_ci_low"])) / (2 * Z95)
        pub_class = _classify(meta["published_ci_low"], meta["published_ci_high"])

        for _, r in rs.iterrows():
            method = _match_method(str(r.get("label", "")))
            if method is None:
                continue
            hr, ci_low, ci_high = r.get("hr"), r.get("ci_low"), r.get("ci_high")
            if pd.isna(hr) or pd.isna(ci_low) or pd.isna(ci_high) or hr <= 0 or ci_low <= 0:
                continue

            log_hr      = np.log(hr)
            se          = (np.log(ci_high) - np.log(ci_low)) / (2 * Z95)
            log_hr_diff = log_hr - log_pub
            se_pooled   = np.sqrt(se ** 2 + se_pub ** 2)
            em_class    = _classify(ci_low, ci_high)

            rows.append({
                "trial_key":         meta["trial_key"],
                "trial_name":        meta["trial_name"],
                "method":            method,
                "n":                 r.get("n"),
                "hr":                hr,
                "ci_low":            ci_low,
                "ci_high":           ci_high,
                "published_hr":      meta["published_hr"],
                "published_ci_low":  meta["published_ci_low"],
                "published_ci_high": meta["published_ci_high"],
                "log_hr":            log_hr,
                "log_published_hr":  log_pub,
                "log_hr_diff":       log_hr_diff,
                "abs_log_hr_diff":   abs(log_hr_diff),
                "se":                se,
                "z_pooled":          log_hr_diff / se_pooled if se_pooled > 0 else np.nan,
                "emulated_class":    em_class,
                "published_class":   pub_class,
                "agree":             em_class == pub_class,
                "ci_overlap":        max(ci_low, meta["published_ci_low"]) <= min(ci_high, meta["published_ci_high"]),
            })

    return pd.DataFrame(rows)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []
    for method in METHODS:
        sub = df[df["method"] == method]
        if sub.empty:
            continue
        if len(sub) >= 3:
            r, p = pearsonr(sub["log_hr"], sub["log_published_hr"])
        else:
            r, p = np.nan, np.nan
        summary_rows.append({
            "method":                    method,
            "n_trials":                  len(sub),
            "pearson_r":                 r,
            "pearson_p":                 p,
            "mean_log_hr_diff":          sub["log_hr_diff"].mean(),
            "mean_abs_log_hr_diff":      sub["abs_log_hr_diff"].mean(),
            "var_log_hr_diff":           sub["log_hr_diff"].var(ddof=1) if len(sub) > 1 else np.nan,
            "mean_z_pooled":             sub["z_pooled"].mean(),
            "var_z_pooled":              sub["z_pooled"].var(ddof=1) if len(sub) > 1 else np.nan,
            "regulatory_agreement_rate": sub["agree"].mean(),
            "ci_overlap_rate":           sub["ci_overlap"].mean(),
        })
    return pd.DataFrame(summary_rows)


# ── Plots ───────────────────────────────────────────────────────────────────

def plot_scatter(df: pd.DataFrame, path: Path) -> None:
    methods = [m for m in METHODS if m in df["method"].unique()]
    n = len(methods)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.2), squeeze=False)
    axes = axes[0]

    all_vals = np.concatenate([df["log_hr"].values, df["log_published_hr"].values])
    lo, hi = np.nanmin(all_vals) - 0.2, np.nanmax(all_vals) + 0.2

    for ax, method in zip(axes, methods):
        sub = df[df["method"] == method]
        yerr = np.vstack([
            sub["log_hr"] - np.log(sub["ci_low"]),
            np.log(sub["ci_high"]) - sub["log_hr"],
        ])
        ax.errorbar(sub["log_published_hr"], sub["log_hr"], yerr=yerr, fmt="o",
                     color="#2166ac", ecolor="#aac4dd", capsize=3, alpha=0.8)
        ax.plot([lo, hi], [lo, hi], "k--", lw=1, alpha=0.6)
        ax.axhline(0, color="gray", lw=0.5)
        ax.axvline(0, color="gray", lw=0.5)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)

        if len(sub) >= 3:
            r, _ = pearsonr(sub["log_hr"], sub["log_published_hr"])
            r_str = f"r={r:.2f}"
        else:
            r_str = "r=n/a"
        ax.set_title(f"{SHORT.get(method, method)} (n={len(sub)}, {r_str})")
        ax.set_xlabel("log(published HR)")
        ax.set_ylabel("log(emulated HR)")

    fig.suptitle("Emulated vs Published HR (log scale, error bars = emulated 95% CI)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_variance(summary: pd.DataFrame, path: Path) -> None:
    labels = [SHORT.get(m, m) for m in summary["method"]]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, summary["var_log_hr_diff"], color="#4393c3")
    axes[0].set_title("Variance of log-HR difference vs published\n(lower = more consistent with RCT)")
    axes[0].set_ylabel("Var(log HR$_{emulated}$ - log HR$_{published}$)")
    axes[0].tick_params(axis="x", rotation=30)

    axes[1].bar(labels, summary["mean_abs_log_hr_diff"], color="#d6604d")
    axes[1].set_title("Mean |log-HR difference| vs published\n(lower = closer to RCT)")
    axes[1].set_ylabel("Mean |log HR$_{emulated}$ - log HR$_{published}$|")
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_zscore(df: pd.DataFrame, path: Path) -> None:
    methods = [m for m in METHODS if m in df["method"].unique()]
    data   = [df.loc[df["method"] == m, "z_pooled"].dropna().values for m in methods]
    labels = [SHORT.get(m, m) for m in methods]

    fig, ax = plt.subplots(figsize=(2 + 1.3 * len(methods), 4.5))
    ax.boxplot(data, labels=labels, showmeans=True)
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.axhline(1.96, color="red", ls=":", lw=0.8)
    ax.axhline(-1.96, color="red", ls=":", lw=0.8)
    ax.set_ylabel("Standardized difference\n(log HR$_{emulated}$ - log HR$_{published}$) / pooled SE")
    ax.set_title("Standardized estimate difference vs published RCT, by method")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-root", default="/home/rbc58/mnt/ecg-tte")
    ap.add_argument("--config-dir", default="configs")
    ap.add_argument("--run-name", default="default")
    ap.add_argument("--output-dir", default=None,
                    help="Default: <output-root>/_meta/<run-name>")
    ap.add_argument("--trials", nargs="*", default=None,
                    help="Restrict to these trial keys (default: all configs)")
    args = ap.parse_args()

    output_root = Path(args.output_root)
    out = Path(args.output_dir) if args.output_dir else output_root / "_meta" / args.run_name
    out.mkdir(parents=True, exist_ok=True)

    cfg_paths = sorted(p for p in Path(args.config_dir).glob("*.yaml") if "_schema" not in p.name)
    if args.trials:
        cfg_paths = [p for p in cfg_paths if p.stem in args.trials]

    df = collect_results(output_root, cfg_paths, args.run_name)
    if df.empty:
        print("No results found — nothing to aggregate.")
        return

    df.to_csv(out / "meta_results.csv", index=False)
    print(f"\n  meta_results.csv saved → {out} "
          f"({len(df)} rows, {df['trial_key'].nunique()} trials)")

    summary = build_summary(df)
    summary.to_csv(out / "meta_summary.csv", index=False)
    print(f"\n  meta_summary.csv:")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    plot_scatter(df, out / "meta_scatter.png")
    plot_variance(summary, out / "meta_variance.png")
    plot_zscore(df, out / "meta_zscore.png")
    print(f"\n  Plots saved → {out}")


if __name__ == "__main__":
    main()
