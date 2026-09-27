"""Round-3: caliper 0.1 vs 0.2 retention by arm and balance on the common-anchor intersection (demo PS, 18 trials, full)."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys
sys.path.insert(0, "/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit3")
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v16")
from multiprocessing import Pool
from a3_common import *  # noqa
import v16_engine as E

VN = [c for c, _, _ in E.VARS]


def p58(T, Hv, vc, s_idx, s_w):
    t = T.t
    comp = pd.Series(E.smd_components(Hv, t, s_idx, s_w, t[s_idx]), index=T.H.columns)
    sv = np.array([comp[vc[c]].dropna().mean() if len(comp[vc[c]].dropna()) else np.nan for c in VN])
    return sv


def one(n):
    T = E.load_trial(n)
    t = T.t
    Hv = T.H.to_numpy(float)
    vc = E.var_components(T.H)
    X = T.cov[T.demo].to_numpy(float)
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    n_anchor = int((t == anchor).sum())
    out, sets = [], {}
    for cal in (0.1, 0.2):
        for arm, Xa in (("base", X), ("ECG", np.hstack([X, T.ecg_pc]))):
            lg = E.ps_logit(Xa, t, model="l2", C=1.0)
            s_idx, cl, s_w = E.match(lg, t, cal=cal, ratio=1)
            sets[(cal, arm)] = (s_idx, cl)
            sv = p58(T, Hv, vc, s_idx, s_w)
            anc = np.unique(cl)
            out.append(dict(trial=n, cal=cal, arm=arm, subset="own", n_pairs=len(anc), retain=len(anc) / n_anchor,
                            pct=100 * np.nanmean(sv[np.isfinite(sv)] < 0.1), mean_smd=np.nanmean(sv), **{f"v:{c}": v for c, v in zip(VN, sv)}))
        # intersection of anchors matched in both arms at this caliper
        common = np.intersect1d(np.unique(sets[(cal, "base")][1]), np.unique(sets[(cal, "ECG")][1]))
        for arm in ("base", "ECG"):
            s_idx, cl = sets[(cal, arm)]
            keep = np.isin(cl, common)
            sv = p58(T, Hv, vc, s_idx[keep], np.ones(keep.sum()))
            out.append(dict(trial=n, cal=cal, arm=arm, subset="common_anchor", n_pairs=len(common), retain=len(common) / n_anchor,
                            pct=100 * np.nanmean(sv[np.isfinite(sv)] < 0.1), mean_smd=np.nanmean(sv), **{f"v:{c}": v for c, v in zip(VN, sv)}))
        # population shift: |SMD| of the 58 panel between matched anchors and ALL anchors (pre-match SD), per arm
        for arm in ("base", "ECG"):
            anc = np.unique(sets[(cal, arm)][1])
            allidx = np.where(t == anchor)[0]
            idx = np.r_[anc, allidx]
            tt = np.r_[np.ones(len(anc)), np.zeros(len(allidx))].astype(int)
            V2 = Hv[idx]
            with np.errstate(invalid="ignore", divide="ignore"):
                sd = np.sqrt((np.nanvar(Hv[t == 1], 0, ddof=1) + np.nanvar(Hv[t == 0], 0, ddof=1)) / 2)
                d = np.abs(np.nanmean(V2[tt == 1], 0) - np.nanmean(V2[tt == 0], 0)) / sd
            comp = pd.Series(d, index=T.H.columns)
            sv = np.array([comp[vc[c]].dropna().mean() if len(comp[vc[c]].dropna()) else np.nan for c in VN])
            out.append(dict(trial=n, cal=cal, arm=arm, subset="shift_vs_all_anchor", n_pairs=len(anc), retain=len(anc) / n_anchor,
                            pct=np.nan, mean_smd=np.nanmean(sv)))
    print(n, flush=True)
    return out


if __name__ == "__main__":
    with Pool(18) as p:
        res = sum(p.map(one, E.TRIALS), [])
    D = pd.DataFrame(res)
    D.to_csv(OUT + "retention_demo.csv", index=False)
    S8 = pd.read_csv(A + "claude-v16-s8-headline/results_v2.csv", low_memory=False)
    S8 = S8[(S8.half == "full") & S8.cell.isin(["demo|cal0.1", "demo|default"]) & S8.arm_role.isin(["base", "ECG"])]
    own = D[D.subset == "own"]
    chk = own.merge(S8.assign(cal=np.where(S8.cell == "demo|cal0.1", 0.1, 0.2)).rename(columns={"arm_role": "arm"})[["trial", "cal", "arm", "n_pairs", "p58_pct_lt10"]],
                    on=["trial", "cal", "arm"], suffixes=("", "_s8"))
    print("reproduce S8: max|d pairs|", (chk.n_pairs - chk.n_pairs_s8).abs().max(), "max|d pct|", (chk.pct - chk.p58_pct_lt10).abs().max())
    P = D.pivot_table(index=["trial", "cal", "subset"], columns="arm", values=["pct", "mean_smd", "retain"])
    for (cal, sub), g in P.groupby(level=[1, 2]):
        d = (g[("pct", "ECG")] - g[("pct", "base")]).droplevel([1, 2])
        dm = (g[("mean_smd", "ECG")] - g[("mean_smd", "base")]).droplevel([1, 2])
        dr = (g[("retain", "ECG")] - g[("retain", "base")]).droplevel([1, 2])
        print(f"cal {cal} {sub}: retain base {g[('retain','base')].mean():.3f} ECG {g[('retain','ECG')].mean():.3f} (d {dr.mean():+.4f}, "
              f"k lower {(dr<0).sum()}/18, p {flip(dr.values):.4f}); pct base {g[('pct','base')].mean():.2f} ECG {g[('pct','ECG')].mean():.2f} "
              f"d {d.mean():+.2f} k {(d>0).sum()}/18 p {flip(d.values):.4f} clp {cluster_p(d):.4f}; mean_smd d {dm.mean():+.4f} p {flip(dm.values):.4f}")
    for cal in (0.1, 0.2):
        for sub in ("own", "common_anchor"):
            g = D[(D.cal == cal) & (D.subset == sub)]
            M = {a: g[g.arm == a].set_index("trial")[[f"v:{c}" for c in VN]].sort_index().to_numpy(float) for a in ("base", "ECG")}
            print(f"love cal {cal} {sub}: base {int(love_count(M['base']))} ECG {int(love_count(M['ECG']))}, swap p {love_swap(M['ECG'], M['base'])[1]:.4f}")
    # cross-caliper: ECG cal0.1 vs base cal0.2 (does ECG gain survive against the looser-caliper base?)
    own = D[D.subset == "own"].set_index(["trial", "cal", "arm"]).pct.unstack([1, 2])
    for a, b in (((0.1, "ECG"), (0.2, "base")), ((0.1, "base"), (0.2, "base")), ((0.1, "ECG"), (0.2, "ECG"))):
        d = own[a] - own[b]
        print(f"{a} - {b}: d {d.mean():+.2f} p {flip(d.values):.4f}")
