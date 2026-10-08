#!/usr/bin/env python
"""v1 audit (claims recheck): independent recomputation of retention / ESS, PS-Flags fairness (CV-tuned, fixed C,
retention-restricted), CLMBR-T retention sensitivity, and the trial-label analyses (physiologic and domain labels,
Spearman data-driven check) from the cell-level outputs. Uses the statistics of core_recompute.py (this audit's own
implementation), not scripts/v21/paper2_grid.py.

Output (aggregates only) in /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/:
  retention_recomputed.csv, flagscv_recomputed.csv, labels_phys_recomputed.csv, labels_dom_recomputed.csv,
  labels_spearman_recomputed.csv, compare_secondary_vs_v21.txt
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_recompute as K  # noqa: E402  (this audit's own implementation)

OUT = K.OUT
SRC = K.SRC
LABELS = K.ROOT / "docs/v21/TRIAL_LABELS.json"


def retention(R, B, S32, S38, CL):
    rows = []
    small = lambda k, tr: B[k]["ret"].loc[tr].mask((B[k]["npairs"].loc[tr] >= 1) & (B[k]["npairs"].loc[tr] < 11))
    for rg, a in (("P5", "base"), ("P5", "ECG"), ("P5", "CLMBR"), ("P5", "ECG+CLMBR"), ("P1", "CLMBR"), ("Flags", "base"),
                  ("hdPS200", "base"), ("clinical", "base")):
        for sname, tr in (("S32", S32), ("S38", S38)):
            x = small((rg, "main", a), tr)
            rows.append(dict(what="retention main", arm=f"{rg} {a}", set=sname, k=int(x.notna().sum()), mean=x.mean(), median=x.median()))
    for rg, a in (("P5", "base"), ("P5", "ECG"), ("P5", "CLMBR"), ("P5", "ECG+CLMBR"), ("P1", "CLMBR"), ("P1", "base"), ("Flags", "base"),
                  ("hdPS200", "base"), ("clinical", "base")):
        for cfg in ("iptw", "overlap"):
            b = B[(rg, cfg, a)]
            f = np.minimum(b["ess_t"].loc[S32] / b["n_t"].loc[S32], b["ess_c"].loc[S32] / b["n_c"].loc[S32])
            rows.append(dict(what=f"ESS fraction {cfg}", arm=f"{rg} {a}", set="S32", k=len(S32), median=f.median(), mean=f.mean()))
    # CLMBR-T gain vs retention loss
    kb = ("P5", "main", "base")
    rb = small(kb, S32)
    for a in ("ECG", "CLMBR", "ECG+CLMBR"):
        ka = ("P5", "main", a)
        Sa, Sb = B[ka]["S"].loc[S32, K.NONC], B[kb]["S"].loc[S32, K.NONC]
        m = Sa.isna() | Sb.isna()
        gain = Sb.mask(m).mean(1) - Sa.mask(m).mean(1)
        drop = rb - small(ka, S32)
        rho, p = spearmanr(gain, drop, nan_policy="omit")
        rows.append(dict(what="spearman gain vs retention drop", arm=a, set="S32", k=int((gain.notna() & drop.notna()).sum()), rho=rho, p=p))
    rcl = small(("P5", "main", "CLMBR"), S32)
    lo = [t for t in S32 if rb[t] - rcl[t] <= 0.05]
    hi = [t for t in S32 if t not in lo]
    for nm, tr in (("drop<=5pp", lo), ("drop>5pp", hi)):
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            o, _ = K.contrast(B, CL, ("P5", "main", a), kb, tr, "one", full=False)
            rows.append(dict(what=f"subset {nm}", arm=a, set="S32", k=len(tr), relred=o["relred54"], lo=o["relred54_lo"],
                             hi=o["relred54_hi"], p=o["m54_p"], better=o["m54_better"]))
    return pd.DataFrame(rows)


def flagscv(R, order, S32, S38, CL):
    R2 = pd.read_parquet(SRC / "restricted_flagscv_cells.parquet")
    RR = pd.concat([R, R2], ignore_index=True)
    B = K.blocks(RR, order)
    rf = B[("Flags", "main", "base")]["ret"]
    sets = {"S32": S32, "S38": S38}
    for th in (0.5, 0.7, 0.9):
        sets[f"S32_flagsret>={th}"] = [t for t in S32 if rf[t] >= th]
    L = []
    for cfg in ("main", "m13", "overlap"):
        L += [(cfg, "P1+CLMBR vs FlagsCV base", ("P1", cfg, "CLMBR"), ("FlagsCV", cfg, "base"), "two"),
              (cfg, "P1CV+CLMBR vs FlagsCV base", ("P1CV", cfg, "CLMBR"), ("FlagsCV", cfg, "base"), "two"),
              (cfg, "FlagsCV: CLMBR vs base", ("FlagsCV", cfg, "CLMBR"), ("FlagsCV", cfg, "base"), "one"),
              (cfg, "FlagsCV: ECG vs base", ("FlagsCV", cfg, "ECG"), ("FlagsCV", cfg, "base"), "one")]
    L += [("main", f"P1+CLMBR vs FlagsC{c} base", ("P1", "main", "CLMBR"), (f"FlagsC{c}", "main", "base"), "two") for c in ("0.1", "0.01")]
    rows = []
    for s in ("S32", "S38"):
        for cfg, lab, ka, kb, side in L:
            o, _ = K.contrast(B, CL, ka, kb, sets[s], side)
            rows.append(dict(set=s, k=len(sets[s]), config=cfg, contrast=lab, **o))
    for s in [x for x in sets if x.startswith("S32_flagsret")]:
        o, _ = K.contrast(B, CL, ("P1", "main", "CLMBR"), ("Flags", "main", "base"), sets[s], "two")
        rows.append(dict(set=s, k=len(sets[s]), config="main", contrast="P1+CLMBR vs Flags base", **o))
    return pd.DataFrame(rows)


def perm_label(g, lab, n=10000, seed=0):
    g, lab = np.asarray(g, float), np.asarray(lab, bool)
    ok = np.isfinite(g)
    g, lab = g[ok], lab[ok]
    obs = g[lab].mean() - g[~lab].mean()
    rng = np.random.default_rng(seed)
    null = np.empty(n)
    for j in range(n):
        p = rng.permutation(lab)
        null[j] = g[p].mean() - g[~p].mean()
    return obs, float((np.abs(null) >= abs(obs) - 1e-12).mean())


def labels(B, S32, S38):
    J = json.loads(LABELS.read_text())
    name = {}
    src = (K.ROOT / "scripts/v21/paper2_grid.py").read_text()  # the trial-name -> internal-name map is data, parsed not imported
    i = src.index("LABEL_NAME = {")
    j = src.index("}\n", i)
    import ast
    name = ast.literal_eval(src[i + len("LABEL_NAME = "):j + 1])
    LB = {name[x["trial"]]: dict(phys=x["physiologic"] == "yes", dom=set(x["domains"]), dom_u=set(x.get("domains_union", x["domains"])))
          for x in J["labels"]}
    DOMI = {"LV_systolic_function": [c for c in K.VN if K.GRP[c] == "Echo: LV function"] + ["smd_obs_lvef"],
            "diastolic_LA": [c for c in K.VN if K.GRP[c] == "Echo: diastolic / LA"],
            "RV_pulmonary_congestion": [c for c in K.VN if K.GRP[c] == "Echo: RV / pulmonary"] + ["pp_BNP__ntprobnp"],
            "rhythm_conduction": ["smd_obs_heart_rate"],
            "LV_structure": [c for c in K.VN if K.GRP[c] == "Echo: LV structure"]}
    ph, dm, sp = [], [], []
    for cfg in K.CONFIGS:
        kb = ("P5", cfg, "base")
        for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"):
            ka = ("P5", cfg, a)
            for sname, tr in (("S32", S32), ("S38", S38)):
                Sa, Sb = B[ka]["S"].loc[tr], B[kb]["S"].loc[tr]
                m = Sa.isna() | Sb.isna()
                Sa2, Sb2 = Sa.mask(m), Sb.mask(m)
                phys = np.array([LB[t]["phys"] for t in tr])
                g54 = (Sb2[K.NONC].mean(1) - Sa2[K.NONC].mean(1)).to_numpy()
                lta = 100 * (Sa2[K.NONC] < .1).sum(1) / Sa2[K.NONC].notna().sum(1)
                ltb = 100 * (Sb2[K.NONC] < .1).sum(1) / Sb2[K.NONC].notna().sum(1)
                xa = np.abs(B[ka]["lg"].loc[tr] - B[ka]["rb"].loc[tr]).to_numpy()
                xb = np.abs(B[kb]["lg"].loc[tr] - B[kb]["rb"].loc[tr]).to_numpy()
                for ep, g in (("m54", g54), ("lt01_54", (lta - ltb).to_numpy()), ("absd", xb - xa)):
                    d, p = perm_label(g, phys)
                    row = dict(set=sname, config=cfg, arm=a, endpoint=ep, diff=d, p=p, n_yes=int(phys.sum()))
                    if ep == "m54":
                        for grp, mm in (("yes", phys), ("no", ~phys)):
                            tt = [t for t, k in zip(tr, mm) if k]
                            e, lo_, hi_, _ = K.boot_relred(Sb2.loc[tt, K.NONC].mean(1), Sa2.loc[tt, K.NONC].mean(1))
                            row.update({f"rr_{grp}": e, f"rr_{grp}_lo": lo_, f"rr_{grp}_hi": hi_})
                    if ep == "absd":
                        row.update(mean_yes=np.nanmean(g[phys]), mean_no=np.nanmean(g[~phys]))
                    ph.append(row)
                for srcf in ("dom", "dom_u"):
                    for D_, items in DOMI.items():
                        lab = np.array([D_ in LB[t][srcf] for t in tr])
                        g = (Sb2.loc[tr, items].mean(1) - Sa2.loc[tr, items].mean(1)).to_numpy()
                        tested = lab.sum() >= 2 and D_ != "LV_structure"
                        d, p = perm_label(g, lab) if tested else (np.nan, np.nan)
                        dm.append(dict(set=sname, config=cfg, arm=a, src=srcf, domain=D_, n_lab=int(lab.sum()), tested=tested,
                                       mean_lab=np.nanmean(g[lab]) if lab.any() else np.nan, mean_not=np.nanmean(g[~lab]), diff=d, p=p))
                resid = Sb[K.ECHO].mean(1).to_numpy()
                for ep, g in (("m54", g54), ("echo", (Sb2[K.ECHO].mean(1) - Sa2[K.ECHO].mean(1)).to_numpy())):
                    ok = np.isfinite(g) & np.isfinite(resid)
                    rho, p = spearmanr(g[ok], resid[ok])
                    sp.append(dict(set=sname, config=cfg, arm=a, endpoint=ep, rho=rho, p=p, k=int(ok.sum())))
    PH, DM, SP = pd.DataFrame(ph), pd.DataFrame(dm), pd.DataFrame(sp)
    PH["q"] = np.nan
    for _, g in PH.groupby(["set", "config"]):
        PH.loc[g.index, "q"] = K.bh(g.p.to_numpy())
    DM["q"] = np.nan
    for _, g in DM.groupby(["set", "config", "src"]):
        ix = g.index[g.tested]
        DM.loc[ix, "q"] = K.bh(DM.loc[ix, "p"].to_numpy())
    return PH, DM, SP


def main():
    os.umask(0o077)
    R, order, key, tiers, S32, S38, CL = K.load()
    B = K.blocks(R, order)
    RT = retention(R, B, S32, S38, CL)
    RT.to_csv(OUT / "retention_recomputed.csv", index=False)
    FC = flagscv(R, order, S32, S38, CL)
    FC.to_csv(OUT / "flagscv_recomputed.csv", index=False)
    PH, DM, SP = labels(B, S32, S38)
    PH.to_csv(OUT / "labels_phys_recomputed.csv", index=False)
    DM.to_csv(OUT / "labels_dom_recomputed.csv", index=False)
    SP.to_csv(OUT / "labels_spearman_recomputed.csv", index=False)
    # comparison with the v21 outputs
    L = []
    V = pd.read_csv(SRC / "flagscv.csv")
    V["k"] = V["set_k"]
    m = FC.merge(V, on=["set", "config", "contrast"], suffixes=("", "_v"))
    for c in ("relred54", "relred54_lo", "relred54_hi", "m54_p", "absd_p", "bshuf_p", "absd_a_pair", "absd_b_pair"):
        L.append(f"flagscv {c}: rows {len(m)} maxdev {np.nanmax(np.abs(m[c] - m[c + '_v'])):.2e}")
    Vp = pd.read_csv(SRC / "labels_physiologic.csv")
    Vp["endpoint"] = Vp.endpoint.str.split(" ").str[0]
    m = PH.merge(Vp, on=["set", "config", "arm", "endpoint"], suffixes=("", "_v"))
    for a, b in (("diff", "diff_yes_minus_no"), ("p", "perm_p"), ("q", "q_family"), ("rr_yes", "relred_yes"), ("rr_no", "relred_no")):
        L.append(f"labels_phys {a}: rows {len(m)} maxdev {np.nanmax(np.abs(m[a] - m[b])):.2e}")
    Vd = pd.read_csv(SRC / "labels_domain.csv").rename(columns={"label_domain": "domain"})
    Vd["src"] = Vd.label_source.map({"domains": "dom", "domains_union": "dom_u"})
    m = DM.merge(Vd, on=["set", "config", "arm", "src", "domain"], suffixes=("", "_v"))
    for a, b in (("p", "perm_p"), ("q", "q_family"), ("mean_lab", "mean_gain_labelled")):
        L.append(f"labels_dom {a}: rows {len(m)} maxdev {np.nanmax(np.abs(m[a] - m[b])):.2e}")
    Vs = pd.read_csv(SRC / "labels_spearman.csv")
    Vs["endpoint"] = Vs.endpoint.str.split(" ").str[0]
    m = SP.merge(Vs, on=["set", "config", "arm", "endpoint"], suffixes=("", "_v"))
    L.append(f"spearman rho: rows {len(m)} maxdev {np.nanmax(np.abs(m.rho - m.spearman_rho)):.2e}")
    (OUT / "compare_secondary_vs_v21.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
