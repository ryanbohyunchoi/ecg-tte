"""Round-3: S9 recomputation, set integrity, love-count test comparison, covars2b leakage, S8 expanded panel on covars2b,
S6 v2b sparse x2np recompute."""
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, "/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit3")
from a3_common import *  # noqa

REPO = Path("/home/rbc58/github/ecg-tte")
S9D = A + "claude-v16-s9-covsets/"
C2B = A + "claude-v16-covars2b/"
C2 = A + "claude-v16-covars2/"
pd.set_option("display.width", 250)

V = pd.concat([pd.read_parquet(S9D + f) for f in ("var_A.parquet", "var_full_B.parquet")], ignore_index=True)
V = V.drop_duplicates(["cell", "trial", "half", "arm_role", "var"])
print("S9 var rows", len(V), V.half.value_counts().to_dict())
dic = pd.read_csv(C2B + "dictionary.csv")
st = pd.read_csv(C2B + "trial_variable_status.csv")
EXTRA_PROX = {"prior_mi_ever", "acute_mi_365", "acs_365", "cci_mi", "lab_bnp", "lab_bnp_missing", "rx_arni_365", "rx_mra_365",
              "rx_loop_diuretic_365", "rx_digoxin_365", "rx_other_hf_drug_365"}
PROX = {f"x:{v}" for v in dic.variable[dic.block == "ecg_proximal"]} | {f"x:{v}" for v in EXTRA_PROX}

# ---- 1. leakage: any excluded (per trial) covars2b variable in S9 var parquet?
bad = st[~st.status.astype(str).str.startswith("kept") | st.status.astype(str).str.contains("leak") |
         st.exposure_leak.astype(str).str.lower().isin(["yes", "true", "1"])]
badset = set(zip(bad.trial, "x:" + bad.variable))
nonpre = {"x:" + v for v in dic.variable[dic.timing != "pre_index"]}
xv = V[V["var"].str.startswith("x:")][["trial", "var"]].drop_duplicates()
hit = xv[[(t, v) in badset for t, v in zip(xv.trial, xv["var"])]]
print("S9: excluded (trial,var) present:", len(hit), hit["var"].value_counts().head(10).to_dict())
print("S9: non-pre-index vars present:", sorted(set(xv["var"]) & nonpre))
print("S9: hfrs_ge5 present:", "x:hfrs_ge5" in set(xv["var"]))

# ---- 2. S8 expanded panel (covars2) vs covars2b exclusions
X8 = pd.read_parquet(A + "claude-v16-s8-headline/xvar_v2.parquet")
x8 = X8[["trial", "var"]].drop_duplicates()
bad8 = x8[[(t, "x:" + v) in badset for t, v in zip(x8.trial, x8["var"])]]
print("S8 xo: (trial,var) pairs excluded in covars2b but present in S8:", len(bad8), bad8["var"].value_counts().to_dict())
print("S8 xo non-pre-index present:", sorted({"x:" + v for v in x8["var"]} & nonpre))
UTIL = ["days_since_last_visit", "ehr_history_days", "n_outpatient_days_365", "n_ed_days_365", "no_prior_visit", "n_office_visits_365",
        "n_telemedicine_365", "n_infusion_visits_365", "n_anticoag_clinic_365"]
print("S8 xo utilisation variables built with the v2 (index-stay) visit rule:", sorted(set(x8["var"]) & set(UTIL)))

# ---- 3. utilisation spot-check covars2 vs covars2b (aggregate %, 3 trials)
for n in ("transform-hf", "paradigm-hf-seq", "plato"):
    a, b = pd.read_parquet(C2 + f"{n}.parquet"), pd.read_parquet(C2B + f"{n}.parquet")
    k = "patient_key" if "patient_key" in a else a.index.name
    a, b = a.set_index("patient_key"), b.set_index("patient_key")
    b = b.reindex(a.index)
    inp = b["index_setting_inpatient"] == 1
    out = {}
    for v in ("recent_hosp_30d", "n_inpatient_stays_365", "days_since_last_visit"):
        if v in a and v in b:
            if v == "recent_hosp_30d":
                out[v] = (round(100 * a.loc[inp, v].mean(), 1), round(100 * b.loc[inp, v].mean(), 1), round(100 * b.loc[~inp, v].mean(), 1))
            else:
                chg = (a[v].fillna(-9) != b[v].fillna(-9)).mean()
                out[v] = f"changed {100*chg:.1f}% of rows; index-inpatient median v2 {a.loc[inp, v].median()} v2b {b.loc[inp, v].median()}"
    print(n, f"index-inpatient share {100*inp.mean():.0f}%", out)

