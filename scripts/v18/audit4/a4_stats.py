"""Round-4 audit: independent recomputation of the v1.7 / S11 / v1.8 (AF, CLMBR) / S10 headline numbers from the
per-trial result CSVs, with own metric and test code (a4_common). Aggregates only."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from a4_common import *  # noqa

os.umask(0o077)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
CL = clusters()
rows = []


def load(f, ps_map=None):
    R = pd.read_csv(A + f, low_memory=False)
    if ps_map:
        R["ps"] = R.ps.replace(ps_map)
    return R


def M(R, ps, arm, half="full", trials=None):
    g = R[(R.ps == ps) & (R.arm_role == arm) & (R.half == half)]
    m = metrics(g)
    return m.loc[trials] if trials is not None else m


def contrast(tag, R, ps, trials, metric, a="ECG", b="base", placebos=("shufECG", "noise"), two=False, pool=None, R_h=None):
    f = flip2 if two else flip1
    sg = 1 if metric in HIGHER else -1
    Fa, Fb = M(R, ps, a, trials=trials), M(R, ps, b, trials=trials)
    d = sg * (Fa[metric] - Fb[metric])
    key = Fa["key"].to_dict() if "key" in Fa else {t: t.replace("-", "_") for t in trials}
    r = dict(tag=tag, ps=ps, metric=metric, contrast=f"{a} vs {b}", n=len(trials), mean_b=Fb[metric].mean(), mean_a=Fa[metric].mean(),
             k=f"{int((d > 0).sum())}/{int(d.notna().sum())}", p=f(d.values))
    for pl in placebos:
        Fp = M(R, ps, pl, trials=trials)
        r[f"mean_{pl}"] = Fp[metric].mean()
        r[f"p_vs_{pl}"] = f((sg * (Fa[metric] - Fp[metric])).values)
    try:
        r["cluster_p"], r["n_cl"] = cluster_p(d, CL, key, two)
    except KeyError:
        r["cluster_p"], r["n_cl"] = np.nan, np.nan
    r["loo_max"] = loo(d, two) if len(trials) > 2 else np.nan
    for h in ("A", "B"):
        dh = sg * (M(R, ps, a, h, trials)[metric] - M(R, ps, b, h, trials)[metric])
        r[f"p_{h}"] = f(dh.values)
    if metric in ("absd", "z2"):
        args = (Fa.loghr.values, Fb.loghr.values, Fa.se.values, Fb.se.values)
        r["bs_perm"] = bshuffle(*args, Fb.rb.values, Fb.rs.values, Fb.rb.values, Fb.rs.values, metric, "perm")[2]
        if pool is not None:
            for nm, (prb, prs) in pool.items():
                for mode in ("pool_norep", "pool_rep", "pool_indep"):
                    o, nm_, p = bshuffle(*args, prb, prs, Fb.rb.values, Fb.rs.values, metric, mode)
                    r[f"bs_{nm}_{mode}"] = p
                r[f"bs_obs"], r[f"bs_{nm}_nullmean"] = o, bshuffle(*args, prb, prs, Fb.rb.values, Fb.rs.values, metric, "pool_norep")[1]
    rows.append(r)
    return r, d


R17 = load("claude-v17-confirm/results_all.csv")
R5 = load("claude-v17-confirm/results_p5.csv", {"P2": "P5"})
RAF = load("claude-v18-af-confirm/results_af5.csv")
RC = load("claude-v18-clmbr/results_all.csv")
RC["arm_role"] = RC.arm_role.replace({"noise32": "noise"})

b33 = M(R17, "P1", "base", trials=ALL33)
b5 = M(RAF, "P1", "base", trials=AF5)
POOL33 = (b33.rb.values, b33.rs.values)
POOL38 = (np.r_[b33.rb.values, b5.rb.values], np.r_[b33.rs.values, b5.rs.values])
pools = {"p33": POOL33, "p38": POOL38}

# ---------------------------------------------------------------- 1. v1.7 confirmation (P1, P2)
for ps in ("P1", "P2"):
    for sc, tr in (("new15", NEW15), ("all33", ALL33), ("old18", OLD18)):
        for m in ("lt01", "x_lt01", "mean_smd", "cstat", "absd", "z2", "cons"):
            contrast(f"v17_{sc}", R17, ps, tr, m, pool=pools if m in ("absd", "z2") else None)
# exact vs Monte-Carlo check of the sign-flip at k = 33
d33 = M(R17, "P1", "ECG", trials=ALL33).lt01 - M(R17, "P1", "base", trials=ALL33).lt01
print("sign-flip all33 P1 lt01: exact", flip1(d33.values), "MC(2e5)", flip1_mc(d33.values))
dd = -(M(R17, "P1", "ECG", trials=ALL33).absd - M(R17, "P1", "base", trials=ALL33).absd)
print("sign-flip all33 P1 absd: exact", flip1(dd.values), "MC(2e5)", flip1_mc(dd.values))

# ---------------------------------------------------------------- 2. S11 P5
for sc, tr in (("all33", ALL33), ("new15", NEW15), ("old18", OLD18), ("AF7", AF7)):
    for m in ("lt01", "x_lt01", "absd", "cons"):
        contrast(f"s11_{sc}", R5, "P5", tr, m, pool=pools if m == "absd" else None)

# ---------------------------------------------------------------- 3. v1.7 category emulation (P1, P2) incl. AF-7
for ps in ("P1", "P2"):
    for cat in ("AF", "HTN", "HF", "DM", "Other"):
        tr = [t for t in ALL33 if CATEGORY[t] == cat]
        for m in ("absd", "z2", "cons"):
            contrast(f"cat_{cat}", R17, ps, tr, m, pool=pools if m != "cons" else None)
J = json.load(open(REPO + "docs/v17/trial_selection.json"))
key33 = M(R17, "P1", "base", trials=ALL33).key.to_dict()
hi = [t for t in ALL33 if J["trials"][key33[t]]["ecg_relevance"] == "high"]
print("blinded ECG relevance high:", hi)
for ps in ("P1", "P2"):
    for m in ("absd", "z2"):
        contrast("cat_ECGhigh", R17, ps, hi, m, pool=pools)

# ---------------------------------------------------------------- 4. v1.8 AF confirmation
RA = pd.concat([R17[R17.ps.isin(["P1"])], R5[R5.ps == "P5"], RAF], ignore_index=True)
for sc, tr in (("AF5", AF5), ("AF12", AF7 + AF5), ("AF7", AF7)):
    for ps in ("P1", "P5"):
        for m in ("absd", "z2", "cons", "lt01", "x_lt01"):
            contrast(f"v18af_{sc}", RA, ps, tr, m, pool=pools if m in ("absd", "z2") else None)

# ---------------------------------------------------------------- 5. CLMBR (P1, P5, P2)
PL = ("shufCLMBR", "noise64")
for ps in ("P1", "P5", "P2"):
    for m in ("nc_lt01", "lt01", "absd", "z2", "cons"):
        contrast("clmbr_all33", RC, ps, ALL33, m, "CLMBR", "base", PL, pool={"p33": POOL33} if m in ("absd", "z2") else None)
        contrast("clmbr_all33", RC, ps, ALL33, m, "ECG", "base", ("shufECG", "noise"), pool={"p33": POOL33} if m in ("absd", "z2") else None)
        contrast("clmbr_all33", RC, ps, ALL33, m, "CLMBR", "ECG", (), two=True)
        contrast("clmbr_all33", RC, ps, ALL33, m, "CLMBR+ECG", "CLMBR", ("CLMBR+shufECG",))
    contrast("clmbr_new15", RC, ps, NEW15, "nc_lt01", "CLMBR", "base", PL)
    contrast("clmbr_old18", RC, ps, OLD18, "nc_lt01", "CLMBR", "base", PL)
    contrast("clmbr_AF7", RC, ps, AF7, "nc_lt01", "CLMBR", "base", PL)
    contrast("clmbr_AF7", RC, ps, AF7, "absd", "CLMBR", "base", PL, pool={"p33": POOL33})
    contrast("clmbr_AF7", RC, ps, AF7, "absd", "ECG", "base", ("shufECG",), pool={"p33": POOL33})
# retention: pairs / smaller arm, per arm; relation between retention loss and balance gain
ret = {}
for arm in ("base", "CLMBR", "ECG", "CLMBR+ECG", "shufCLMBR", "noise64"):
    m = M(RC, "P1", arm, trials=ALL33)
    ret[arm] = m.n_pairs / np.minimum(m.n_t, m.n_c)
ret = pd.DataFrame(ret)
print("\nP1 retention (pairs / smaller arm), mean over 33:\n", ret.mean().round(4).to_string())
pr = (ret["CLMBR"] / ret["base"])
print("CLMBR pairs / base pairs: mean", round(pr.mean(), 4), "min", round(pr.min(), 3), "median", round(pr.median(), 3))
print("ECG pairs / base pairs: mean", round((ret["ECG"] / ret["base"]).mean(), 4))
gain = M(RC, "P1", "CLMBR", trials=ALL33).nc_lt01 - M(RC, "P1", "base", trials=ALL33).nc_lt01
loss = ret["base"] - ret["CLMBR"]
from scipy.stats import spearmanr  # noqa: E402
print("Spearman(retention loss, nc balance gain) CLMBR P1:", spearmanr(loss, gain))
lo = loss <= loss.median()
print("nc gain in the 17 trials with smallest retention loss:", round(gain[lo].mean(), 2), flip1(gain[lo].values),
      "| largest:", round(gain[~lo].mean(), 2), flip1(gain[~lo].values))
ret.assign(nc_gain=gain).to_csv(OUT + "clmbr_retention_from_results.csv")

# ---------------------------------------------------------------- 6. S10 (two-sided, as in s10_summarize) + per-trial table
S10 = pd.read_csv(A + "claude-v16-s10-demo6/results.csv")
S10 = S10[S10.caliper == 0.2].copy()
S10["ps"] = "P2"
S10["key"] = S10.trial.map(lambda t: t)
from audit_v16 import CLUSTER as C16  # noqa: E402  (the cluster map S10 used; constant)
for m in ("lt01", "mean_smd", "cstat", "absd", "z2"):
    sg = 1 if m in HIGHER else -1
    Fa, Fb = M(S10, "P2", "ECG", trials=OLD18), M(S10, "P2", "base", trials=OLD18)
    Fs, Fn = M(S10, "P2", "shufECG", trials=OLD18), M(S10, "P2", "noise", trials=OLD18)
    d = sg * (Fa[m] - Fb[m])
    r = dict(tag="s10_old18", ps="P2(S10)", metric=m, contrast="ECG vs base (two-sided)", n=18, mean_b=Fb[m].mean(), mean_a=Fa[m].mean(),
             k=f"{int((d > 0).sum())}/18", p=flip2(d.values), p_vs_shufECG=flip2((sg * (Fa[m] - Fs[m])).values),
             p_vs_noise=flip2((sg * (Fa[m] - Fn[m])).values),
             cluster_p=flip2(d.groupby(d.index.map(C16)).mean().values), loo_max=loo(d, True),
             p_A=flip2((sg * (M(S10, "P2", "ECG", "A", OLD18)[m] - M(S10, "P2", "base", "A", OLD18)[m])).values),
             p_B=flip2((sg * (M(S10, "P2", "ECG", "B", OLD18)[m] - M(S10, "P2", "base", "B", OLD18)[m])).values))
    if m in ("absd", "z2"):
        r["bs_perm"] = bshuffle(Fa.loghr.values, Fb.loghr.values, Fa.se.values, Fb.se.values, Fb.rb.values, Fb.rs.values,
                                Fb.rb.values, Fb.rs.values, m, "perm")[2]
    rows.append(r)
Fa, Fb = M(S10, "P2", "ECG", trials=OLD18), M(S10, "P2", "base", trials=OLD18)
pt = pd.DataFrame({"bal_b": Fb.lt01, "bal_e": Fa.lt01, "rct_hr": np.exp(Fb.rb), "hr_b": np.exp(Fb.loghr), "hr_e": np.exp(Fa.loghr),
                   "absd_b": Fb.absd, "absd_e": Fa.absd, "cons_b": Fb.cons > 0, "cons_e": Fa.cons > 0})
pt.round(3).to_csv(OUT + "s10_per_trial_recomputed.csv")
print("\nS10 per-trial (recomputed):\n", pt.round(2).to_string())
print("closer", int((pt.absd_e < pt.absd_b).sum()), "/18; consistent", int(pt.cons_b.sum()), "->", int(pt.cons_e.sum()))

S = pd.DataFrame(rows)
S.to_csv(OUT + "recompute.csv", index=False)
print(S.round(4).to_string(index=False))
