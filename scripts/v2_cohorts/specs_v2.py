"""Spec-v2 cohort rules (exclusions from the version 1 analysed cohorts) and outcome re-definitions.

scripts/trial_specs.py is unchanged; this file declares the v2 deltas only. Every rule is an EXCLUSION evaluated on data on
or before index (no patient is admitted, no index date moves). Sources are in docs/v2_cohorts/COHORT_FIXES.md.

Rule kinds
  age      exact age at index outside [lo, hi] (builder age formula)
  num      latest plausible value in [index - lookback, index - 1] (flags.MEASURE; 90 d labs/vitals, 365 d BMI) violates the
           published bound. PRIMARY: an unknown value passes (build_trial_cohort convention). SENSITIVITY (v2meas): for the
           entry bounds (HbA1c window, BP entry (inclusion) bounds of LIFE / INSIGHT / ASCOT-BPLA / ALLHAT / VALUE, natriuretic-peptide threshold, PARADIGM-HF LVEF <= 35%, PROVE IT
           cholesterol cap; ENTRY_PREFIX) and the COMET LVEF restriction the value must be measured, otherwise the patient
           is excluded; safety-type exclusions keep "unknown passes".
  flag     data-check flag(s) (scripts/v1_criteria_check/s2_flags.py, audits/claude-v1-criteria/flags) OR-ed
Outcome re-definitions (flags.py outcome; not exclusions): AMPLIFY, LODESTAR, PROVE IT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

import v2common as K


@dataclass
class Rule:
    rid: str
    kind: str              # age | num | flag
    fix: int               # task fix number 1-4 (1 numeric bound, 2 age, 3 washout / class, 4 gate / population)
    text: str              # plain-language rule
    source: str            # citation key (COHORT_FIXES.md)
    fn: Callable = None    # (M, F) -> (violates: bool array, measured: bool array or None)
    meas_fn: Callable = None  # optional stricter version for v2meas (M, F) -> bool array
    cols: list = field(default_factory=list)

    @property
    def entry(self):
        """entry (population-defining inclusion) bound: the v2meas sensitivity requires its value to be measured."""
        return self.kind == "num" and self.rid.startswith(ENTRY_PREFIX)

    def evaluate(self, M, F):
        if self.kind == "flag":
            miss = [c for c in self.cols if c not in F]
            assert not miss, (self.rid, miss)
            d = F[self.cols].fillna(False).astype(bool).any(axis=1).to_numpy()
            dm = d | self.meas_fn(M, F) if self.meas_fn else d
            return d, dm
        v, meas = self.fn(M, F)
        v = np.asarray(v, bool)
        if meas is None or not self.entry:
            return v, v
        return v, v | ~np.asarray(meas, bool)


# entry bounds (v2meas requires the value measured); safety-type exclusions (renal, Hb, platelets, ALT, BMI, HR, EF
# exclusions) keep "unknown passes" in every variant
ENTRY_PREFIX = ("hba1c", "bp_life", "bp_insight", "bp_ascot", "bp_allhat", "bp_value", "natriuretic", "ntprobnp", "lvef_le35",
                "tc_le240")


# ---------------------------------------------------------------- builders
def age(lo=None, hi=None, src="", fix=2):
    txt = f"age {lo if lo is not None else ''}-{hi if hi is not None else ''}"
    def fn(M, F):
        a = M.age.to_numpy(float)
        bad = np.zeros(len(a), bool)
        if lo is not None:
            bad |= a < lo
        if hi is not None:
            bad |= a > hi
        return bad, None
    return Rule(f"age_{lo}_{hi}", "age", fix, f"exclude if {txt} not met (age at index)", src, fn)


def num(rid, measure, lo=None, hi=None, src="", text="", when=None, fix=1):
    """exclude if measured and value < lo or value > hi (bounds are the inclusion range; None = open).
    when: optional (M) -> bool array restricting the rule to a subgroup (others pass)."""
    def fn(M, F):
        x = M[measure].to_numpy(float)
        ok = np.isfinite(x)
        bad = np.zeros(len(x), bool)
        if lo is not None:
            bad |= ok & (x < lo)
        if hi is not None:
            bad |= ok & (x > hi)
        if when is not None:
            w = np.asarray(when(M), bool)
            return bad & w, ok | ~w
        return bad, ok
    return Rule(rid, "num", fix, text or f"{measure} in [{lo}, {hi}]", src, fn)


def custom(rid, fn, text, src, fix=1):
    return Rule(rid, "num", fix, text, src, fn)


def flag(rid, cols, text, src, fix, meas_fn=None):
    return Rule(rid, "flag", fix, text, src, cols=cols, meas_fn=meas_fn)


# ---------------------------------------------------------------- rule table (filled per trial)
RULES: dict[str, list[Rule]] = {n: [] for n in K.ALL}


def rules(n):
    return RULES[n]


# ---------------------------------------------------------------- aggregate counting (suppressed)
def _share(k, n):
    return K.pct(k, n)


def count_row(n, r, t, d_main, d_meas):
    t = np.asarray(t)
    out = dict(trial=n, label=K.NAME[n], rule=r.rid, kind=r.kind, fix=r.fix, text=r.text, source=r.source, n=len(t))
    for lab, d in (("v2", d_main), ("v2meas", d_meas)):
        out[f"pct_removed_{lab}"] = _share(d.sum(), len(d))
        for a in (1, 0):
            m = t == a
            out[f"pct_removed_{lab}_arm{a}"] = _share(d[m].sum(), m.sum())
    return out


def count_trial(n, t, d2, dm, rids):
    t = np.asarray(t)
    out = dict(trial=n, label=K.NAME[n], n_rules=len(rids), rules=";".join(rids), n_analysed=K.sup(len(t)))
    for lab, d in (("v2", d2), ("v2meas", dm)):
        out[f"pct_removed_{lab}"] = _share(d.sum(), len(d))
        for a in (1, 0):
            m = t == a
            out[f"pct_removed_{lab}_arm{a}"] = _share(d[m].sum(), m.sum())
        small = any(1 <= d[t == a].sum() < K.MIN_CELL or 1 <= (~d[t == a]).sum() < K.MIN_CELL for a in (1, 0))
        out[f"n_retained_{lab}"] = "suppressed" if small else K.sup((~d).sum())
    return out


# ================================================================ fixes 3-4: class washouts and gate / population fixes
# (data-check flags, scripts/v1_criteria_check/s2_flags.py; windows as there: drug orders in [index - 365, index])
def _not_measured_ef(M, F):
    return ~F["ef_measured"].fillna(False).astype(bool).to_numpy()


DC = "TRIAL_CRITERIA_CHECK"
RULES["comet"] += [
    flag("comet_succinate_365", ["fx_comet_succinate"], "exclude metoprolol succinate-named JDAT order in [index-365, index] "
         "(prior/concurrent succinate; both arms)", DC + "; COMET", 3),
    flag("comet_lvef_le35", ["fx_comet_lvef35"], "exclude latest echo EF > 35% in [index-365, index-1] (unknown passes; "
         "v2meas: EF must be measured)", "COMET (LVEF <= 35%)", 4, meas_fn=_not_measured_ef),
]
RULES["elite-ii"] += [flag("arni_365", ["fx_arni"], "exclude ARNI (sacubitril/entresto) order in [index-365, index], both arms",
                           DC + "; ELITE II (ACEi-naive)", 3)]
RULES["valiant"] += [
    flag("arni_365", ["fx_arni"], "exclude ARNI order in [index-365, index], both arms", DC + "; VALIANT", 3),
    flag("valiant_lvd_or_hf", ["fx_valiant_ef_hf"], "require LV dysfunction or HF: exclude latest echo EF > 40% in "
         "[index-365, index] (index-day echo included) and exclude EF unknown without an I50 code on/before index",
         "VALIANT (LVEF <= 40% and/or HF)", 4),
]
RULES["emperor-preserved-v2"] += [flag("saxa_alo_365", ["fx_saxalo"], "exclude saxagliptin/alogliptin order in "
                                       "[index-365, index] (removes them from the DPP-4i comparator)", DC + "; R2 must-fix", 3)]
RULES["declare"] += [
    flag("saxa_alo_365", ["fx_saxalo"], "exclude saxagliptin/alogliptin order in [index-365, index]", DC + "; R2 must-fix", 3),
    flag("other_sglt2_365", ["fx_washout"], "exclude other-SGLT2i order in [index-365, index]", DC + "; DECLARE", 3),
]
RULES["canvas"] += [flag("other_sglt2_365", ["fx_washout"], "exclude other-SGLT2i order in [index-365, index]", DC + "; CANVAS", 3)]
for _n in ("leader", "sustain6", "rewind"):
    RULES[_n] += [flag("other_glp1_365", ["fx_washout"], "exclude other-GLP-1RA order in [index-365, index]", DC + "; " + K.NAME[_n], 3)]
RULES["laaos3"] += [flag("af_before_admission", ["fx_laaos3_postop_af"], "require AF coded before the index admission: exclude "
                         "first-ever I48 dated within the index inpatient stay (or on the index day without a stay)",
                         DC + "; LAAOS III (pre-existing AF)", 4)]
RULES["life"] += [flag("definite_lvh", ["fx_life_hedged_primary"], "require a definite ECG-LVH statement: exclude patients "
                       "whose only LVH statements are minimal-voltage / normal-variant, possible / cannot-rule-out or negated",
                       DC + "; LIFE (ECG-LVH)", 4)]

# outcome re-definitions (flags.py outcome): trial -> text
OUTCOME_FIX = {
    "amplify": "recurrent VTE = first inpatient stay starting >= 7 d after the end of the index stay with a primary "
               "hospital-billing VTE code (I26, I80.1, I80.2, I82.4); death / data end censor",
    "lodestar": "composite + coronary revascularisation (PCI or CABG procedure codes) after the end of the index stay",
    "prove-it": "composite + coronary revascularisation (PCI or CABG) >= 30 d after index",
}


# ================================================================ fixes 1-2: numeric entry bounds and age (published criteria)
ULN_ALT = 40.0  # U/L; assumed upper limit of normal for "x ULN" rules (laboratory-specific ULN not in OMOP gold)


def _arr(M, c):
    return M[c].to_numpy(float)


def bp_rule(rid, include, src, text, when=None):
    """BP rule on the latest SBP and DBP (both 90 d). include(sbp, dbp, M) -> bool (inclusion met, given both measured);
    a patient with SBP or DBP unknown passes (v2) / is excluded (v2meas)."""
    def fn(M, F):
        s, d = _arr(M, "sbp"), _arr(M, "dbp")
        ok = np.isfinite(s) & np.isfinite(d)
        with np.errstate(invalid="ignore"):
            inc = np.asarray(include(s, d, M), bool)
        bad = ok & ~inc
        if when is not None:
            w = np.asarray(when(M), bool)
            return bad & w, ok | ~w
        return bad, ok
    return custom(rid, fn, text, src)


def np_rule(rid, thr_nt, thr_bnp, src, text):
    """natriuretic-peptide inclusion: NT-proBNP >= thr_nt(M) or BNP >= thr_bnp(M) (either qualifies); unknown passes."""
    def fn(M, F):
        nt, b = _arr(M, "ntprobnp"), _arr(M, "bnp")
        tn = np.asarray(thr_nt(M), float)
        tb = np.asarray(thr_bnp(M), float) if thr_bnp is not None else np.full(len(M), np.inf)
        with np.errstate(invalid="ignore"):
            q = (np.isfinite(nt) & (nt >= tn)) | (np.isfinite(b) & (b >= tb))
        meas = np.isfinite(nt) | (np.isfinite(b) if thr_bnp is not None else False)
        return meas & ~q, meas
    return custom(rid, fn, text, src)


def hba1c(lo=None, hi=None, src="", text="", lo_excl=False, hi_excl=False):
    def fn(M, F):
        x = _arr(M, "hba1c")
        ok = np.isfinite(x)
        bad = np.zeros(len(x), bool)
        with np.errstate(invalid="ignore"):
            if lo is not None:
                bad |= ok & ((x <= lo) if lo_excl else (x < lo))
            if hi is not None:
                bad |= ok & ((x >= hi) if hi_excl else (x > hi))
        return bad, ok
    return custom(f"hba1c_{lo}_{hi}", fn, text or f"HbA1c in [{lo}, {hi}]%", src)


def hba1c_cond(rid, bounds, src, text):
    """bounds(M) -> (lo array, hi array): per-patient HbA1c inclusion window (e.g. by background therapy)."""
    def fn(M, F):
        x = _arr(M, "hba1c")
        lo, hi = bounds(M)
        ok = np.isfinite(x)
        with np.errstate(invalid="ignore"):
            bad = ok & ((x < lo) | (x > hi))
        return bad, ok
    return custom(rid, fn, text, src)


def ef_rule(rid, lo=None, hi=None, src="", text=""):
    """latest echo EF in [index-365, index-1] (as build_trial_cohort): exclude if < lo or > hi (inclusion range)."""
    r = num(rid, "ef", lo=lo, hi=hi, src=src, text=text)
    return r


def alt_rule(mult, src, strict=True):
    lim = mult * ULN_ALT
    return num(f"alt_gt{mult}uln", "alt", hi=lim, src=src,
               text=f"exclude ALT > {mult} x ULN (ULN assumed {ULN_ALT:g} U/L, i.e. > {lim:g} U/L)")


AF = lambda M: M.af_code_on_before.to_numpy(bool)  # noqa: E731
TRT = lambda M: M.treated_htn_365.to_numpy(bool)  # noqa: E731
GL = lambda M: M.glucose_lowering_84.to_numpy(bool)  # noqa: E731
SU = lambda M: M.su_glinide_84.to_numpy(bool)  # noqa: E731


def _add(n, *rs):
    RULES[n] += list(rs)


# ---- age: the published hard bound for every trial (risk-factor age routes are not hard bounds and are not applied)
AGE = {"comet": (18, None), "paradigm-hf-seq": (18, None), "transform-hf": (18, None), "elite-ii": (60, None),
       "life": (55, 80), "plato": (18, None), "aristotle": (18, None), "rocket-af": (18, None), "rely": (18, None),
       "allhat": (55, None), "emperor-preserved-v2": (18, None), "east-afnet4": (18, None), "cabana-v2": (18, None),
       "ontarget": (55, None), "value": (50, None), "ascot": (40, 79), "empa-reg": (18, None), "carolina": (40, 85),
       "leader": (50, None), "sustain6": (50, None), "rewind": (50, None), "declare": (40, None), "canvas": (30, None),
       "tecos": (50, None), "carmelina": (18, None), "valiant": (18, None), "insight": (55, 80), "affirm": (18, None),
       "af-chf": (18, None), "precision": (18, None), "amplify": (18, None), "lodestar": (19, None), "prove-it": (18, None),
       "frail-af": (75, None), "laaos3": (18, None), "protect-af": (18, None), "raft-af": (18, None), "active-w": (18, None)}
for _n, (_lo, _hi) in AGE.items():
    RULES[_n].insert(0, age(_lo, _hi, src=f"{K.NAME[_n]} (published age bound)"))

# ---- heart failure / post-MI
_add("comet",
     bp_rule("bp_le170_105", lambda s, d, M: (s <= 170) & (d <= 105), "COMET", "exclude SBP > 170 or DBP > 105 mmHg"),
     num("sbp_ge85", "sbp", lo=85, src="COMET", text="exclude SBP < 85 mmHg"),
     num("hr_ge60", "heart_rate", lo=60, src="COMET", text="exclude resting heart rate < 60 bpm"))
_add("paradigm-hf-seq",
     ef_rule("lvef_le35", hi=35, src="PARADIGM-HF (amended LVEF <= 35%)", text="exclude latest echo EF > 35%"),
     np_rule("natriuretic_peptide", lambda M: np.where(M.hf_hosp_365, 400.0, 600.0), lambda M: np.where(M.hf_hosp_365, 100.0, 150.0),
             "PARADIGM-HF", "require NT-proBNP >= 600 or BNP >= 150 pg/mL (>= 400 / >= 100 if an HF hospitalisation in the prior "
             "12 months); exclude if measured and neither qualifies"),
     alt_rule(2, "PARADIGM-HF"))
_add("elite-ii",
     num("dbp_le95", "dbp", hi=95, src="ELITE II", text="exclude DBP > 95 mmHg"),
     num("creat_le2_5", "creatinine", hi=2.5, src="ELITE II", text="exclude creatinine > 2.5 mg/dL (220 umol/L)"))
_add("emperor-preserved-v2",
     np_rule("ntprobnp_300_900", lambda M: np.where(AF(M), 900.0, 300.0), None, "EMPEROR-Preserved",
             "require NT-proBNP > 300 pg/mL (> 900 with an AF code on/before index); exclude if measured and below"),
     num("bmi_lt45", "bmi", hi=44.999, src="EMPEROR-Preserved", text="exclude BMI >= 45 kg/m2 (365 d)"),
     num("sbp_lt180", "sbp", hi=179.999, src="EMPEROR-Preserved", text="exclude SBP >= 180 mmHg"),
     num("hr_le110_af", "heart_rate", hi=110, src="EMPEROR-Preserved", when=AF,
         text="exclude heart rate > 110 bpm in patients with an AF code"),
     num("hb_ge9", "hemoglobin", lo=9, src="EMPEROR-Preserved", text="exclude haemoglobin < 9 g/dL"),
     alt_rule(3, "EMPEROR-Preserved"))
_add("valiant", num("creat_lt2_5", "creatinine", hi=2.4999, src="VALIANT", text="exclude creatinine >= 2.5 mg/dL"))
_add("af-chf", num("hr_ge50", "heart_rate", lo=50, src="AF-CHF", text="exclude heart rate < 50 bpm (pacemaker not identifiable)"))
_add("raft-af", np_rule("ntprobnp_raft", lambda M: np.where(M.hf_hosp_274, 400.0, 600.0), None, "RAFT-AF",
                        "require NT-proBNP >= 400 pg/mL with an HF hospitalisation in the prior 9 months, else >= 600 (the "
                        "sinus-rhythm thresholds; rhythm at sampling not identifiable, so the lower thresholds are used)"))

# ---- hypertension (BP on prior treatment: treated = antihypertensive order in [index-365, index-1])
_add("life",
     bp_rule("bp_life", lambda s, d, M: ((s >= 160) | (d >= 95)) & (s <= 200) & (d <= 115), "LIFE",
             "require SBP 160-200 and/or DBP 95-115 mmHg (SBP >= 160 or DBP >= 95, and SBP <= 200 and DBP <= 115)"),
     ef_rule("lvef_gt40", lo=40.001, src="LIFE", text="exclude latest echo EF <= 40%"))
_add("insight",
     bp_rule("bp_insight", lambda s, d, M: ((s >= 150) & (d >= 95)) | (s >= 160), "INSIGHT",
             "require BP >= 150/95 mmHg or SBP >= 160 mmHg"),
     ef_rule("lvef_ge40", lo=40, src="INSIGHT", text="exclude latest echo EF < 40%"))
_add("ascot",
     bp_rule("bp_ascot", lambda s, d, M: np.where(TRT(M), (s >= 140) | (d >= 90), (s >= 160) | (d >= 100)), "ASCOT-BPLA",
             "require SBP >= 160 or DBP >= 100 mmHg if untreated, SBP >= 140 or DBP >= 90 if treated"))
_add("allhat",
     bp_rule("bp_allhat", lambda s, d, M: np.where(TRT(M), (s <= 160) & (d <= 100), ((s >= 140) | (d >= 90)) & (s <= 180) & (d <= 110)),
             "ALLHAT", "require SBP >= 140 or DBP >= 90 and <= 180/110 mmHg if untreated; <= 160/100 if treated (visit 1)"),
     ef_rule("lvef_ge35", lo=35, src="ALLHAT", text="exclude latest echo EF < 35%"),
     num("creat_lt2", "creatinine", hi=1.9999, src="ALLHAT", text="exclude creatinine >= 2.0 mg/dL"))
_add("value",
     bp_rule("bp_value", lambda s, d, M: np.where(TRT(M), (s <= 210) & (d < 115), (s >= 160) & (s <= 210) & (d < 115)), "VALUE",
             "require SBP 160-210 and DBP < 115 mmHg if untreated; SBP <= 210 and DBP < 115 if treated"),
     num("creat_le3", "creatinine", hi=3.0, src="VALUE", text="exclude creatinine > 265 umol/L (3.0 mg/dL)"))
_add("ontarget",
     bp_rule("bp_le160_100", lambda s, d, M: (s <= 160) & (d <= 100), "ONTARGET", "exclude BP > 160/100 mmHg"),
     num("creat_le3", "creatinine", hi=3.0, src="ONTARGET", text="exclude creatinine > 265 umol/L (3.0 mg/dL)"),
     alt_rule(4, "ONTARGET"))

# ---- anticoagulation / AF / devices
BP180 = lambda s, d, M: (s <= 180) & (d <= 100)  # noqa: E731
_add("aristotle",
     bp_rule("bp_le180_100", BP180, "ARISTOTLE", "exclude SBP > 180 or DBP > 100 mmHg"),
     num("creat_le2_5", "creatinine", hi=2.5, src="ARISTOTLE", text="exclude creatinine > 2.5 mg/dL"),
     num("egfr_ge25", "egfr", lo=25, src="ARISTOTLE", text="exclude eGFR < 25 (CrCl < 25 mL/min approximated by eGFR)"),
     num("plt_gt100", "platelets", lo=100.001, src="ARISTOTLE", text="exclude platelets <= 100 x 10^9/L"),
     num("hb_ge9", "hemoglobin", lo=9, src="ARISTOTLE", text="exclude haemoglobin < 9 g/dL"),
     alt_rule(2, "ARISTOTLE"))
_add("rocket-af",
     bp_rule("bp_lt180_100", lambda s, d, M: (s < 180) & (d < 100), "ROCKET AF", "exclude SBP >= 180 or DBP >= 100 mmHg"),
     num("plt_ge90", "platelets", lo=90, src="ROCKET AF", text="exclude platelets < 90 x 10^9/L"),
     num("hb_ge10", "hemoglobin", lo=10, src="ROCKET AF", text="exclude haemoglobin < 10 g/dL"),
     num("egfr_ge30", "egfr", lo=30, src="ROCKET AF", text="exclude eGFR < 30 (CrCl < 30 approximated)"),
     alt_rule(3, "ROCKET AF"))
_add("rely",
     bp_rule("bp_le180_100", BP180, "RE-LY", "exclude SBP > 180 or DBP > 100 mmHg"),
     num("egfr_ge30", "egfr", lo=30, src="RE-LY", text="exclude eGFR < 30 (CrCl < 30 approximated)"),
     num("hb_ge10", "hemoglobin", lo=10, src="RE-LY", text="exclude haemoglobin < 10 g/dL"),
     num("plt_ge100", "platelets", lo=100, src="RE-LY", text="exclude platelets < 100 x 10^9/L"),
     alt_rule(2, "RE-LY"))
_add("amplify",
     bp_rule("bp_le180_100", BP180, "AMPLIFY", "exclude SBP > 180 or DBP > 100 mmHg"),
     num("hb_ge9", "hemoglobin", lo=9, src="AMPLIFY", text="exclude haemoglobin < 9 g/dL"),
     num("plt_ge100", "platelets", lo=100, src="AMPLIFY", text="exclude platelets < 100 x 10^9/L"),
     num("creat_le2_5", "creatinine", hi=2.5, src="AMPLIFY", text="exclude creatinine > 2.5 mg/dL"),
     num("egfr_ge25", "egfr", lo=25, src="AMPLIFY", text="exclude eGFR < 25 (CrCl < 25 approximated)"),
     alt_rule(2, "AMPLIFY"))
_add("protect-af",
     ef_rule("lvef_ge30", lo=30, src="PROTECT AF", text="exclude latest echo EF < 30%"),
     num("plt_ge100", "platelets", lo=100, src="PROTECT AF", text="exclude platelets < 100 x 10^9/L"),
     num("hb_ge10", "hemoglobin", lo=10, src="PROTECT AF", text="exclude haemoglobin < 10 g/dL"))
_add("active-w", num("plt_ge50", "platelets", lo=50, src="ACTIVE W", text="exclude platelets < 50 x 10^9/L"))

# ---- diabetes CVOTs (HbA1c 90 d; BMI 365 d)
_add("empa-reg",
     hba1c_cond("hba1c_empareg", lambda M: (np.full(len(M), 7.0), np.where(GL(M), 10.0, 9.0)), "EMPA-REG OUTCOME",
                "require HbA1c 7.0-10.0% if on glucose-lowering therapy in the prior 12 weeks, 7.0-9.0% if drug-naive"),
     num("bmi_le45", "bmi", hi=45, src="EMPA-REG OUTCOME", text="exclude BMI > 45 kg/m2"),
     alt_rule(3, "EMPA-REG OUTCOME"))
_add("carolina",
     hba1c_cond("hba1c_carolina", lambda M: (np.full(len(M), 6.5), np.where(SU(M), 7.5, 8.5)), "CAROLINA",
                "require HbA1c 6.5-8.5% (6.5-7.5% if on a sulfonylurea or glinide in the prior 12 weeks)"),
     num("bmi_le45", "bmi", hi=45, src="CAROLINA", text="exclude BMI > 45 kg/m2"),
     alt_rule(3, "CAROLINA"))
_add("leader", hba1c(7.0, None, "LEADER", "require HbA1c >= 7.0%"))
_add("sustain6", hba1c(7.0, None, "SUSTAIN-6", "require HbA1c >= 7.0%"))
_add("rewind",
     hba1c(None, 9.5, "REWIND", "require HbA1c <= 9.5%"),
     num("bmi_ge23", "bmi", lo=23, src="REWIND", text="exclude BMI < 23 kg/m2"),
     num("alt_lt3uln", "alt", hi=3 * ULN_ALT - 1e-9, src="REWIND", text=f"exclude ALT >= 3 x ULN (ULN assumed {ULN_ALT:g} U/L)"))
_add("declare",
     hba1c(6.5, 12.0, "DECLARE-TIMI 58", "exclude HbA1c < 6.5% or >= 12.0%", hi_excl=True),
     bp_rule("bp_le180_100", BP180, "DECLARE-TIMI 58", "exclude SBP > 180 or DBP > 100 mmHg"),
     alt_rule(3, "DECLARE-TIMI 58"))
_add("canvas", hba1c(7.0, 10.5, "CANVAS / CANVAS-R", "require HbA1c 7.0-10.5%"), alt_rule(2, "CANVAS / CANVAS-R"))
_add("tecos", hba1c(6.5, 8.0, "TECOS", "require HbA1c 6.5-8.0%"))
_add("carmelina",
     hba1c(6.5, 10.0, "CARMELINA", "require HbA1c 6.5-10.0%"),
     num("bmi_le45", "bmi", hi=45, src="CARMELINA", text="exclude BMI > 45 kg/m2"),
     num("alt_lt3uln", "alt", hi=3 * ULN_ALT - 1e-9, src="CARMELINA", text=f"exclude ALT >= 3 x ULN (ULN assumed {ULN_ALT:g} U/L)"))

# ---- other
_add("precision",
     bp_rule("bp_le140_90", lambda s, d, M: (s <= 140) & (d <= 90), "PRECISION (design paper Table I, secondary source)",
             "exclude uncontrolled BP: SBP > 140 or DBP > 90 mmHg"),
     custom("creat_sex", lambda M, F: (np.isfinite(_arr(M, "creatinine")) & (_arr(M, "creatinine") > np.where(M.male == 1, 1.7, 1.5)),
                                       np.isfinite(_arr(M, "creatinine"))),
            "exclude creatinine > 1.7 (men) / > 1.5 (women) mg/dL", "PRECISION"),
     ef_rule("lvef_gt35", lo=35.001, src="PRECISION", text="exclude latest echo EF <= 35%"),
     alt_rule(2, "PRECISION"))
_add("lodestar", alt_rule(3, "LODESTAR"))
_add("prove-it",
     num("tc_le240", "total_chol", hi=240, src="PROVE IT-TIMI 22", text="require total cholesterol <= 240 mg/dL (not on statin: "
         "other-statin washout in the spec; window 90 d before index, not the trial's 24 h after ACS)"),
     num("creat_le2", "creatinine", hi=2.0, src="PROVE IT-TIMI 22", text="exclude creatinine > 2.0 mg/dL"))
