import sys; sys.path.insert(0, "."); from a2_common import *
df = pd.read_csv("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s7-dxremoval/results.csv", low_memory=False,
                 usecols=["cell","half","trial","arm_role","loghr","se","rb","rs","mean_smd","cstat"])
SM = pd.read_csv("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s7-dxremoval/summary_ecg.csv")
rows = []
for cell in ["sparse", "loo_atrial_fibrillation", "cum_k1", "cum_k3", "cum_k8", "demo", "common10", "noextras", "loo_peripheral_arterial_disease", "rand0_k4"]:
    g = df[(df.cell == cell) & (df.half == "full")]
    for m in ["absd", "z2", "mean_smd", "cstat"]:
        d = diff(g[g.arm_role == "ECG"], g[g.arm_role == "base"], m)
        r = dict(cell=cell, metric=m, **summ(d))
        s = SM[(SM.cell == cell) & (SM.half == "full")].iloc[0]
        r.update(rep_d=s[f"d_{m}"], rep_p=s[f"p_{m}"], rep_k=s[f"k_{m}"], rep_clp=s.get(f"cl_p_{m}"), rep_loo=s.get(f"loo_pmax_{m}"))
        if m in ("absd", "z2"):
            sh = shuffle(g[g.arm_role == "ECG"], g[g.arm_role == "base"], m)
            r.update(sh_null=sh["null_mean"], sh_p=sh["p"], rep_sh_null=s[f"bs_{m}_null_mean"], rep_sh_p=s[f"bs_{m}_p"])
        rows.append(r)
R = pd.DataFrame(rows); R.to_csv("s7_recompute.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 30); print(R.round(4).to_string())
# halves for loo_AF
for h in "AB":
    g = df[(df.cell == "loo_atrial_fibrillation") & (df.half == h)]
    d = diff(g[g.arm_role == "ECG"], g[g.arm_role == "base"], "absd"); print("half", h, round(d.mean(),4), flip(d.values))
# AF vs placebo
g = df[(df.cell == "loo_atrial_fibrillation") & (df.half == "full")]
for pl in ["shufECG", "noise"]:
    d = diff(g[g.arm_role == "ECG"], g[g.arm_role == pl], "absd"); print("vs", pl, round(d.mean(),4), flip(d.values))
# loo_AF+ECG vs sparse+ECG and sparse base
sp = df[(df.cell == "sparse") & (df.half == "full")]
for a, b, lab in [(g[g.arm_role=="ECG"], sp[sp.arm_role=="ECG"], "looAF+ECG - sparse+ECG"), (g[g.arm_role=="base"], sp[sp.arm_role=="base"], "looAF base - sparse base"),
                  (g[g.arm_role=="ECG"], sp[sp.arm_role=="base"], "looAF+ECG - sparse base")]:
    d = diff(a, b, "absd"); print(lab, round(d.mean(),4), f"{(d<0).sum()}/{len(d)}", flip(d.values))
# per-trial contribution concentration for loo_AF absd
d = diff(g[g.arm_role == "ECG"], g[g.arm_role == "base"], "absd")
print("AF absd: share of top trial", round(d.abs().max()/d.abs().sum(),3), "top-3 share", round(d.abs().sort_values().iloc[-3:].sum()/d.abs().sum(),3), "cluster of top", CLUSTER[d.abs().idxmax()])
print("AF absd drop top trial:", round(d.drop(d.abs().idxmax()).mean(),4), flip(d.drop(d.abs().idxmax()).values))
# BH of shuffle p over distinct designs only
s = SM[SM.half=="full"].copy()
dup = {"cum_k1","rand0_k1","rand2_k1","rand2_k2"}
s2 = s[~s.cell.isin(dup)]
import sys; sys.path.insert(0,"/home/rbc58/github/ecg-tte/scripts/v16")
def bh(p):
    p=np.asarray(p); o=np.argsort(p); m=len(p); a=p[o]*m/np.arange(1,m+1); a=np.minimum.accumulate(a[::-1])[::-1]; q=np.empty(m); q[o]=np.minimum(a,1); return q
s2 = s2.assign(q=bh(s2.bs_absd_p.values))
print("BH shuffle p over 42 distinct designs, loo_AF q:", s2.loc[s2.cell=="loo_atrial_fibrillation","q"].round(4).tolist(), "min q", s2.q.min().round(4))
# joint BH: sign-flip p OR shuffle p requirement -> max(p_absd, bs_absd_p) as intersection-union
s2 = s2.assign(pmax=np.maximum(s2.p_absd, s2.bs_absd_p)); s2 = s2.assign(qmax=bh(s2.pmax.values))
print("IU (max of flip & shuffle p) BH, loo_AF:", s2.loc[s2.cell=="loo_atrial_fibrillation",["pmax","qmax"]].round(4).values.tolist(), "min", s2.qmax.min().round(4))