# ---- 4. S9 sets
SET1 = ["p58:smd_obs_lvef", "p58:pp_LVFUNC__ef", "p58:pp_LVFUNC__lv_sys_grade", "p58:pp_LVFUNC__gls", "p58:pp_LVFUNC__lvsvi",
        "p58:pp_LVSTRUCT__lvidd", "p58:pp_LVSTRUCT__lvedvi", "p58:pp_LVSTRUCT__lvesvi", "p58:pp_LVSTRUCT__ivsd", "p58:pp_LVSTRUCT__lvpwd",
        "p58:pp_LVSTRUCT__wall_thickness_grade", "p58:pp_DIAST__lavi", "p58:pp_DIAST__la_size_grade", "p58:pp_DIAST__e_eprime",
        "p58:pp_DIAST__diastolic_grade", "p58:pp_RVPULM__rvsp", "p58:pp_RVPULM__tapse", "p58:pp_RVPULM__rv_s", "p58:pp_RVPULM__rv_sys_grade",
        "x:pulmonary_hypertension", "p58:pp_BNP__ntprobnp", "p58:pp_LAB__egfr", "p58:smd_obs_creatinine", "p58:pp_LAB__bun",
        "p58:smd_obs_hemoglobin", "x:n_hf_hosp_365", "x:cardiomyopathy_any", "x:rx_loop_diuretic_365"]
allv = set(V["var"])
print("SET1 vars never observed:", [v for v in SET1 if v not in allv])
sys.path.insert(0, str(REPO / "scripts/v16"))
import s9_covsets as S9  # noqa: E402  (only for the Set-2 mapping function, checked against the frozen COVARIATES2.md)
set2_now = S9.set2()
# Set 2 at the mapping commit: COVARIATES2.md as of 5c0a94d
tmp = Path(OUT + "docs_5c0a94d")
tmp.mkdir(exist_ok=True)
for f in ("COVARIATES2.md", "lit_covariates.json"):
    (tmp / f).write_text(subprocess.run(["git", "-C", str(REPO), "show", f"5c0a94d:docs/v16/{f}"], capture_output=True, text=True).stdout)
S9.DOCS = tmp
set2_then = S9.set2()
print("Set 2 size now", len(set2_now), "at 5c0a94d", len(set2_then), "sym diff", sorted(set(set2_now) ^ set(set2_then))[:20])
lit = json.loads((REPO / "docs/v16/lit_covariates.json").read_text())
cc = [x for x in lit if x["priority"] in ("core", "common")]
LM = S9.lit_map()
print("lit core+common items", len(cc), "mapped items", len(LM), "items with >=1 variable", sum(1 for x in LM if x[3]),
      "items with none", [(x[0], x[1][:30], x[4]) for x in LM if not x[3]][:40])
J = json.loads((REPO / "docs/v16/selection_S9.json").read_text())


def cube(cell, half, role, trs, vs):
    if role == "unmatched":
        g = V[(V.cell == "unmatched") & (V.half == half)]
        b = V[(V.cell == cell) & (V.half == half) & (V.arm_role == "base")][["trial", "var"]]
        g = g.merge(b, on=["trial", "var"])
    else:
        g = V[(V.cell == cell) & (V.half == half) & (V.arm_role == role)]
    g = g[g.trial.isin(trs) & g["var"].isin(vs)]
    return g.pivot(index="trial", columns="var", values="smd").reindex(index=trs, columns=vs)


# own Set-3 re-selection from half A only
def reselect(cell, sub):
    trs = PHYS if sub == "phys" else sorted(V.trial.unique())
    pool = sorted(v for v in allv if v.startswith("p58:") or (v.startswith("x:") and v not in PROX))
    Mb, Me = cube(cell, "A", "base", trs, pool).to_numpy(), cube(cell, "A", "ECG", trs, pool).to_numpy()
    both = np.isfinite(Mb) & np.isfinite(Me)
    nav = both.sum(0)
    with np.errstate(invalid="ignore"):
        gain = np.where(both, Mb - Me, 0).sum(0) / nav
    g = pd.DataFrame({"var": pool, "gain": gain, "n": nav})
    g = g[g.n >= np.ceil(len(trs) / 2)].sort_values(["gain", "var"], ascending=[False, True])
    return g.head(25)["var"].tolist()


for sc in J["scenarios"]:
    cell, sub = sc.split("@")
    r = reselect(cell, sub)
    if r != J["scenarios"][sc]["selected"]:
        print("SET3 reselection MISMATCH", sc, len(set(r) & set(J["scenarios"][sc]["selected"])))
print("SET3 re-selection from half A done")

