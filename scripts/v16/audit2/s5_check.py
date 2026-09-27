import sys; sys.path.insert(0, "."); from a2_common import *
from scipy.optimize import minimize; from scipy.stats import norm
N = pd.read_csv("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco/nco_estimates.csv")
M = N[N.elig_pooled].copy()
M["fin"] = np.isfinite(M.loghr) & np.isfinite(M.se)
# keep NCO per trial-half estimable in all arms
na = M.groupby(["trial","half"]).apply(lambda g: g[["cell","arm_role"]].drop_duplicates().shape[0])
cnt = M.groupby(["trial","half","nco"]).fin.sum()
keep = cnt[cnt.values == na.reindex(cnt.index.droplevel(2)).values].reset_index()[["trial","half","nco"]]
M = M.merge(keep)
print("NCOs per trial (full, unmatched):", M[(M.half=="full")&(M.arm_role=="unmatched")].groupby("trial").size().describe()[["50%","min","max"]].tolist())
def fit(b, se):
    b, se = np.asarray(b), np.asarray(se)
    f = lambda p: -norm.logpdf(b, p[0], np.sqrt(np.exp(2*p[1]) + se**2)).sum()
    r = minimize(f, [0, np.log(.1)], method="Nelder-Mead", options=dict(xatol=1e-7, fatol=1e-9, maxiter=5000)); return r.x[0], np.exp(r.x[1])
F = M[M.half=="full"]
PT = F.groupby(["trial","cell","arm_role"]).apply(lambda g: pd.Series(dict(abs_b=np.mean(np.abs(g.loghr)), z2=np.mean(g.loghr**2/g.se**2), b2x=np.mean(g.loghr**2-g.se**2)))).reset_index()
u = PT[PT.arm_role=="unmatched"]; print("unmatched mean|b| %.3f b2x %.3f" % (u.abs_b.mean(), u.b2x.mean()), "pooled sigma unmatched %.3f" % fit(F[F.arm_role=="unmatched"].loghr, F[F.arm_role=="unmatched"].se)[1])
out = []
for cell in ["r1_demo","r3_min7","r5_sparse","r7_hdPS200","r8_clinical"]:
    for m in ["abs_b","z2","b2x"]:
        a = PT[(PT.cell==cell)&(PT.arm_role=="ECG")].set_index("trial")[m]; b = PT[(PT.cell==cell)&(PT.arm_role=="base")].set_index("trial")[m]
        d = a - b
        out.append(dict(cell=cell, metric=m, d=d.mean(), k=f"{(d<0).sum()}/18", p=flip(d.values), sd=d.std(ddof=1), mde80=2.8*d.std(ddof=1)/np.sqrt(len(d)),
                        base_level=b.mean()))
R = pd.DataFrame(out); print(R.round(4).to_string())
# pooled sigma and arm-swap permutation null (own code), for sparse & clinical & demo
rng = np.random.default_rng(3)
for cell in ["r1_demo","r5_sparse","r8_clinical"]:
    g = F[F.cell==cell]; Ga = {t: x for t, x in g[g.arm_role=="ECG"].groupby("trial")}; Gb = {t: x for t, x in g[g.arm_role=="base"].groupby("trial")}
    tr = sorted(Ga)
    def st(sw):
        A_ = pd.concat([Gb[t] if s else Ga[t] for t, s in zip(tr, sw)]); B_ = pd.concat([Ga[t] if s else Gb[t] for t, s in zip(tr, sw)])
        return fit(A_.loghr, A_.se)[1] - fit(B_.loghr, B_.se)[1]
    o = st([False]*len(tr)); nl = np.array([st(rng.random(len(tr)) < .5) for _ in range(400)])
    sb = fit(g[g.arm_role=="base"].loghr, g[g.arm_role=="base"].se)[1]
    print(cell, "sigma base %.3f ECG %.3f d %.4f perm p %.3f null SD %.4f  MDE80(2.8*SD) %.4f = %.0f%% of base sigma" % (sb, sb+o, o, np.mean(np.abs(nl) >= abs(o)-1e-12), nl.std(), 2.8*nl.std(), 100*2.8*nl.std()/sb))
