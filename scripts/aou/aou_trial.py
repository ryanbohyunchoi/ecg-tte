"""AoU trial object: the attributes paper2_grid.task / v16_engine.run_cell use, built from trials/<n>/ (aou_build.py).

Same construction as v13_common.Trial + v16_engine.load_trial, without the ECG:
  keys      cohort persons with a baseline row, a panel row and a CLMBR-T embedding (Yale also required ECG and ECG
            phenotype rows; AoU has no ECG, so the analysed populations are not restricted to people with an ECG)
  cov       completed baseline, imputation `imputation` (1..5), lvef absent; demo / dxc / meds / util / phys as in Trial
  X_dx      demo + diagnosis columns; X_core = all core columns (PS-Clinical without LVEF)
  dx10      PS-CVD5 / CVD10 flag columns (aou_build.step_dx10)
  lv, hd()  hdPS levels from pool A of the panel (split seed 0, exposure features removed), hdps_rank on treatment only
  clm_pc    64 PCs of CLMBR-T within the trial (eval_longtail_balance.pcs); shuffle_perm = default_rng(424242)
  y_t, y_e, y_ok, horizon   primary outcome at the trial horizon (v13_common.outcomes rule); censoring variant selectable
  rb, rs    RCT benchmark (v13_common.bench)
  H         held-out components (heldout_matrix below)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import aou_common as AC

UTIL = {"outpatient_visits", "ed_encounters", "hospital_admissions"}

# held-out items: (column, label, group). EHR items keep the Yale column names; survey items are AoU-only.
EHR_VARS = [
    ("smd_obs_sbp", "Systolic BP", "Vitals & core labs"), ("smd_obs_dbp", "Diastolic BP", "Vitals & core labs"),
    ("smd_obs_heart_rate", "Heart rate", "Vitals & core labs"), ("smd_obs_bmi", "BMI", "Vitals & core labs"),
    ("smd_obs_creatinine", "Creatinine", "Vitals & core labs"), ("smd_obs_potassium", "Potassium", "Vitals & core labs"),
    ("smd_obs_sodium", "Sodium", "Vitals & core labs"), ("smd_obs_hemoglobin", "Hemoglobin", "Vitals & core labs"),
    ("pp_BNP__ntprobnp", "NT-proBNP", "Other labs"), ("pp_LAB__albumin", "Albumin", "Other labs"), ("pp_LAB__bun", "BUN", "Other labs"),
    ("pp_LAB__egfr", "eGFR", "Other labs"), ("pp_LAB__glucose", "Glucose", "Other labs"), ("pp_LAB__hba1c", "HbA1c", "Other labs"),
    ("pp_LAB__hs_troponin_t", "hs-TnT", "Other labs"), ("pp_LAB__ldl", "LDL", "Other labs"),
    ("pp_LAB__platelets", "Platelets", "Other labs"), ("pp_LAB__wbc", "WBC", "Other labs"),
]
CODED_VARS = [("mean_meds", "Medications (mean over classes)", "Coded record"), ("mean_util", "Healthcare use (mean)", "Coded record"),
              ("B_mean", "Held-out dx/drug/procedure codes (mean)", "Coded record")]


def survey_vars():
    from aou_build import SURVEY_ITEMS
    return [(c, lab, "Survey: lifestyle & social") for c, (_, lab) in SURVEY_ITEMS.items()]


def survey_vars_other(tag="any"):
    return [(f"{c}__{tag}", f"{lab} ({tag} time)", f"{g} ({tag} time)") for c, lab, g in survey_vars()]


def all_vars():
    """every item a cell stores: coded (secondary), EHR, survey (primary timing), survey (other timing, sensitivity)."""
    return CODED_VARS + EHR_VARS + survey_vars() + survey_vars_other()


def var_components(H: pd.DataFrame, VARS) -> dict:
    """= v16_engine.var_components with the item list as a parameter (sv_ items are their own component)."""
    cc = list(H.columns)
    out = {}
    for c, _, _ in VARS:
        if c == "mean_meds":
            out[c] = [x for x in cc if x.startswith("meds::")]
        elif c == "mean_util":
            out[c] = [x for x in cc if x.startswith("util::")]
        elif c == "B_mean":
            out[c] = [x for x in cc if x.startswith("B::")]
        elif c == "smd_prog_full":
            out[c] = [x for x in cc if x == "prog_full"]
        elif c.startswith("smd_obs_"):
            out[c] = [x for x in cc if x == "obs_" + c[len("smd_obs_"):]]
        else:
            out[c] = [x for x in cc if x == c]
    return out


def pools(dic: pd.DataFrame, split_seed: int = 0):
    """Panel features split in halves per domain (v13_common.Trial / v16_engine.heldout_matrix, same rng use)."""
    rng = np.random.default_rng(split_seed)
    pool = {}
    for dom, grp in dic.groupby("domain"):
        f = grp.feature.to_numpy().copy()
        rng.shuffle(f)
        pool[dom] = (f[: len(f) // 2], f[len(f) // 2:])
    return pool


class AouTrial:
    def __init__(self, n: str, imputation: int = 1, survey: str = "pre", censoring: str = "last_ehr", split_seed: int = 0):
        from eval_longtail_balance import hdps_levels, pcs
        from trial_specs import HORIZON_MONTHS
        from v13_common import bench
        D = AC.trial_dir(n)
        self.n = n
        roles = json.loads((D / "baseline" / "roles.json").read_text())
        self.roles, self.key = roles, roles["trial"]
        cov = pd.read_parquet(D / "baseline" / f"restricted_completed_{imputation:02d}.parquet").set_index("patient_key")
        t_s = cov.pop("treated").astype(int)
        core = [c for c in roles["core"] if c in cov]
        cov = cov[core].astype(float)
        panel = pd.read_parquet(D / "panel" / "restricted_panel.parquet").set_index("patient_key")
        C = self._clmbr(D)
        common = cov.index.intersection(panel.index).intersection(C.index).sort_values()
        self.keys = common
        self.t = t_s.loc[common].to_numpy()
        self.cov = cov.loc[common]
        self.core = core
        self.clm_raw = C.loc[common].to_numpy(float)
        self.clm_pc = pcs(self.clm_raw, 64) if len(common) else np.zeros((0, 64))
        self.shuffle_perm = np.random.default_rng(AC.SEED_SHUFFLE).permutation(len(common))
        phys = [c for c in roles.get("heldout_physiology", []) if c in cov]
        meds = [c for c in core if c.endswith("_order")]
        dxc = [c for c in core if c not in set(roles["demo"]) | set(phys) | set(meds) | UTIL and c != "pci_index_30d"]
        self.phys, self.meds, self.util = phys, meds, [c for c in core if c in UTIL]
        self.demo = [c for c in roles["demo"] if c in cov]
        self.dxc = dxc
        self.X_dx = self.cov[self.demo + dxc].to_numpy()
        self.X_core = self.cov.to_numpy()
        DX = pd.read_parquet(D / "dx10" / "restricted_dx10.parquet").set_index("patient_key").reindex(common)
        self.dx10 = DX
        # hdPS pool A (v13_common.Trial)
        panel = panel.loc[common]
        dic = pd.read_csv(D / "panel" / "panel_dictionary.csv")
        pool = pools(dic, split_seed)
        Af = [f for a, _ in pool.values() for f in a]
        Af = Af + [f.replace("lab_", "labn_") for f in Af if f.startswith("lab_")]
        expo = set(roles.get("exposure_features", []))
        Af = [f for f in Af if f not in expo]
        is_code = lambda f: f.split("_")[0] in ("dx", "rx", "px")  # noqa: E731
        codesA = [f for f in Af if is_code(f)]
        counts_panel = bool(len(codesA) and panel[codesA].max().max() > 1)
        self.lv = pd.concat([hdps_levels(panel[codesA], binary_only=not counts_panel),
                             hdps_levels(panel[[f for f in Af if f.startswith("labn_")]], binary_only=True)], axis=1)
        self._panel, self._pool, self._expo = panel, pool, expo
        # outcomes (v13_common.outcomes rule)
        O = pd.read_parquet(D / "outcomes" / "restricted_outcomes.parquet").set_index("patient_key").reindex(common)
        H = int(round(HORIZON_MONTHS[self.key] * 30.4375))
        tc, ec = ("t_primary", "e_primary") if censoring == "last_ehr" else ("t_primary_admin", "e_primary_admin")
        self.y_ok = (O[tc].notna() & (O.get("exclude_phase2", 0) == 0)).to_numpy()
        self.y_t = np.minimum(O[tc].to_numpy(float), H)
        self.y_e = ((O[ec] == 1) & (O[tc] <= H)).to_numpy(int)
        # censoring sensitivity (the Yale rule: administrative end only), fitted on the same matched sample
        self.y_t2 = np.minimum(O["t_primary_admin"].to_numpy(float), H)
        self.y_e2 = ((O["e_primary_admin"] == 1) & (O["t_primary_admin"] <= H)).to_numpy(int)
        self.horizon = H
        self.rb, self.rs = bench(self.key)
        self.H = self.heldout(D, survey)
        self.flags_path = D / "flags" / "restricted_flags.parquet"

    @staticmethod
    def _clmbr(D: Path) -> pd.DataFrame:
        fs = sorted((D / "clmbr").glob("restricted_embeddings_*.parquet"))
        if not fs:
            raise FileNotFoundError("no CLMBR-T embeddings (run aou_build.py encode)")
        d = pd.concat([pd.read_parquet(f, columns=["patient_key", "embedding"]) for f in fs])
        d = d.drop_duplicates("patient_key")
        return pd.DataFrame(np.stack(d.embedding.to_numpy()), index=d.patient_key.astype(str).values)

    def hd(self, k=200, t=None, rows=None):
        from eval_longtail_balance import hdps_rank
        lv = self.lv if rows is None else self.lv.iloc[rows]
        tt = self.t if t is None else t
        r = hdps_rank(lv.reset_index(drop=True), tt)[:k]
        return lv[r].to_numpy(float)

    def heldout(self, D: Path, survey: str) -> pd.DataFrame:
        """= v16_engine.heldout_matrix without the prognostic score and echo; + AoU survey items."""
        keys = self.keys
        cols = {}
        for c in self.meds:
            cols[f"meds::{c}"] = self.cov[c].to_numpy(float)
        for c in self.util:
            cols[f"util::{c}"] = self.cov[c].to_numpy(float)
        Bf = [f for _, b in self._pool.values() for f in b]
        Bf = Bf + [f.replace("lab_", "labn_") for f in Bf if f.startswith("lab_")]
        Bf = [f for f in Bf if f not in self._expo]
        is_code = lambda f: f.split("_")[0] in ("dx", "rx", "px")  # noqa: E731
        for f in Bf:
            v = self._panel[f].to_numpy(float)
            cols[f"B::{f}"] = (v > 0).astype(float) if is_code(f) else v
        obs = pd.read_parquet(D / "baseline" / "restricted_baseline_observed.parquet").set_index("patient_key").reindex(keys)
        rep_ok = [c for c in self.roles["report_covariates"] if c in self.cov]
        obs_cols = [c for c in dict.fromkeys(rep_ok + self.roles.get("heldout_physiology", [])) if c in obs]
        want_obs = {c[len("smd_obs_"):] for c, _, _ in EHR_VARS if c.startswith("smd_obs_")}
        for c in obs_cols:
            if c in want_obs and obs[c].isna().any():  # v16_engine quirk kept: only if the column has missing values
                cols[f"obs_{c}"] = obs[c].to_numpy(float)
        PP = pd.read_parquet(D / "labs" / "restricted_physiology_panel.parquet").set_index("patient_key").reindex(keys)
        for c, _, _ in EHR_VARS:
            if c.startswith("pp_") and c[3:] in PP:
                cols[c] = pd.to_numeric(PP[c[3:]], errors="coerce").to_numpy(float)
        other = "any" if survey == "pre" else "pre"
        for tag, suffix in ((survey, ""), (other, "__" + other)):  # primary timing as sv_<item>; the other as sv_<item>__<tag>
            SV = pd.read_parquet(D / "survey" / f"restricted_survey_{tag}.parquet").set_index("patient_key").reindex(keys)
            for c, _, _ in survey_vars():
                if c in SV:
                    cols[c + suffix] = SV[c].to_numpy(float)
        return pd.DataFrame(cols, index=keys)

    def flags_matrix(self, min_prev=0.01):
        """= paper2_grid.flags_matrix (count > 0, ICD-10 3-character, exposure features removed, 1 % <= prevalence < 1)."""
        import re
        W = pd.read_parquet(self.flags_path).set_index("patient_key").reindex(self.keys)
        B = (W.fillna(0) > 0).astype(float)
        cols = [c for c in B.columns if re.match(r"^dx_[A-Z][0-9][0-9A-Z]$", c) and c not in self._expo]
        B = B[cols]
        prev = B.mean()
        keep = prev.index[(prev >= min_prev) & (prev < 1.0)]
        return B[keep].to_numpy(float), list(keep)
