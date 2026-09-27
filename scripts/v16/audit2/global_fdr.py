import sys; sys.path.insert(0, "."); from a2_common import *
A = "/mnt/raid0/rbc58/ecg-tte/audits/"
U = ["trial","loghr","se","rb","rs","mean_smd","cstat"]
cells = {}   # name -> (ECG df, base df)
def add(sweep, df, key):
    for c, g in df.groupby(key):
        e, b = g[g.arm_role=="ECG"], g[g.arm_role=="base"]
        if len(e) and len(b): cells[f"{sweep}:{c}"] = (e[U], b[U])
s1 = pd.read_csv(A+"claude-v16-s1-ladder/results.csv", usecols=["cell","half","arm_role"]+U); add("S1", s1[s1.half=="full"], "cell")
s3 = pd.read_csv(A+"claude-v16-s3-repr/results.csv", usecols=["cell","half","arm_role"]+U); add("S3", s3[s3.half=="full"], "cell")
s4 = pd.read_csv(A+"claude-v16-s4-subgroups/results.csv", usecols=["cell","half","arm_role"]+U); add("S4", s4[s4.half=="full"], "cell")
s2 = pd.read_csv(A+"claude-v16-s2-dropout/results.csv", usecols=["cell","half","arm_role","seed"]+U); s2 = s2[s2.half=="full"]
# S2: per-trial metrics averaged over seeds -> handled by averaging metric values; store seed-0 copy for dedupe with S6
S2avg = {}
for c, g in s2[s2.arm_role.isin(["ECG","base"])].groupby("cell"):
    S2avg[c] = g
    add("S2seed0", g[g.seed==0], "cell") if False else None
s6 = pd.read_csv(A+"claude-v16-s6-balance/results_p58.csv", usecols=["cell","half","arm_role"]+U, low_memory=False); add("S6", s6[s6.half=="full"], "cell")
s7 = pd.read_csv(A+"claude-v16-s7-dxremoval/results.csv", usecols=["cell","half","arm_role"]+U, low_memory=False); add("S7", s7[s7.half=="full"], "cell")
MET = ["absd","z2","mean_smd","cstat"]
def dvec(e, b, m): return diff(e, b, m)
rows, vecs = [], {}
seen = {}
for name, (e, b) in cells.items():
    if name.endswith(":unmatched"): continue
    ee, bb = e.drop_duplicates("trial").set_index("trial"), b.drop_duplicates("trial").set_index("trial")
    t = sorted(ee.index.intersection(bb.index))
    sig = tuple(np.round(np.r_[ee.loc[t].loghr.values, bb.loc[t].loghr.values], 7)) + tuple(t)
    if sig in seen: continue
    seen[sig] = name
    r = dict(cell=name, n=len(t))
    for m in MET:
        d = dvec(e, b, m); vecs[(name, m)] = d
        r[f"d_{m}"], r[f"p_{m}"] = d.mean(), flip(d.values)
    r["p_shuf_absd"] = shuffle(e, b, "absd", nperm=5000)["p"]
    r["p_shuf_z2"] = shuffle(e, b, "z2", nperm=5000)["p"]
    rows.append(r)
