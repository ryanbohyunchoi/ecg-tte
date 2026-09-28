"""Round-4 audit: CLMBR retention and balance on the common-anchor intersection (P1 demographics PS, full cohort, 33 trials).

Re-fits the PS (engine ps_logit, L2 C=1) and re-matches (engine match, caliper 0.2, 1:1) for base, +CLMBR64 and +ECG32,
then computes the 58-panel / non-coded-54 |SMD| (a) on each arm's own matched sample and (b) restricted to anchors
(smaller-arm patients) matched in BOTH base and the embedding arm (identical anchor population). Reproduction of
the v1.8 n_pairs / nc % < 0.1 is checked. Aggregates only."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from a4_common import *  # noqa: E402,F401
import v16_engine as E  # noqa: E402

VN = [c for c, _, _ in E.VARS]
NCV = [c for c, _, g in E.VARS if g != "Coded record"]


def panel(T, Hv, vc, s_idx, s_w):
    comp = pd.Series(E.smd_components(Hv, T.t, s_idx, s_w, T.t[s_idx]), index=T.H.columns)
    return pd.Series([comp[vc[c]].dropna().mean() if len(comp[vc[c]].dropna()) else np.nan for c in VN], index=VN)


def summ(sv):
    a, nc = sv.dropna(), sv[NCV].dropna()
    return dict(lt01=100 * (a < 0.1).mean(), nc_lt01=100 * (nc < 0.1).mean(), nc_mean=nc.mean())


def one(n):
    T = E.load_trial(n) if n in OLD18 else E.load_trial(n, cache=False)
    t = T.t
    Hv = T.H.to_numpy(float)
    vc = E.var_components(T.H)
    X = T.cov[T.demo].to_numpy(float)
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    na = int((t == anchor).sum())
    out, sets = [], {}
    for arm, Xa in (("base", X), ("CLMBR", np.hstack([X, T.clm_pc])), ("ECG", np.hstack([X, T.ecg_pc]))):
        lg = E.ps_logit(Xa, t, model="l2", C=1.0)
        s_idx, cl, s_w = E.match(lg, t, cal=0.2, ratio=1)
        sets[arm] = (s_idx, cl)
        out.append(dict(trial=n, arm=arm, subset="own", n_pairs=len(np.unique(cl)), retain=len(np.unique(cl)) / na,
                        **summ(panel(T, Hv, vc, s_idx, s_w))))
    for emb in ("CLMBR", "ECG"):
        common = np.intersect1d(np.unique(sets["base"][1]), np.unique(sets[emb][1]))
        for arm in ("base", emb):
            s_idx, cl = sets[arm]
            k = np.isin(cl, common)
            out.append(dict(trial=n, arm=arm, subset=f"common_{emb}", n_pairs=len(common), retain=len(common) / na,
                            **summ(panel(T, Hv, vc, s_idx[k], np.ones(k.sum())))))
    print(n, flush=True)
    return out


if __name__ == "__main__":
    os.umask(0o077)
    with Pool(16) as p:
        D = pd.DataFrame(sum(p.map(one, ALL33, chunksize=1), []))
    D.to_csv(OUT + "clmbr_common_anchor.csv", index=False)
    RC = pd.read_csv(A + "claude-v18-clmbr/results_all.csv", low_memory=False)
    RC = RC[(RC.ps == "P1") & (RC.half == "full") & RC.arm_role.isin(["base", "CLMBR", "ECG"])]
    KEYS = dict(zip(RC.trial, RC.key))
    ref = metrics(RC.rename(columns={"arm_role": "arm_"}).assign(trial=RC.trial + "|" + RC.arm_role))
    own = D[D.subset == "own"].assign(k=lambda x: x.trial + "|" + x.arm).set_index("k")
    print("reproduction: max |d n_pairs|", (own.n_pairs - ref.n_pairs.reindex(own.index)).abs().max(),
          "max |d nc_lt01|", (own.nc_lt01 - ref.nc_lt01.reindex(own.index)).abs().max())
    for sub, emb in (("own", "CLMBR"), ("common_CLMBR", "CLMBR"), ("own", "ECG"), ("common_ECG", "ECG")):
        g = D[D.subset == sub].pivot(index="trial", columns="arm")
        for m in ("nc_lt01", "lt01", "nc_mean"):
            d = (g[(m, emb)] - g[(m, "base")]) * (1 if m != "nc_mean" else -1)
            print(f"{sub:13s} {emb:5s} {m:8s} base {g[(m, 'base')].mean():.2f} emb {g[(m, emb)].mean():.2f} d {d.mean():+.2f} "
                  f"k {(d > 0).sum()}/33 p {flip1(d.values):.5f} clp {cluster_p(d, clusters(), KEYS)[0]:.4f}")
        print(f"   retain base {g[('retain', 'base')].mean():.3f} {emb} {g[('retain', emb)].mean():.3f}")
