"""Round-3 global multiplicity: unique full-cohort ECG-vs-base cells S1-S9 (18-trial), BH within metric.
Extends claude-v16-audit2/global_fdr.py (same dedupe signature, joint benchmark shuffle) with S8 / S9 and the
%|SMD|<0.1 metric (own computation from smd: columns)."""
import sys
sys.path.insert(0, "/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit3")
from a3_common import *  # noqa

U = ["trial", "loghr", "se", "rb", "rs", "mean_smd", "cstat", "pct"]
MET = ["absd", "z2", "mean_smd", "cstat", "pct"]


def load(f, extra=()):
    d = pd.read_csv(A + f, low_memory=False)
    sc = [c for c in d.columns if c.startswith("smd:")]
    x = d[sc].to_numpy(float)
    ok = np.isfinite(x)
    d["pct"] = 100 * np.where(ok, x < 0.1, False).sum(1) / ok.sum(1)
    return d[["cell", "half", "arm_role"] + list(extra) + U]


def met(x, m):
    if m == "absd":
        return (x.loghr - x.rb).abs()
    if m == "z2":
        return (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)
    return x[m]


cells = {}   # name -> per-trial DataFrame with columns metric_ECG, metric_base, loghr/se per arm, rb, rs


def add_plain(sweep, df, trials=None):
    for c, g in df[df.half == "full"].groupby("cell"):
        e = g[g.arm_role == "ECG"].drop_duplicates("trial").set_index("trial")
        b = g[g.arm_role == "base"].drop_duplicates("trial").set_index("trial")
        t = e.index.intersection(b.index).sort_values()
        if trials is not None:
            t = t.intersection(trials)
        if len(t) < 5:
            continue
        cells[f"{sweep}:{c}"] = dict(e=e.loc[t], b=b.loc[t], seeds=False)


def add_seedavg(sweep, df, trials=None):
    for c, g in df[df.half == "full"].groupby("cell"):
        e, b = g[g.arm_role == "ECG"], g[g.arm_role == "base"]
        if not len(e) or not len(b):
            continue
        cells[f"{sweep}:{c}"] = dict(e=e, b=b, seeds=True, trials=trials)


add_plain("S1", load("claude-v16-s1-ladder/results.csv"))
add_plain("S3", load("claude-v16-s3-repr/results.csv"))
add_plain("S4", load("claude-v16-s4-subgroups/results.csv"))
add_seedavg("S2avg", load("claude-v16-s2-dropout/results.csv", ["seed"]))
add_plain("S6", load("claude-v16-s6-balance/results_p58.csv"))
add_plain("S7", load("claude-v16-s7-dxremoval/results.csv"))
s8 = load("claude-v16-s8-headline/results_v2.csv", ["seed"])
add_plain("S8", s8[~s8.cell.str.startswith("sparse_p")])
add_seedavg("S8avg", s8[s8.cell.str.startswith("sparse_p")])
add_plain("S9", load("claude-v16-s9-covsets/results.csv"))
PH = pd.Index(PHYS)
add_plain("S8phys", s8[~s8.cell.str.startswith("sparse_p")], trials=PH)
add_seedavg("S8physavg", s8[s8.cell.str.startswith("sparse_p")], trials=PH)

