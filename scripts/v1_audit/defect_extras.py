"""Defect-impact extras for docs/v1_audit/DEFECT_IMPACT.md (called by `defect_impact.py extras`).

defect 2  shrinkage decomposition of the PS-CVD5 agreement gains (all 6 configurations, S32):
          mean |log HR| and SE, base vs arm; share of trials moved toward the null; a pure-shrinkage counterfactual
          (base log HRs scaled by s = mean|arm| / mean|base|); the benchmark-permutation null mean of the |Δ| reduction.
defect 3  CV-chosen PS-Flags penalties (ratio to C = 1) and the flagscv head-to-heads on S35.
defect 4  IPTW effective sample size per arm; IPTW P5 contrasts restricted to trials with ESS fraction >= 0.5 in both cells.
defect 6  physiologic-label and LV-systolic-function domain tests on S35; agreement by R2 blind tier; paper2 quality strata.
defect 7  global BH family (sweep balance + agreement + domain + label p values, S32) for the headline rows.
Only aggregates are written (trial-level rows are not).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import defect_impact as D

P2, SP, E, V = D.P2, D.SP, D.E, D.V
OUT, CORE = D.OUT, D.CORE
NONCODED = D.NONCODED


def shrinkage(F, sets):
    rows = []
    rng = np.random.default_rng(0)
    for sname in ("S32", "S35"):
        tr = sets[sname]
        IX = np.array([rng.permutation(len(tr)) for _ in range(20000)])
        for cfg in SP.CONFIGS:
            Fb = F[("P5", cfg, "base")].loc[tr]
            for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"):
                Fa = F[("P5", cfg, a)].loc[tr]
                ok = (np.isfinite(Fa.loghr) & np.isfinite(Fb.loghr)).to_numpy()
                la, lb, rb, rs = Fa.loghr.to_numpy()[ok], Fb.loghr.to_numpy()[ok], Fb.rb.to_numpy()[ok], Fb.rs.to_numpy()[ok]
                sa, sb = Fa.se.to_numpy()[ok], Fb.se.to_numpy()[ok]
                s = np.abs(la).mean() / np.abs(lb).mean()
                cf = s * lb
                obs_gain = np.mean(np.abs(lb - rb) - np.abs(la - rb))
                ix = IX[:, : ok.sum()] if ok.sum() == len(tr) else np.array([rng.permutation(ok.sum()) for _ in range(20000)])
                q = rb[ix]
                null_gain = np.mean(np.abs(lb - q) - np.abs(la - q), axis=1)
                ea = lambda l: int((np.abs(l - rb) <= 1.96 * rs).sum())
                sda = lambda l, se: int((np.abs(l - rb) / np.sqrt(se ** 2 + rs ** 2) < 1.96).sum())
                rows.append(dict(set=sname, config=cfg, arm=a, k=int(ok.sum()), mean_abs_loghr_base=np.abs(lb).mean(),
                                 mean_abs_loghr_arm=np.abs(la).mean(), shrink_factor=s,
                                 n_toward_null=int((np.abs(la) < np.abs(lb)).sum()), mean_se_base=sb.mean(), mean_se_arm=sa.mean(),
                                 absd_base=np.abs(lb - rb).mean(), absd_arm=np.abs(la - rb).mean(), absd_pure_shrink=np.abs(cf - rb).mean(),
                                 share_of_gain_from_pure_shrink=(np.abs(lb - rb).mean() - np.abs(cf - rb).mean()) / obs_gain if obs_gain else np.nan,
                                 obs_gain=obs_gain, perm_null_mean_gain=null_gain.mean(),
                                 perm_null_mean_over_obs=null_gain.mean() / obs_gain if obs_gain else np.nan,
                                 ea_base=ea(lb), ea_arm=ea(la), ea_pure_shrink=ea(cf),
                                 sda_base=sda(lb, sb), sda_arm=sda(la, sa), sda_pure_shrink_base_se=sda(cf, sb), sda_base_est_arm_se=sda(lb, sa)))
    return pd.DataFrame(rows)


def iptw(R, F, SM, sets):
    rows = []
    for sname in ("S32",):
        tr = sets[sname]
        ess = {}
        for (rg, cfg, a), g in R[R.config == "iptw"].groupby(["rung", "config", "arm"]):
            g = g.set_index("trial").loc[tr]
            ess[(rg, a)] = np.minimum(g.ess_t / g.n_t, g.ess_c / g.n_c)
            rows.append(dict(analysis="ESS fraction under IPTW (min over arms), median [IQR]", set=sname, cell=f"{rg} {a}",
                             median=float(ess[(rg, a)].median()), q25=float(ess[(rg, a)].quantile(.25)), q75=float(ess[(rg, a)].quantile(.75)),
                             n_trials_lt05=int((ess[(rg, a)] < 0.5).sum())))
        for ra, aa, rb_, ab in (("P5", "ECG", "P5", "base"), ("P5", "CLMBR", "P5", "base"), ("P5", "ECG+CLMBR", "P5", "base"),
                                ("P1", "CLMBR", "Flags", "base"), ("P1", "CLMBR", "hdPS200", "base")):
            keep = [t for t in tr if ess[(ra, aa)][t] >= 0.5 and ess[(rb_, ab)][t] >= 0.5]
            ka, kb = (ra, "iptw", aa), (rb_, "iptw", ab)
            side = "one" if ra == rb_ else "two"
            if len(keep) >= 5:
                b = P2.bal_light(F[ka], F[kb], P2.mask(SM[ka], NONCODED), P2.mask(SM[kb], NONCODED), keep, side, V.cluster_of(), full=False)
                rows.append(dict(analysis="IPTW contrast restricted to trials with ESS fraction >= 0.5 in both cells", set=sname,
                                 cell=f"{ra}+{aa} vs {rb_} {ab}", k=len(keep), relred=b["relred"], lo=b["relred_lo"], hi=b["relred_hi"], p=b["m58_p"]))
            else:
                rows.append(dict(analysis="IPTW contrast restricted to trials with ESS fraction >= 0.5 in both cells", set=sname,
                                 cell=f"{ra}+{aa} vs {rb_} {ab}", k=len(keep), relred=np.nan))
    return pd.DataFrame(rows)


def labels_s35(F, SM, sets):
    """paper2 label tests (P2.labels logic, main configuration) on S32 / S35 / S38 with paper2's FDR families:
    physiologic = 5 arms x 3 endpoints; domain = tested rows (5 arms x label domains with >= 2 labelled trials, LV
    structure excluded) per label source. S32 rows must reproduce core/labels_physiologic.csv and labels_domain.csv."""
    LB = P2.load_labels()
    rows, drows = [], []
    cfg = "main"
    kb = ("P5", cfg, "base")
    Sb = SM[kb]
    for sname in ("S32", "S35", "S38"):
        tr = sets[sname]
        for a in P2.LAB_ARMS:
            ka = ("P5", cfg, a)
            Sa = SM[ka]
            msk = Sa.isna() | Sb.isna()
            Sa2, Sb2 = Sa.mask(msk), Sb.mask(msk)
            phys = np.array([LB[t]["phys"] for t in tr])
            gain54 = (Sb2.loc[tr, NONCODED].mean(1) - Sa2.loc[tr, NONCODED].mean(1)).to_numpy()
            gainlt = (100 * (Sa2.loc[tr, NONCODED] < 0.1).sum(1) / Sa2.loc[tr, NONCODED].notna().sum(1)
                      - 100 * (Sb2.loc[tr, NONCODED] < 0.1).sum(1) / Sb2.loc[tr, NONCODED].notna().sum(1)).to_numpy()
            gabs = (F[kb].loc[tr, "absd"] - F[ka].loc[tr, "absd"]).to_numpy()
            for ep, g in (("m54 gain (base - arm mean |SMD|)", gain54), ("lt01_54 gain (pp)", gainlt), ("absd gain (closer > 0)", gabs)):
                d, p, ny, nn = P2.perm_diff(g, phys)
                rr = {}
                if ep.startswith("m54"):
                    for grp, m_ in (("yes", phys), ("no", ~phys)):
                        tt = [t for t, k in zip(tr, m_) if k]
                        e, lo, hi, _ = SP.relred_ci(Sb2.loc[tt, NONCODED].mean(1), Sa2.loc[tt, NONCODED].mean(1))
                        rr.update({f"relred_{grp}": e, f"relred_{grp}_lo": lo, f"relred_{grp}_hi": hi})
                rows.append(dict(set=sname, config=cfg, arm=a, endpoint=ep, n_yes=ny, n_no=nn, diff=d, perm_p=p, **rr))
            for src, fld in (("domains", "dom"), ("domains_union", "dom_u")):
                for D_, items in P2.DOMAIN_ITEMS.items():
                    lab = np.array([D_ in LB[t][fld] for t in tr])
                    g = (Sb2.loc[tr, items].mean(1) - Sa2.loc[tr, items].mean(1)).to_numpy()
                    tested = bool(lab.sum() >= 2 and D_ != "LV_structure")
                    d, p, ny, nn = P2.perm_diff(g, lab) if tested else (np.nan, np.nan, int(lab.sum()), int((~lab).sum()))
                    drows.append(dict(set=sname, config=cfg, arm=a, label_source=src, label_domain=D_, n_labelled=ny, n_not=nn,
                                      diff=d, perm_p=p, tested=tested))
    L, M = pd.DataFrame(rows), pd.DataFrame(drows)
    L["q_family"] = np.nan
    for _, g in L.groupby("set"):
        ix = g.index[g.perm_p.notna()]
        L.loc[ix, "q_family"] = E.bh_fdr(L.loc[ix, "perm_p"].to_numpy())
    M["q_family"] = np.nan
    for _, g in M.groupby(["set", "label_source"]):
        ix = g.index[g.tested & g.perm_p.notna()]
        M.loc[ix, "q_family"] = E.bh_fdr(M.loc[ix, "perm_p"].to_numpy())
    # gate against paper2 (S32, main)
    ref = pd.read_csv(CORE / "labels_physiologic.csv")
    ref = ref[(ref["set"] == "S32") & (ref.config == "main")].set_index(["arm", "endpoint"])
    x = L[L["set"] == "S32"].set_index(["arm", "endpoint"])
    dev_p = float(np.nanmax(np.abs(x.perm_p - ref.loc[x.index, "perm_p"])))
    dev_q = float(np.nanmax(np.abs(x.q_family - ref.loc[x.index, "q_family"])))
    refd = pd.read_csv(CORE / "labels_domain.csv")
    refd = refd[(refd["set"] == "S32") & (refd.config == "main")].set_index(["arm", "label_source", "label_domain"])
    y = M[M["set"] == "S32"].set_index(["arm", "label_source", "label_domain"])
    dev_dq = float(np.nanmax(np.abs(y.q_family - refd.loc[y.index, "q_family"])))
    gate = dict(labels_S32_maxdev_p=dev_p, labels_S32_maxdev_q=dev_q, domain_S32_maxdev_q=dev_dq)
    return L, M, gate


def quality(F, sets):
    tier2 = D.r2_tier()
    qt = SP.QT
    rows = []
    for lab, sname, grp in (("v1 tier (paper2)", "S32", lambda t: "Excellent/Good" if qt[D.KEY[t]] in ("Excellent", "Good") else "Moderate"),
                            ("R2 blind tier", "S35", lambda t: "A/B" if tier2[t] in ("A", "B") else "C"),
                            ("R2 blind tier", "S38", lambda t: {"A": "A/B", "B": "A/B", "C": "C", "D": "D"}[tier2[t]])):
        tr = sets[sname]
        for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG"):
            Fb, Fa = F[("P5", "main", "base")], F[("P5", "main", a)]
            for g_ in sorted({grp(t) for t in tr}):
                tt = [t for t in tr if grp(t) == g_]
                d = (Fb.loc[tt, "absd"] - Fa.loc[tt, "absd"]).to_numpy()
                rows.append(dict(grouping=lab, set=sname, arm=a, group=g_, k=len(tt), absd_base=float(Fb.loc[tt, "absd"].mean()),
                                 absd_arm=float(Fa.loc[tt, "absd"].mean()), closer=f"{int((d > 0).sum())}/{len(tt)}", p_one_sided=SP.p1s(d)))
    return pd.DataFrame(rows)


def flagscv_s35(workers):
    R = pd.concat([pd.read_parquet(CORE / "restricted_cells.parquet"), pd.read_parquet(CORE / "restricted_flagscv_cells.parquet")],
                  ignore_index=True)
    F, SM, RET = P2.load_F(R)
    sets = {"S32": D.S32, "S38": D.S38, "S35": D.s35()}
    P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS=sets)
    jobs = [("S35", c) for c in P2.cv_contrasts() if c[0] == "main"]
    jobs += [("S35", ("main", "P1+CLMBR vs Flags base", "across", "P1", "CLMBR", "Flags", "base", "two"))]
    res = [P2._row(j)[0] for j in jobs]
    S = pd.DataFrame(res)
    log = pd.read_csv(CORE / "flagscv_log.csv").set_index("trial")
    ratio = 1 / log.loc[D.S32, "C_FlagsCV_base"]
    extra = dict(C_ratio_min_S32=float(ratio.min()), C_ratio_max_S32=float(ratio.max()),
                 C_values_S32=sorted(set(np.round(log.loc[D.S32, "C_FlagsCV_base"], 6))))
    return S, extra


def global_fdr():
    S = pd.read_csv(CORE / "sensitivity.csv")
    Dm = pd.read_csv(CORE / "domains.csv")
    LP = pd.read_csv(CORE / "labels_physiologic.csv")
    LD = pd.read_csv(CORE / "labels_domain.csv")
    S = S[S["set"] == "S32"]
    parts = []
    for c in P2.BAL_FAM + P2.AGR_FAM:
        x = S[["config", "contrast", c]].dropna().rename(columns={c: "p"})
        x["src"] = c
        parts.append(x)
    d = Dm[Dm["set"] == "S32"][["config", "contrast", "domain", "p"]].dropna()
    d["src"] = "domain:" + d.domain
    parts.append(d.drop(columns="domain"))
    lp = LP[LP["set"] == "S32"][["config", "arm", "endpoint", "perm_p"]].dropna().rename(columns={"perm_p": "p"})
    lp["contrast"] = "label phys: " + lp.arm + " | " + lp.endpoint
    lp["src"] = "label_phys"
    parts.append(lp[["config", "contrast", "p", "src"]])
    ld = LD[(LD["set"] == "S32") & LD.tested][["config", "arm", "label_source", "label_domain", "perm_p"]].dropna().rename(columns={"perm_p": "p"})
    ld["contrast"] = "label dom: " + ld.label_source + " " + ld.label_domain + " | " + ld.arm
    ld["src"] = "label_domain"
    parts.append(ld[["config", "contrast", "p", "src"]])
    G = pd.concat(parts, ignore_index=True)
    G["q_global"] = E.bh_fdr(G.p.to_numpy())
    return G


def by_fdr(p):
    """Benjamini-Yekutieli q (valid under arbitrary dependence): BH q x sum_{i<=m} 1/i, capped at 1."""
    p = np.asarray(p, float)
    ok = np.isfinite(p)
    q = np.full(len(p), np.nan)
    m = int(ok.sum())
    q[ok] = np.minimum(1.0, np.asarray(E.bh_fdr(p[ok])) * np.sum(1.0 / np.arange(1, m + 1)))
    return q


def by_families():
    """paper2 families (S32): balance {m54, lt01_54, m58, lt01_58} and agreement {absd, cons, bshuf} over all 337 rows; BY q."""
    S = pd.read_csv(CORE / "sensitivity.csv")
    S = S[S["set"] == "S32"].reset_index(drop=True)
    out = S[["config", "contrast"] + P2.BAL_FAM + P2.AGR_FAM + [f"q_{c}_fam" for c in P2.BAL_FAM + P2.AGR_FAM]].copy()
    for fam in (P2.BAL_FAM, P2.AGR_FAM):
        long = S[fam].stack(dropna=True)
        q = pd.Series(by_fdr(long.to_numpy()), index=long.index).unstack()
        for c in fam:
            out[f"qBY_{c}"] = q[c]
    return out


def main(workers):
    import os
    os.umask(0o077)
    R = pd.read_parquet(CORE / "restricted_cells.parquet")
    F, SM, RET = P2.load_F(R)
    sets = {"S32": D.S32, "S38": D.S38, "S35": D.s35()}
    shrinkage(F, sets).to_csv(OUT / "d2_shrinkage.csv", index=False)
    iptw(R, F, SM, sets).to_csv(OUT / "d4_iptw.csv", index=False)
    L, M, g = labels_s35(F, SM, sets)
    L.to_csv(OUT / "d6_labels.csv", index=False)
    M.to_csv(OUT / "d6_labels_domain.csv", index=False)
    (OUT / "d6_labels_gate.json").write_text(json.dumps(g, indent=1))
    print("labels gate", g, flush=True)
    quality(F, sets).to_csv(OUT / "d6_quality_strata.csv", index=False)
    S, extra = flagscv_s35(workers)
    S.to_csv(OUT / "d3_flagscv_s35.csv", index=False)
    (OUT / "d3_flags_penalty.json").write_text(json.dumps(extra, indent=1, default=float))
    G = global_fdr()
    G.to_csv(OUT / "d7_global_fdr.csv", index=False)
    by_families().to_csv(OUT / "d7_by_families.csv", index=False)
    print("extras written", flush=True)


def substitution_gap():
    """defect 8 (descriptive): PS-CVD5 (+ representation) vs PS-Clinical, original and leakage-clean masks, S32 / S35."""
    rows = []
    for v in ("orig", "clean"):
        D._setup(v)
        for sname in ("S32", "S35"):
            for aa in ("base", "ECG", "CLMBR", "ECG+CLMBR"):
                r, _ = P2._row((sname, ("main", f"P5+{aa} vs clinical base", "across", "P5", aa, "clinical", "base", "two")))
                rows.append(dict(variant=v, set=sname, arm=aa, m54_clinical=r["m54_b"], m54_p5arm=r["m54_a"], relred54=r["relred54"],
                                 lo=r["relred54_lo"], hi=r["relred54_hi"], better=r["m54_better"], p=r["m54_p"]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import os
    os.umask(0o077)
    substitution_gap().to_csv(OUT / "d8_substitution_gap.csv", index=False)
