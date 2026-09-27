import sys; sys.path.insert(0, "."); from a2_common import *
D = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s6-balance/"
V = pd.read_csv(D + "verdicts.csv")
rows = []
for panel in ["x2np", "p58", "x2all"]:
    df = pd.read_csv(D + f"results_{panel}.csv", low_memory=False)
    if panel == "x2np":
        print("n_extra by cell (full, base), median/min/max:"); print(df[(df.half=="full")&(df.arm_role.isin(["base","unmatched"]))].groupby("cell")[["n_extra","n_extra_dropped","n_x_prox"]].agg(["median","min","max"]).to_string())
        print("rep_dev_mean_smd max", df.rep_dev_mean_smd.max(), " npairs mismatch", ((df.rep_npairs != df.n_pairs) & df.n_pairs.notna()).sum())
    df["absd"] = (df.loghr - df.rb).abs(); df["z2"] = (df.loghr-df.rb)**2/(df.se**2+df.rs**2)
    for cell in ["demo", "min7", "sparse", "sparse_drop50", "hdPS200", "clinical"]:
        for m in ["xsmd_other", "maha_all", "ks_mean", "ob_signed", "energy", "prog_ho_smd", "sub_smd", "miss_bnp"]:
            if m not in df or df[m].isna().all(): continue
            g = df[(df.cell==cell)&(df.half=="full")]
            d = diff(g[g.arm_role=="ECG"], g[g.arm_role=="base"], m)
            s = summ(d)
            hA = diff(*(lambda h: (h[h.arm_role=="ECG"], h[h.arm_role=="base"]))(df[(df.cell==cell)&(df.half=="A")]), m)
            hB = diff(*(lambda h: (h[h.arm_role=="ECG"], h[h.arm_role=="base"]))(df[(df.cell==cell)&(df.half=="B")]), m)
            v = V[(V.panel==panel)&(V.cell==cell)&(V.metric==m)]
            v = v.iloc[0] if len(v) else None
            rows.append(dict(panel=panel, cell=cell, metric=m, base=g[g.arm_role=="base"][m].mean(), ecg=g[g.arm_role=="ECG"][m].mean(), **s,
                             pA=flip(hA.values), pB=flip(hB.values),
                             rep_d=None if v is None else v.d_base_full, rep_p=None if v is None else v.p_base_full, rep_clp=None if v is None else v.cluster_p,
                             robust=None if v is None else v.robust))
R = pd.DataFrame(rows); R.to_csv("s6_recompute.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 300)
print(R[R.panel=="x2np"].round(4).to_string())
print("max |d - rep_d|", (R.d - R.rep_d).abs().max(), "max |p - rep_p|", (R.p - R.rep_p).abs().max(), "max |clp-rep|", (R.cl_p - R.rep_clp).abs().max())