rows, seen, DUP = [], {}, {}
rng = np.random.default_rng(31)
for name, C in cells.items():
    if name.endswith(":unmatched"):
        continue
    if C["seeds"]:
        e, b = C["e"].copy(), C["b"].copy()
        if C.get("trials") is not None:
            e, b = e[e.trial.isin(C["trials"])], b[b.trial.isin(C["trials"])]
        for x in (e, b):
            x["absd"], x["z2"] = met(x, "absd"), met(x, "z2")
        E_, B_ = e.groupby("trial")[MET].mean(), b.groupby("trial")[MET].mean()
        tr = sorted(E_.index.intersection(B_.index))
        sig = tuple(np.round(E_.loc[tr].absd.values, 7)) + tuple(tr)
        L = {a: x.pivot_table(index="trial", columns="seed", values="loghr").loc[tr].values for a, x in (("e", e), ("b", b))}
        SE = {a: x.pivot_table(index="trial", columns="seed", values="se").loc[tr].values for a, x in (("e", e), ("b", b))}
        rb0, rs0 = e.groupby("trial").rb.first().loc[tr].values, e.groupby("trial").rs.first().loc[tr].values
        fa = lambda r_, s_: np.nanmean(np.nanmean(np.abs(L["e"] - r_[:, None]), 1) - np.nanmean(np.abs(L["b"] - r_[:, None]), 1))
        fz = lambda r_, s_: np.nanmean(np.nanmean((L["e"] - r_[:, None]) ** 2 / (SE["e"] ** 2 + s_[:, None] ** 2), 1)
                                       - np.nanmean((L["b"] - r_[:, None]) ** 2 / (SE["b"] ** 2 + s_[:, None] ** 2), 1))
    else:
        e, b = C["e"], C["b"]
        tr = list(e.index)
        sig = tuple(np.round(np.r_[e.loghr.values, b.loghr.values], 7)) + tuple(tr)
        E_ = pd.DataFrame({m: met(e, m) for m in MET})
        B_ = pd.DataFrame({m: met(b, m) for m in MET})
        ok = np.isfinite(e.loghr.values) & np.isfinite(b.loghr.values)
        la, lb, sa, sb, rb0, rs0 = (v[ok] for v in (e.loghr.values, b.loghr.values, e.se.values, b.se.values, b.rb.values, b.rs.values))
        fa = lambda r_, s_, la=la, lb=lb: np.mean(np.abs(la - r_) - np.abs(lb - r_))
        fz = lambda r_, s_, la=la, lb=lb, sa=sa, sb=sb: np.mean((la - r_) ** 2 / (sa ** 2 + s_ ** 2) - (lb - r_) ** 2 / (sb ** 2 + s_ ** 2))
    if sig in seen:
        DUP[name] = seen[sig]
        continue
    seen[sig] = name
    r = dict(cell=name, n=len(tr), sweep=name.split(":")[0])
    for m in MET:
        d = (E_[m] - B_[m]).dropna()
        r[f"d_{m}"], r[f"p_{m}"] = d.mean(), flip(d.values)
    oa, oz = fa(rb0, rs0), fz(rb0, rs0)
    na, nz = [], []
    for _ in range(5000):
        p = rng.permutation(len(rb0))
        na.append(fa(rb0[p], rs0[p]))
        nz.append(fz(rb0[p], rs0[p]))
    r["p_shuf_absd"], r["p_shuf_z2"] = float(np.mean(np.array(na) <= oa)), float(np.mean(np.array(nz) <= oz))
    rows.append(r)
R = pd.DataFrame(rows)
R = R[~R.cell.isin(["S2avg:sparse_p0", "S2avg:hdPS200_p0"])]
R.to_csv(OUT + "global_cells_raw.csv", index=False)
print("duplicates (S8/S9):", {k: v for k, v in DUP.items() if k.startswith(("S8", "S9"))})
for fam, mask in (("18-trial S1-S9", R.n >= 17), ("incl. S8 physiology subsets", R.n >= 1)):
    Q = R[mask].copy()
    for m in MET:
        Q[f"q_{m}"] = bh(Q[f"p_{m}"])
    Q["q_shuf_absd"], Q["q_shuf_z2"] = bh(Q.p_shuf_absd), bh(Q.p_shuf_z2)
    Q["p_iu_absd"] = np.maximum(Q.p_absd, Q.p_shuf_absd)
    Q["q_iu_absd"] = bh(Q.p_iu_absd)
    print(f"\n== {fam}: {len(Q)} unique cells", Q.sweep.value_counts().to_dict())
    for m in MET + ["shuf_absd", "shuf_z2", "iu_absd"]:
        dcol = "d_" + (m if m in MET else m.split("_")[-1])
        good = (Q[dcol] > 0) if m == "pct" else (Q[dcol] < 0)
        s = Q[(Q[f"q_{m}"] < 0.05) & good]
        print(f"{m}: {len(s)}/{len(Q)} q<0.05", s.groupby("sweep").size().to_dict(), "| best:",
              Q.sort_values(f"q_{m}").head(3)[["cell", f"q_{m}"]].round(3).values.tolist())
    Q.to_csv(OUT + f"global_cells_{'all18' if 'S1-S9' in fam else 'withphys'}.csv", index=False)
    for c in ("S8:demo|cal0.1", "S8:demo|default", "S8:min7|default", "S8:common10|default", "S8phys:demo|cal0.1", "S8phys:min7|default", "S8phys:common10|default", "S1:r1_demo"):
        if c in set(Q.cell):
            x = Q[Q.cell == c].iloc[0]
            print("  ", c, {k: round(float(x[k]), 4) for k in ("d_absd", "p_absd", "q_absd", "p_shuf_absd", "q_shuf_absd", "d_z2", "q_z2", "q_shuf_z2", "d_pct", "q_pct", "q_mean_smd")})
