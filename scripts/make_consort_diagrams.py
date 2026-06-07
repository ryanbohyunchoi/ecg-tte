"""
trialemulation/make_consort_diagrams.py

CONSORT-style attrition flow diagrams from Stage 3 attrition.csv files.
Aggregates granular filter steps into 5 logical stages:
  1. EHR candidates identified
  2. Index date restriction
  3. Inclusion criteria  (age, HFrEF, ≥ fills, AF/loop-diuretic requirement)
  4. Exclusion criteria  (MI, CKD, hepatic, AV block, etc.)
  5. ECG required → Final analytic cohort

Usage:
    python trialemulation/make_consort_diagrams.py \
        --paradigm  .../paradigm/runs/paradigm_810d/attrition.csv \
        --aristotle .../aristotle/runs/aristotle_660d/attrition.csv \
        --dig       .../dig/runs/dig_1095d/attrition.csv \
        --rales     .../mra/rales/runs/rales_730d/attrition.csv \
        --out-dir   .../consort_figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd


# ── Trial metadata ─────────────────────────────────────────────────────────────

TRIAL_META = {
    "paradigm":  {
        "label": "PARADIGM-HF",
        "drug":  "sacubitril/valsartan vs. ACEi",
        "treated_col": "n_arnii",    "treated_label": "ARNI",
        "control_col": "n_acei",     "control_label": "ACEi",
    },
    "aristotle": {
        "label": "ARISTOTLE",
        "drug":  "apixaban vs. warfarin",
        "treated_col": "n_apixaban", "treated_label": "Apixaban",
        "control_col": "n_warfarin", "control_label": "Warfarin",
    },
    "dig": {
        "label": "DIG",
        "drug":  "digoxin vs. no digoxin",
        "treated_col": "n_treated",  "treated_label": "Digoxin",
        "control_col": "n_control",  "control_label": "No digoxin",
    },
    "rales": {
        "label": "RALES",
        "drug":  "spironolactone vs. no MRA",
        "treated_col": "n_treated",  "treated_label": "Spironolactone",
        "control_col": "n_control",  "control_label": "No MRA",
    },
}

# ── Step categorisation ────────────────────────────────────────────────────────

def _categorise(step: str) -> str:
    s = step.lower()
    if "pool" in s or "pre-filter" in s:
        return "pool"
    if "index date" in s:
        return "index"
    if any(x in s for x in [
        "age", "hfref", "adherence", "fills",
        "require af", "require atrial", "require loop",
        "require hf", "loop diuretic",
    ]):
        return "inclusion"
    if "exclude" in s:
        return "exclusion"
    if "ecg required" in s or "ecg required" in s:
        return "ecg"
    if "final" in s:
        return "final"
    return "other"


def _inclusion_bullets(steps_rows: list[tuple[str, int, int]]) -> str:
    """Build exclusion bullet list for the inclusion stage."""
    lines = []
    for step, excluded, _ in steps_rows:
        s = step.lower()
        if excluded <= 0:
            continue
        if "age" in s:
            label = "Age criteria"
        elif "hfref" in s or "ef" in s:
            label = "HFrEF criterion (EF / I50.2x)"
        elif "adherence" in s or "fills" in s:
            label = "< 2 prescription fills"
        elif "require af" in s or "require atrial" in s:
            label = "No atrial fibrillation"
        elif "require loop" in s or "loop diuretic" in s:
            label = "No loop diuretic at baseline"
        else:
            label = step.strip()
        lines.append(f"  • {label}: {excluded:,}")
    return "\n".join(lines) if lines else "  (none)"


def _exclusion_bullets(steps_rows: list[tuple[str, int, int]]) -> str:
    lines = []
    for step, excluded, _ in steps_rows:
        s = step.lower()
        if excluded <= 0:
            continue
        if "mi" in s or "acs" in s or "revasc" in s:
            label = "Recent MI/ACS/revascularisation"
        elif "hepatic" in s:
            label = "Severe hepatic failure"
        elif "angioedema" in s:
            label = "History of angioedema"
        elif "ckd" in s or "esrd" in s:
            label = "CKD stage 4+ / ESRD"
        elif "valvular" in s:
            label = "Valvular heart disease"
        elif "af" in s or "flutter" in s:
            label = "Atrial fibrillation / flutter"
        elif "av block" in s or "sick sinus" in s:
            label = "AV block / sick sinus syndrome"
        elif "hcm" in s:
            label = "Hypertrophic cardiomyopathy"
        elif "amyloid" in s:
            label = "Amyloid cardiomyopathy"
        elif "inotrope" in s:
            label = "IV inotrope use"
        else:
            label = step.strip()
        lines.append(f"  • {label}: {excluded:,}")
    return "\n".join(lines) if lines else "  (none)"


# ── Aggregate attrition into 5 stages ─────────────────────────────────────────

def _aggregate(atr: pd.DataFrame, meta: dict) -> list[dict]:
    """
    Returns list of 5 stage dicts:
      stage, label, n_total, n_treated, n_control,
      excl_total, excl_treated, excl_control, excl_detail
    """
    tc, cc = meta["treated_col"], meta["control_col"]
    tl, cl = meta["treated_label"], meta["control_label"]

    def _get(row, col):
        return int(row[col]) if col in row.index and pd.notna(row[col]) else None

    # Tag each row
    atr = atr.copy()
    atr["_cat"] = atr["step"].apply(_categorise)

    # Pool row (always first)
    pool_row = atr[atr["_cat"] == "pool"].iloc[0]
    n_pool   = int(pool_row["n_total"])
    nt_pool  = _get(pool_row, tc)
    nc_pool  = _get(pool_row, cc)

    stages: list[dict] = []

    def _stage(cat, label, detail_fn=None):
        rows = atr[atr["_cat"] == cat]
        if rows.empty:
            return None
        last = rows.iloc[-1]
        n    = int(last["n_total"])
        nt   = _get(last, tc)
        nc   = _get(last, cc)

        # entry n = last n of previous stage
        prev_n  = stages[-1]["n_total"]  if stages else n_pool
        prev_nt = stages[-1]["n_treated"] if stages else nt_pool
        prev_nc = stages[-1]["n_control"] if stages else nc_pool

        excl    = prev_n  - n
        excl_t  = (prev_nt - nt) if (nt is not None and prev_nt is not None) else None
        excl_c  = (prev_nc - nc) if (nc is not None and prev_nc is not None) else None

        # Build per-step detail for exclusion box
        detail = ""
        if detail_fn and excl > 0:
            # Collect (step, excluded_at_step) tuples within this category
            sub_rows = []
            for idx, r in rows.iterrows():
                # n entering this step = previous row's n_total
                pos = atr.index.get_loc(idx)
                prev_r = atr.iloc[pos - 1] if pos > 0 else pool_row
                ex = int(prev_r["n_total"]) - int(r["n_total"])
                sub_rows.append((str(r["step"]), ex, int(r["n_total"])))
            detail = detail_fn(sub_rows)

        return {
            "stage":      cat,
            "label":      label,
            "n_total":    n,
            "n_treated":  nt,
            "n_control":  nc,
            "excl_total": excl,
            "excl_t":     excl_t,
            "excl_c":     excl_c,
            "detail":     detail,
        }

    stages.append({
        "stage": "pool", "label": "EHR candidates identified",
        "n_total": n_pool, "n_treated": nt_pool, "n_control": nc_pool,
        "excl_total": 0, "excl_t": None, "excl_c": None, "detail": "",
    })

    for cat, label, fn in [
        ("index",     "Index date restriction applied",  None),
        ("inclusion", "Inclusion criteria applied",      _inclusion_bullets),
        ("exclusion", "Exclusion criteria applied",      _exclusion_bullets),
        ("ecg",       "ECG available within window",     None),
    ]:
        s = _stage(cat, label, fn)
        if s:
            stages.append(s)

    # Rename last stage to Final analytic cohort
    stages[-1]["label"] = "Final analytic cohort"
    return stages


# ── Drawing ────────────────────────────────────────────────────────────────────

BOX_W     = 0.52
BOX_H_MIN = 0.10
X_MAIN    = 0.04
X_EXCL    = 0.62
EXCL_W    = 0.36
FONT_MAIN = 10.0
FONT_EXCL = 9.0
FONT_DETAIL = 8.5


def _measure_excl_h(detail: str, base_h: float = BOX_H_MIN) -> float:
    n_lines = detail.count("\n") + 2  # header + lines
    return max(base_h, n_lines * 0.022 + 0.02)


def draw_consort_5stage(
    stages: list[dict],
    meta: dict,
    ax: plt.Axes,
) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        f"{meta['label']}\n({meta['drug']})",
        fontsize=13, fontweight="bold", pad=6,
    )

    tl, cl = meta["treated_label"], meta["control_label"]
    n_stages = len(stages)

    # Pre-compute exclusion box heights to allocate vertical space
    excl_heights = []
    for s in stages:
        if s["excl_total"] > 0 and s["detail"]:
            excl_heights.append(_measure_excl_h(s["detail"]))
        else:
            excl_heights.append(BOX_H_MIN if s["excl_total"] > 0 else 0)

    # Total vertical space consumed by exclusion boxes + main boxes
    # Distribute y evenly across stages
    y_top    = 0.94
    y_bottom = 0.03
    total_h  = y_top - y_bottom
    slot_h   = total_h / n_stages

    def _nt_nc(s: dict) -> str:
        nt, nc = s["n_treated"], s["n_control"]
        if nt is not None and nc is not None:
            return f"{tl}: {nt:,}  |  {cl}: {nc:,}"
        return ""

    def _main_box(ax, x, y_center, w, h, text, is_final=False):
        fc = "#ffffff"
        ec = "#000000"
        lw = 1.8 if is_final else 1.1
        rect = mpatches.FancyBboxPatch(
            (x, y_center - h / 2), w, h,
            boxstyle="round,pad=0.015",
            facecolor=fc, edgecolor=ec, linewidth=lw,
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y_center, text,
                ha="center", va="center", fontsize=FONT_MAIN,
                transform=ax.transAxes, clip_on=False,
                multialignment="center")

    def _excl_box(ax, x, y_center, w, h, header, detail):
        rect = mpatches.FancyBboxPatch(
            (x, y_center - h / 2), w, h,
            boxstyle="round,pad=0.015",
            facecolor="#ffffff", edgecolor="#000000", linewidth=0.9,
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(rect)
        full_text = header + ("\n" + detail if detail else "")
        ax.text(x + w / 2, y_center, full_text,
                ha="center", va="center", fontsize=FONT_EXCL,
                transform=ax.transAxes, clip_on=False,
                multialignment="left", color="#000000")

    def _arrow_down(ax, x, y1, y2):
        ax.annotate("", xy=(x, y2), xytext=(x, y1),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color="#000000", lw=1.0))

    def _arrow_right(ax, x1, y, x2):
        ax.annotate("", xy=(x2, y), xytext=(x1, y),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color="#000000", lw=0.9))

    y_centers = []
    for i in range(n_stages):
        y_centers.append(y_top - (i + 0.5) * slot_h)

    for i, s in enumerate(stages):
        is_final = (i == n_stages - 1)
        yc = y_centers[i]
        h  = BOX_H_MIN

        n_txt  = f"n = {s['n_total']:,}"
        arm_txt = _nt_nc(s)
        label  = s["label"]
        main_text = f"{label}\n{n_txt}" + (f"\n{arm_txt}" if arm_txt else "")

        _main_box(ax, X_MAIN, yc, BOX_W, h, main_text, is_final=is_final)

        # Down arrow
        if i < n_stages - 1:
            _arrow_down(ax,
                        X_MAIN + BOX_W / 2,
                        yc - h / 2,
                        y_centers[i + 1] + BOX_H_MIN / 2)

        # Exclusion box (between this box and next)
        if i < n_stages - 1 and s["excl_total"] > 0:
            excl_yc = yc - h / 2 - (y_centers[i + 1] - yc) * 0.45
            # horizontal line from mid-arrow to exclusion box
            arrow_x = X_MAIN + BOX_W / 2
            _arrow_right(ax, arrow_x, excl_yc, X_EXCL)

            excl_t = s["excl_t"]
            excl_c = s["excl_c"]
            if excl_t is not None and excl_c is not None:
                header = (f"Excluded: {s['excl_total']:,}\n"
                          f"({tl}: {excl_t:,}  |  {cl}: {excl_c:,})")
            else:
                header = f"Excluded: {s['excl_total']:,}"

            detail = s["detail"]
            excl_h = _measure_excl_h(detail) if detail else BOX_H_MIN
            _excl_box(ax, X_EXCL, excl_yc, EXCL_W, excl_h, header, detail)


# ── Per-trial and combined figures ────────────────────────────────────────────

def make_consort(path: str, trial_key: str, out_dir: Path) -> bool:
    meta = TRIAL_META[trial_key]
    p = Path(path)
    if not p.exists():
        print(f"  [{trial_key}] NOT FOUND: {p}")
        return False

    atr    = pd.read_csv(p)
    stages = _aggregate(atr, meta)
    print(f"  [{meta['label']}] {len(stages)} stages, "
          f"final n={stages[-1]['n_total']:,}")

    fig, ax = plt.subplots(figsize=(7, 10))
    draw_consort_5stage(stages, meta, ax)
    plt.tight_layout()
    out_path = out_dir / f"consort_{trial_key}.png"
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {out_path}")
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CONSORT flow diagrams from attrition CSVs")
    p.add_argument("--paradigm",  default=None)
    p.add_argument("--aristotle", default=None)
    p.add_argument("--dig",       default=None)
    p.add_argument("--rales",     default=None)
    p.add_argument("--out-dir",   required=True)
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

    done = {k: v for k, v in trial_paths.items()
            if v and make_consort(v, k, out_dir)}

    # Combined 2×2
    available = [k for k in ["paradigm", "aristotle", "dig", "rales"] if k in done]
    if len(available) >= 2:
        fig, axes = plt.subplots(2, 2, figsize=(14, 20))
        for i, trial_key in enumerate(available):
            meta   = TRIAL_META[trial_key]
            atr    = pd.read_csv(Path(done[trial_key]))
            stages = _aggregate(atr, meta)
            draw_consort_5stage(stages, meta, axes.flatten()[i])
        for j in range(len(available), 4):
            axes.flatten()[j].axis("off")
        plt.tight_layout(h_pad=4, w_pad=3)
        combined_path = out_dir / "consort_combined.png"
        fig.savefig(combined_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"\nCombined → {combined_path}")


if __name__ == "__main__":
    main()