TR = sorted(V.trial.unique())
rows = []
SS = pd.read_csv(S9D + "set_summary.csv")
for cell, sub in [("demo|cal0.1", "all"), ("demo|default", "all"), ("min7|default", "all"), ("common10|default", "all"), ("sparse|default", "all"),
                  ("hdPS200|default", "all"), ("demo|cal0.1", "phys"), ("min7|default", "phys"), ("common10|default", "phys")]:
    trs = PHYS if sub == "phys" else TR
    for sname in ("SET1", "SET2", "SET3", "FULL", "XNP"):
        if sname == "SET1":
            vs = [v for v in SET1 if v in allv]
        elif sname == "SET2":
            vs = [v for v in set2_then if v in allv]
        elif sname == "SET3":
            vs = J["scenarios"][f"{cell}@{sub}"]["selected"]
        elif sname == "FULL":
            vs = sorted(v for v in allv if v.startswith("p58:") or (v.startswith("x:") and v not in PROX))
        else:  # S8-style expanded non-proximal panel on covars2b (x: only)
            vs = sorted(v for v in allv if v.startswith("x:") and v not in PROX)
        for h in ("full", "A", "B"):
            M = {r_: cube(cell, h, r_, trs, vs) for r_ in ("base", "ECG", "shufECG", "noise")}
            pc = {}
            for r_, m in M.items():
                x = m.to_numpy()
                ok = np.isfinite(x)
                pc[r_] = pd.Series(100 * np.where(ok, x < 0.1, False).sum(1) / ok.sum(1), index=m.index)
            d = (pc["ECG"] - pc["base"]).dropna()
            ob, lp = love_swap(M["ECG"].to_numpy(), M["base"].to_numpy(), ndraw=20000 if (cell == "demo|cal0.1" and sub == "all" and h != "A") else 2000) if not (sname == "XNP" or h == "A") else (np.nan, np.nan)
            rr = dict(cell=cell, subset=sub, set=sname, half=h, n_set=len(vs), base=pc["base"].mean(), ecg=pc["ECG"].mean(), d=d.mean(),
                      k=int((d > 0).sum()), p=flip(d.values), clp=cluster_p(d), p_shuf=flip((pc["ECG"] - pc["shufECG"]).dropna().values),
                      p_noise=flip((pc["ECG"] - pc["noise"]).dropna().values), love_base=int(love_count(M["base"].to_numpy())),
                      love_ecg=int(love_count(M["ECG"].to_numpy())), love_p_swap=lp)
            # trial-level sign-flip alternative for a 'count below 0.1' claim: per-trial count difference
            xb, xe = M["base"].to_numpy(), M["ECG"].to_numpy()
            cnt = pd.Series(np.nansum(xe < 0.1, 1) - np.nansum(xb < 0.1, 1), index=M["base"].index)
            rr["cnt_d"], rr["cnt_p_flip"] = cnt.mean(), flip(cnt.values)
            if sname != "XNP":
                s = SS[(SS.cell == cell) & (SS.subset == sub) & (SS.set == sname) & (SS.half == h)]
                if len(s):
                    s = s.iloc[0]
                    rr.update(s9_d=s.d_pct_lt10, s9_p=s.p_pct_lt10, s9_love=f"{s.love_base}->{s.love_ECG}", s9_love_p=s.p_love)
            rows.append(rr)
G = pd.DataFrame(rows)
G.to_csv(OUT + "s9_recompute.csv", index=False)
print(G[G.set != "XNP"].assign(dd=lambda x: (x.d - x.s9_d).abs())[["cell", "subset", "set", "half", "n_set", "base", "ecg", "d", "k", "p", "clp", "p_shuf", "p_noise",
                                                                      "love_base", "love_ecg", "love_p_swap", "s9_love", "s9_love_p", "cnt_p_flip", "dd"]].round(4).to_string())
print("max |d - S9 d|", (G.d - G.s9_d).abs().max(), "max |p - S9 p|", (G.p - G.s9_p).abs().max())
X = G[G.set == "XNP"]
print(X[["cell", "subset", "half", "n_set", "base", "ecg", "d", "k", "p", "clp"]].round(4).to_string())
# love test comparison over S9 family rows (full cohort)
fam = SS[(SS.half == "full") & SS.family]
print("S9 family (full): love p<0.05:", int((fam.p_love < 0.05).sum()), "pct p<0.05:", int((fam.p_pct_lt10 < 0.05).sum()),
      "discordant (pct sig, love not):", int(((fam.p_pct_lt10 < 0.05) & (fam.p_love >= 0.05)).sum()),
      "(love sig, pct not):", int(((fam.p_love < 0.05) & (fam.p_pct_lt10 >= 0.05)).sum()),
      "spearman(log p)", round(np.corrcoef(np.log(fam.p_love.rank()), np.log(fam.p_pct_lt10.rank()))[0, 1], 2))

# ---- 5. S6 v2b sparse x2np xsmd_other recompute
S6 = pd.read_csv(A + "claude-v16-s6-balance-v2b/results_x2np.csv", low_memory=False)
for cell in S6.cell.unique():
    if cell == "unmatched":
        continue
    for h in ("full", "A", "B"):
        g = S6[(S6.cell == cell) & (S6.half == h)]
        e, b = g[g.arm_role == "ECG"].set_index("trial").xsmd_other, g[g.arm_role == "base"].set_index("trial").xsmd_other
        d = (e - b).dropna()
        if h == "full" or cell == "sparse":
            print(f"S6v2b x2np {cell} {h}: {b.mean():.4f} -> {e.mean():.4f} d {d.mean():+.4f} k {(d<0).sum()}/{len(d)} p {flip(d.values):.4f} clp {cluster_p(d):.4f}")