# S2 seed-averaged cells
for c, g in S2avg.items():
    if c == "unmatched": continue
    gg = g.copy(); gg["absd"] = (gg.loghr-gg.rb).abs(); gg["z2"] = (gg.loghr-gg.rb)**2/(gg.se**2+gg.rs**2)
    P = gg.groupby(["trial","arm_role"])[["absd","z2","mean_smd","cstat"]].mean().unstack()
    r = dict(cell=f"S2avg:{c}", n=len(P))
    for m in MET:
        d = (P[(m,"ECG")] - P[(m,"base")]).dropna(); vecs[(r["cell"], m)] = d
        r[f"d_{m}"], r[f"p_{m}"] = d.mean(), flip(d.values)
    # shuffle for seed-avg absd: permute rb,rs jointly and recompute seed-averaged |d|
    rng = np.random.default_rng(9); tr = sorted(set(gg.trial)); rbm = gg.groupby("trial").rb.first().loc[tr].values; rsm = gg.groupby("trial").rs.first().loc[tr].values
    L = {a: gg[gg.arm_role==a].pivot_table(index="trial", columns="seed", values="loghr").loc[tr].values for a in ("ECG","base")}
    S_ = {a: gg[gg.arm_role==a].pivot_table(index="trial", columns="seed", values="se").loc[tr].values for a in ("ECG","base")}
    fa = lambda rb_: np.nanmean(np.nanmean(np.abs(L["ECG"]-rb_[:,None]),1) - np.nanmean(np.abs(L["base"]-rb_[:,None]),1))
    fz = lambda rb_, rs_: np.nanmean(np.nanmean((L["ECG"]-rb_[:,None])**2/(S_["ECG"]**2+rs_[:,None]**2),1) - np.nanmean((L["base"]-rb_[:,None])**2/(S_["base"]**2+rs_[:,None]**2),1))
    oa, oz = fa(rbm), fz(rbm, rsm); na, nz = [], []
    for _ in range(5000):
        p = rng.permutation(len(tr)); na.append(fa(rbm[p])); nz.append(fz(rbm[p], rsm[p]))
    r["p_shuf_absd"], r["p_shuf_z2"] = float(np.mean(np.array(na) <= oa)), float(np.mean(np.array(nz) <= oz))
    rows.append(r)
R = pd.DataFrame(rows)
# drop S2avg p0 (duplicates S1 sparse/hdPS200 if seed-invariant)
R = R[~R.cell.isin(["S2avg:sparse_p0", "S2avg:hdPS200_p0"])]
def bh(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); a = p[o]*m/np.arange(1, m+1); a = np.minimum.accumulate(a[::-1])[::-1]; q = np.empty(m); q[o] = np.minimum(a, 1); return q
for m in MET: R[f"q_{m}"] = bh(R[f"p_{m}"])
R["q_shuf_absd"] = bh(R.p_shuf_absd); R["q_shuf_z2"] = bh(R.p_shuf_z2)
# intersection-union: significant AND benchmark-specific
R["p_iu_absd"] = np.maximum(R.p_absd, R.p_shuf_absd); R["q_iu_absd"] = bh(R.p_iu_absd)
R["p_iu_z2"] = np.maximum(R.p_z2, R.p_shuf_z2); R["q_iu_z2"] = bh(R.p_iu_z2)
R["sweep"] = R.cell.str.split(":").str[0]
R.to_csv("global_fdr_cells.csv", index=False)
print("unique cells:", len(R), R.sweep.value_counts().to_dict())
for m in MET + ["shuf_absd", "shuf_z2", "iu_absd", "iu_z2"]:
    dcol = "d_" + (m if m in MET else m.split("_")[-1])
    s = R[(R[f"q_{m}"] < 0.05) & (R[dcol] < 0)]
    print(f"{m}: {len(s)}/{len(R)} q<0.05 ", s.groupby("sweep").size().to_dict(), "| best:", R.sort_values(f"q_{m}").head(4)[["cell", f"q_{m}"]].round(3).values.tolist())
# effective number (Li-Ji) per metric
for m in MET:
    M = pd.DataFrame({c: vecs[(c, m)] for c in R.cell}).dropna()
    ev = np.linalg.eigvalsh(np.corrcoef(M.values.T)); ev = np.abs(ev)
    meff = np.sum((ev >= 1).astype(float) + (ev - np.floor(ev)))
    C = np.corrcoef(M.values.T); iu = np.triu_indices_from(C, 1)
    print(f"M_eff {m}: {meff:.1f} (trials {len(M)}, cells {M.shape[1]}), median r {np.median(C[iu]):.2f}, first-eig share {ev.max()/ev.sum():.2f}")
