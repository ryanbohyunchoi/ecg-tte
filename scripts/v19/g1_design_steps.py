#!/usr/bin/env python
"""v1.9 G1 (docs/v18/V19_GERMAN_STYLE_PLAN.md): ECG imbalance as an orthogonal diagnostic across design steps
(German et al. 2025 Fig 2 analogue). Exploratory.

Design steps per trial:
  S0  crude contrast in drug vs comparator initiators WITHOUT trial eligibility gates: build_trial_cohort.py stages
      s1-s4 unchanged (first use in window, comparator washout, prior activity 365 d, dedupe; switch_seq designs:
      the same candidate records then sequential sampling), with the disease gate, all other gates (require_all,
      first_dx_within, ecg_text, pci, procedure_1d, require_drugs) and every declared exclusion removed; age >= 18
      (trial-specific min/max age dropped). Built into audits/claude-v19-g1-<trial>-s0/ (cohort, ECG selection,
      BCL embeddings on an idle GPU, phenotype heads re-trained excluding the S0 roster, physiology panel v2).
  S1  trial cohort (v16 engine analysis set, T.keys), unmatched
  S2  sparse-PS matched (T.X_dx), S3 hdPS200 matched (T.X_dx + T.hd(200)), S4 clinical-PS matched (T.X_core);
      L2 C = 1 PS, greedy 1:1 caliper 0.2 SD logit (= v16_engine.run_cell / v18_embed_compare full half, arm base).
Diagnostics (none of them in any PS), in each step's (matched) sample:
  |SMD| of the 5 AI-ECG phenotype scores (T.ph = ph_lvef_le_40_logit, ph_afib_logit, ph_male_logit, ph_lvef_pred,
  ph_age_pred); ph_mean = mean over the 5; ph3_mean = mean over the 3 non-demographic scores (LVEF<=40, AF, LVEF);
  ecg_c = 5-fold cross-fitted L2 (C = 1) logistic AUC of treatment from 32 ECG PCs (v16_engine.balance_cstat);
  shuf_c = same with PCs permuted across patients (placebo, expected 0.5);
  held-out echo LVEF (physpanel v2 LVFUNC__ef) and NT-proBNP (BNP__ntprobnp raw and log) |SMD| where measured
  (echo masked for index < 2016-07-31). SMD denominators: pooled SD of the step's unmatched rows (S0: S0 rows;
  S1-S4: S1 rows), as the engine.

Usage:
  g1_design_steps.py cohort --trial KEY --out DIR       (internal) gate-free cohort via build_trial_cohort.main
  g1_design_steps.py build --trial NAME --gpu G         S0 data pipeline (resumable; skips finished steps)
  g1_design_steps.py run [--workers 12]                 S1-S4 for the 38 trials + S0 where built -> OUT/steps.csv
  g1_design_steps.py summarize                          tests, figure docs/v19/G1_design_steps.png, OUT/*.csv
Outputs aggregate only (OUT = audits/claude-v19-g1-design-steps; umask 077; counts 1-10 suppressed).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import copy  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "v18"))
sys.path.insert(0, str(SCRIPTS / "v16"))

ROOT = Path("/mnt/raid0/rbc58/ecg-tte")
A = ROOT / "audits"
OUT = A / "claude-v19-g1-design-steps"
DOCS = SCRIPTS.parent / "docs" / "v19"
PY = str(ROOT / "software/tte-analysis/bin/python")
BCL = ROOT / "software/bcl-smoke-runtime-zZ5FVVsd"
CK = ("/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_"
      "Dropout0.5_08_26_2026/trained_12lead_30.pt")
ECHO_START = "2016-07-31"
PH = ["ph_lvef_le_40_logit", "ph_afib_logit", "ph_male_logit", "ph_lvef_pred", "ph_age_pred"]
PH3 = ["ph_lvef_le_40_logit", "ph_afib_logit", "ph_lvef_pred"]
FOCUS = ["empa-reg", "aristotle", "east-afnet4", "paradigm-hf-seq"]
STEPS = ["S0", "S1", "S2", "S3", "S4"]
STEP_LAB = {"S0": "S0 ungated initiators", "S1": "S1 trial cohort", "S2": "S2 sparse PS", "S3": "S3 hdPS200",
            "S4": "S4 clinical PS"}
MIN_CELL = 11


def s0dir(n):
    return A / f"claude-v19-g1-{n}-s0"


# ================================================================ S0 cohort (gate-free build_trial_cohort)
class _Con:
    """duckdb proxy: the disease-gate table s5 becomes a copy of s4 (no gate)."""

    def __init__(self, c):
        self._c = c

    def execute(self, sql, *a, **k):
        if sql.lstrip().startswith("CREATE TEMP TABLE s5 AS SELECT * FROM s4 WHERE"):
            sql = "CREATE TEMP TABLE s5 AS SELECT * FROM s4"
        return self._c.execute(sql, *a, **k)

    def __getattr__(self, k):
        return getattr(self._c, k)


def cmd_cohort(a):
    import build_trial_cohort as btc
    spec = copy.deepcopy(btc.TRIALS[a.trial])
    g = spec["gate"]
    keep = {k: g[k] for k in ("any_before_or_on_index", "window_30d") if k in g} or {"any_before_or_on_index": ["I50"]}
    spec["gate"] = keep  # only used to build the (unused) condition table; s5 := s4 via _Con
    spec["exclusions"] = {}
    spec["min_age"] = 18
    spec.pop("max_age", None)
    spec["spec_version"] = f"{spec.get('spec_version', '')}+v19g1-s0-nogates"
    btc.TRIALS[a.trial] = spec
    orig = btc.connect
    btc.connect = lambda *x, **k: _Con(orig(*x, **k))
    sys.argv = ["build_trial_cohort.py", "--trial", a.trial, "--output-dir", a.out, "--threads", str(a.threads)]
    btc.main()


def _run(cmd, log, env=None):
    with open(log, "w") as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(SCRIPTS), env=env)
    if r.returncode:
        raise RuntimeError(f"failed ({r.returncode}): {' '.join(map(str, cmd[:3]))} ... see {log}")


def gpu_idle(g):
    u = subprocess.run(["nvidia-smi", "-i", str(g), "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True).stdout.strip().split(",")
    return int(u[0]) < 1000 and int(u[1]) < 5


def reuse_existing(n, B):
    """GPU saver: ECGs (by fileID) already embedded with the same checkpoint / settings in an analysed trial's BCL run
    (audits/claude-<trial>-bcl for the 38 registry trials, the focus-trial S0 full re-embeds) are copied into an extra
    shard (embeddings/shard_reuse_00000.npy + _index.csv, read by select_cohort_ecgs link); only the rest is embedded.
    Determinism is audited on the focus trials (full re-embed vs existing S1 embeddings, log emb_maxabs_dev_*)."""
    import glob as _g
    import v18_af_confirm as AF
    sel = pd.read_parquet(B / "input/restricted_selection.parquet")
    need = set(sel.fileID)
    dirs = [A / f"claude-{t}-bcl/embeddings" for t in AF.V.ALL if t != "comet"] + [
        s0dir(t) / "bcl/embeddings" for t in FOCUS if (s0dir(t) / "READY").exists()]
    vecs, ids = [], []
    for d in dirs:
        cf = d / "embedding_config.json"
        if not cf.exists() or d == s0dir(n) / "bcl/embeddings":
            continue
        c = json.load(open(cf))
        if not (c["checkpoint_path"] == CK and c["signal_representation"] == "lead_time_transformer" and c["embed_dim"] == 256
                and not c["amp"] and c["data_roots"] == ["/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"]):
            continue
        for f in sorted(_g.glob(f"{d}/shard_*[0-9].npy")):
            ix = pd.read_csv(f.replace(".npy", "_index.csv"), keep_default_na=False)
            ok = (ix.error == "").to_numpy() & ix.fileID.isin(need).to_numpy()
            if ok.any():
                X = np.load(f, mmap_mode="r")[ok]
                good = np.isfinite(X).all(1) & (np.abs(X).sum(1) > 0)
                vecs.append(np.asarray(X[good], np.float32))
                got = ix.fileID.to_numpy()[ok][good]
                ids.extend(got)
                need -= set(got)
        if not need:
            break
    E = B / "embeddings"
    E.mkdir(mode=0o700, exist_ok=True)
    if ids:
        Xr = np.concatenate(vecs)
        u = ~pd.Index(ids).duplicated()
        np.save(E / "shard_reuse_00000.npy", Xr[u])
        pd.DataFrame({"row": np.arange(int(u.sum())), "fileID": np.array(ids)[u], "error": ""}).to_csv(
            E / "shard_reuse_00000_index.csv", index=False)
    miss = sel[sel.fileID.isin(need)]
    inp, fmt = B / "input/restricted_input_missing.csv", B / "input/restricted_formats_missing.csv"
    miss[["fileID"]].to_csv(inp, index=False)
    pd.DataFrame({"fileID": miss.fileID, "format_new": "adapter_non250"}).to_csv(fmt, index=False)
    json.dump(dict(n_selected=int(len(sel)), n_reused=int(len(sel) - len(miss)), n_to_embed=int(len(miss))),
              open(B / "reuse.json", "w"))
    return inp, fmt


def cmd_build(a):
    import v18_af_confirm as AF
    os.umask(0o077)
    n = a.trial
    key = AF.V.KEY[n]
    D = s0dir(n)
    D.mkdir(mode=0o700, exist_ok=True)
    L = D / "logs"
    L.mkdir(mode=0o700, exist_ok=True)
    st = D / "status"
    say = lambda m: open(st, "a").write(f"{time.strftime('%H:%M:%S')} {m}\n")
    C = D / "cohort"
    ros = C / "restricted_cohort.parquet"
    if not ros.exists():
        say("cohort start")
        _run([PY, str(HERE / "g1_design_steps.py"), "cohort", "--trial", key, "--out", str(C), "--threads", "8"], L / "cohort.log")
    say("cohort done")
    B = D / "bcl"
    if not (B / "input").exists():
        B.mkdir(mode=0o700, exist_ok=True)
        _run([PY, "select_cohort_ecgs.py", "select", "--cohort", str(ros), "--output-dir", str(B / "input")], L / "select.log")
    if not (B / "restricted_embeddings_part-00000.parquet").exists():
        inp, fmt = B / "input/restricted_input.csv", B / "input/restricted_formats_no250.csv"
        if a.reuse:
            inp, fmt = reuse_existing(n, B)
        n_emb = sum(1 for _ in open(inp)) - 1
        if n_emb > 0 and not gpu_idle(a.gpu):
            raise SystemExit(f"GPU {a.gpu} not idle")
        say(f"BCL on GPU {a.gpu} ({n_emb} ECGs to embed)")
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(a.gpu)}
        n_emb > 0 and _run([str(BCL / "env/bin/python"), "bcl_embed_uv.py", "--upstream-dir", str(BCL / "upstream"), "--", "--checkpoint-path", CK,
              "--input-file", str(inp), "--formats-csv", str(fmt),
              "--data-roots", "/mnt/raid0/bb2238/signals/preprocessed/all_ecgs", "--output-dir", str(B / "embeddings"),
              "--batch-size", "64", "--num-workers", "4", "--shard-size", "512", "--no-quality-filter", "--no-deduplicate",
              "--no-partial", "--no-amp", "--no-overwrite", "--no-ddp-autodetect"], B / "run.log", env=env)
        _run([PY, "select_cohort_ecgs.py", "link", "--selection-dir", str(B / "input"), "--embeddings-dir", str(B / "embeddings")],
             B / "link.json")
    say("BCL done")
    P = D / "phenotypes"
    if not (P / "restricted_cohort_phenotypes.parquet").exists():
        _run([PY, "train_ecg_phenotype_heads.py", "--phenotype-set", str(A / "claude-ecg-phenotype-set/restricted_phenotype_set.parquet"),
              "--phenotype-embeddings", str(A / "claude-ecg-phenotype-set/embeddings"),
              "--cohort-embeddings-glob", str(B / "restricted_embeddings_part-*.parquet"), "--exclude-cohort", str(ros),
              "--output-dir", str(P)], L / "phenotypes.log")
    say("phenotypes done")
    Q = D / "physpanel"
    if not (Q / "restricted_physiology_panel.parquet").exists():
        _run([PY, "build_physiology_panel_v2.py", "--roster", str(ros), "--threads", "8", "--output-dir", str(Q)], L / "physpanel.log")
    say("physpanel done")
    (D / "READY").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    say("READY")


# ================================================================ diagnostics
def _E():
    import v16_engine as E
    return E


def smd_abs(V, t, s_idx, s_w, ref_t=None, ref_V=None):
    """|SMD| per column (NaN-aware weighted means in the sample / pooled SD of the reference rows)."""
    E = _E()
    RV = V if ref_V is None else ref_V
    Rt = t if ref_t is None else ref_t
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt((np.nanvar(RV[Rt == 1], axis=0, ddof=1) + np.nanvar(RV[Rt == 0], axis=0, ddof=1)) / 2)
        S = V[s_idx]
        st = t[s_idx]
        d = np.abs(E._wmean(S[st == 1], s_w[st == 1]) - E._wmean(S[st == 0], s_w[st == 0])) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def nmeas(v, t):
    ok = ~np.isnan(v)
    return int((ok & (t == 1)).sum()), int((ok & (t == 0)).sum())


def diagnostics(ph, pc, lvef, bnp, t, s_idx, s_w, perm, seed=0):
    """ph (n x 5), pc (n x 32), lvef, bnp (n,), t: rows of the reference (unmatched) set; s_idx/s_w: sample."""
    E = _E()
    r = {}
    d = smd_abs(ph, t, s_idx, s_w)
    for c, v in zip(PH, d):
        r[f"smd:{c}"] = float(v)
    r["ph_mean"] = float(np.nanmean(d))
    r["ph3_mean"] = float(np.nanmean(d[[PH.index(c) for c in PH3]]))
    st = t[s_idx]
    r["ecg_c"] = E.balance_cstat(pc[s_idx], st, s_w, model=("l2", 1.0), seed=seed)
    r["shuf_c"] = E.balance_cstat(pc[perm][s_idx], st, s_w, model=("l2", 1.0), seed=seed)
    lb = np.log(np.where(bnp > 0, bnp, np.nan))
    M = np.column_stack([lvef, bnp, lb])
    dm = smd_abs(M, t, s_idx, s_w)
    r["smd_lvef"], r["smd_bnp"], r["smd_logbnp"] = map(float, dm)
    for nm, v in (("lvef", lvef), ("bnp", bnp)):
        a1, a0 = nmeas(v[s_idx], st)
        r[f"nmeas_{nm}_t"], r[f"nmeas_{nm}_c"] = a1, a0
        if min(a1, a0) < 20:  # too few measured in an arm: SMD not reported
            r["smd_lvef" if nm == "lvef" else "smd_bnp"] = np.nan
            if nm == "bnp":
                r["smd_logbnp"] = np.nan
    return r


def s0_data(n):
    """S0 arrays (restricted, in memory): keys, t, ph, pc32, lvef, bnp, index_date."""
    from eval_longtail_balance import emb, pcs
    D = s0dir(n)
    ro = pd.read_parquet(D / "cohort/restricted_cohort.parquet").set_index("patient_key")
    ecg = emb(str(D / "bcl/restricted_embeddings_part-*.parquet"))
    ph = pd.read_parquet(D / "phenotypes/restricted_cohort_phenotypes.parquet").set_index("patient_key")
    keys = ro.index.intersection(ecg.index).intersection(ph.index).sort_values()
    PP = pd.read_parquet(D / "physpanel/restricted_physiology_panel.parquet").set_index("patient_key").reindex(keys)
    idx = pd.to_datetime(ro.index_date.reindex(keys))
    early = idx.lt(pd.Timestamp(ECHO_START)).fillna(True).to_numpy()
    lvef = pd.to_numeric(PP["LVFUNC__ef"], errors="coerce").to_numpy(float)
    lvef[early] = np.nan
    bnp = pd.to_numeric(PP["BNP__ntprobnp"], errors="coerce").to_numpy(float)
    raw = ecg.loc[keys].to_numpy(float)
    return dict(keys=keys, t=ro.treated.reindex(keys).to_numpy(int), ph=ph.loc[keys, PH].to_numpy(float),
                pc=pcs(raw, 64)[:, :32], raw=raw, lvef=lvef, bnp=bnp, idx=idx.to_numpy())


def trial_task(n):
    import v18_af_confirm as AF
    from v13_common import cox, match, ps_logit
    E = _E()
    V = AF.V
    t0 = time.time()
    T = E.load_trial(n) if n in V.OLD else E.load_trial(n, cache=False)
    from v13_common import paths
    assert list(pd.read_parquet(paths(n)["ph"]).columns[1:]) == PH
    t = T.t
    N = len(t)
    perm = np.random.default_rng(190_001).permutation(N)
    lvef = T.H["pp_LVFUNC__ef"].to_numpy(float) if "pp_LVFUNC__ef" in T.H else np.full(N, np.nan)
    bnp = T.H["pp_BNP__ntprobnp"].to_numpy(float) if "pp_BNP__ntprobnp" in T.H else np.full(N, np.nan)
    base = dict(trial=n, key=V.KEY[n], rb=T.rb, rs=T.rs)
    rows, log = [], {}
    # S1
    r = dict(base, step="S1", variant="engine", n=N, n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=np.nan)
    m = T.y_ok
    r["loghr"], r["se"] = cox(T.y_t[m], T.y_e[m], t[m])
    r.update(diagnostics(T.ph, T.ecg_pc, lvef, bnp, t, np.arange(N), np.ones(N), perm))
    rows.append(r)
    X = {"S2": T.X_dx, "S3": np.hstack([T.X_dx, T.hd(200)]), "S4": T.X_core}
    for s, Xs in X.items():
        lg = ps_logit(np.asarray(Xs, float), t)
        s_idx, cl, s_w = match(lg, t, cal=0.2, ratio=1)
        mm = T.y_ok[s_idx]
        b, se = cox(T.y_t[s_idx][mm], T.y_e[s_idx][mm], t[s_idx][mm], cluster=cl[mm])
        r = dict(base, step=s, variant="engine", n=len(s_idx), n_t=int(t[s_idx].sum()), n_c=int((1 - t[s_idx]).sum()),
                 n_pairs=int(len(np.unique(cl))), loghr=b, se=se)
        r.update(diagnostics(T.ph, T.ecg_pc, lvef, bnp, t, s_idx, s_w, perm))
        rows.append(r)
    # S0 (where built): S0 diagnostics and S1 recomputed on the S0 data sources (S0 heads / S0 PCs / S0 panel)
    if (s0dir(n) / "READY").exists():
        S = s0_data(n)
        k0 = S["keys"]
        t0_ = S["t"]
        n0 = len(k0)
        p0 = np.random.default_rng(190_002).permutation(n0)
        r = dict(base, step="S0", variant="s0data", n=n0, n_t=int(t0_.sum()), n_c=int((1 - t0_).sum()), n_pairs=np.nan)
        r.update(diagnostics(S["ph"], S["pc"], S["lvef"], S["bnp"], t0_, np.arange(n0), np.ones(n0), p0))
        rows.append(r)
        pos = pd.Index(k0).get_indexer(T.keys)
        ok = pos >= 0
        log["s1_in_s0_frac"] = float(ok.mean())
        log["s1_treated_agree"] = float((t0_[pos[ok]] == t[ok]).mean())
        # same person, same arm and same index date (switch_seq designs re-sample, so S1 is not nested in S0)
        same = ok.copy()
        same[ok] = (t0_[pos[ok]] == t[ok]) & (S["idx"][pos[ok]] == T.index_date.to_numpy()[ok])
        log["s1_same_record_in_s0_frac"] = float(same.mean())
        ok = same
        sub = pos[ok]
        # audits: same patients -> same ECG embedding and near-identical phenotype scores
        log["emb_maxabs_dev_s1_vs_s0"] = float(np.nanmax(np.abs(S["raw"][sub] - T.ecg_raw[ok])))
        log["ph_corr_s1heads_vs_s0heads"] = [float(np.corrcoef(S["ph"][sub, j], T.ph[ok, j])[0, 1]) for j in range(len(PH))]
        lv1 = lvef[ok]
        lv0 = S["lvef"][sub]
        both = ~np.isnan(lv1) & ~np.isnan(lv0)
        log["lvef_agree_frac"] = float(np.mean(np.isclose(lv1[both], lv0[both]))) if both.any() else np.nan
        # S1 on S0 data (S0-trained phenotype heads, PCs of S0 embeddings), rows = S1 patients present in S0
        tt = t0_[sub]
        ph1, pc1 = S["ph"][sub], S["pc"][sub]
        r = dict(base, step="S1", variant="s0data", n=len(sub), n_t=int(tt.sum()), n_c=int((1 - tt).sum()), n_pairs=np.nan)
        r.update(diagnostics(ph1, pc1, S["lvef"][sub], S["bnp"][sub], tt, np.arange(len(sub)), np.ones(len(sub)),
                             np.random.default_rng(190_003).permutation(len(sub))))
        rows.append(r)
    log["secs"] = round(time.time() - t0, 1)
    return rows, {n: log}


def suppress(D):
    D = D.copy()
    for c in ("n", "n_t", "n_c", "n_pairs") + tuple(c for c in D.columns if c.startswith("nmeas_")):
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            D.loc[(v >= 1) & (v < MIN_CELL), c] = np.nan
    return D


def cmd_run(a):
    import v18_af_confirm as AF
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(mode=0o700, exist_ok=True)
    trials = a.trials.split(",") if a.trials else list(AF.V.ALL)
    trials = [x for x in trials if x != "comet"] if a.skip_comet else trials
    with Pool(min(a.workers, len(trials))) as p:
        res = p.map(trial_task, trials, chunksize=1)
    R = pd.DataFrame([r for rr, _ in res for r in rr])
    lg = {}
    for _, g in res:
        lg.update(g)
    tag = f"_{a.tag}" if a.tag else ""
    suppress(R).to_csv(OUT / f"steps{tag}.csv", index=False)
    (OUT / f"log{tag}.json").write_text(json.dumps(lg, indent=1))
    print("done", len(R), flush=True)


# ================================================================ summaries
def load_steps():
    R = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("steps*.csv"))], ignore_index=True)
    R = R.drop_duplicates(["trial", "step", "variant"], keep="last")
    R["absd"] = (R.loghr - R.rb).abs()
    return R


def spearman_cluster_perm(x, y, g, nperm=20000, seed=0):
    """Spearman rho of x vs y over (trial x step) points; null: y's trial blocks permuted across trials of equal
    block size (cluster-robust permutation by trial). Also within-trial (centred) version."""
    from scipy.stats import rankdata, spearmanr
    x, y, g = np.asarray(x, float), np.asarray(y, float), np.asarray(g)
    ok = ~np.isnan(x) & ~np.isnan(y)
    x, y, g = x[ok], y[ok], g[ok]
    if len(x) < 6:
        return dict(rho=np.nan, p=np.nan, n_pts=len(x), n_trials=len(set(g)), rho_within=np.nan, p_within=np.nan)
    rho = spearmanr(x, y)[0]
    rng = np.random.default_rng(seed)
    ug = pd.unique(g)
    blocks = {k: np.where(g == k)[0] for k in ug}
    size = {k: len(v) for k, v in blocks.items()}
    bysize = {}
    for k in ug:
        bysize.setdefault(size[k], []).append(k)
    null = np.empty(nperm)
    rx = rankdata(x)
    for b in range(nperm):
        yp = np.empty_like(y)
        for s, ks in bysize.items():
            perm = rng.permutation(len(ks))
            for k, kk in zip(ks, np.array(ks, dtype=object)[perm]):
                yp[blocks[k]] = y[blocks[kk]]
        null[b] = np.corrcoef(rx, rankdata(yp))[0, 1]
    p = float((np.sum(np.abs(null) >= abs(rho) - 1e-12) + 1) / (nperm + 1))
    if max(size.values()) == 1:
        return dict(rho=float(rho), p=p, n_pts=int(len(x)), n_trials=int(len(ug)), rho_within=np.nan, p_within=np.nan)
    # within-trial: ranks centred within trial; null = within-trial permutation of y
    xc = pd.Series(rankdata(x)).groupby(g).transform(lambda s: s - s.mean()).to_numpy()
    yc = pd.Series(rankdata(y)).groupby(g).transform(lambda s: s - s.mean()).to_numpy()
    rw = float(np.corrcoef(xc, yc)[0, 1]) if xc.std() > 0 and yc.std() > 0 else np.nan
    nw = np.empty(nperm)
    ry = rankdata(y)
    for b in range(nperm):
        yp = ry.copy()
        for k in ug:
            ii = blocks[k]
            yp[ii] = ry[ii][rng.permutation(len(ii))]
        ypc = pd.Series(yp).groupby(g).transform(lambda s: s - s.mean()).to_numpy()
        nw[b] = np.corrcoef(xc, ypc)[0, 1]
    pw = float((np.sum(np.abs(nw) >= abs(rw) - 1e-12) + 1) / (nperm + 1)) if np.isfinite(rw) else np.nan
    return dict(rho=float(rho), p=p, n_pts=int(len(x)), n_trials=int(len(ug)), rho_within=rw, p_within=pw)


def cmd_summarize(a):
    from v13_summarize import sign_flip
    os.umask(0o077)
    R = load_steps()
    E1 = R[R.variant == "engine"]
    MET = ["ph_mean", "ph3_mean", "ecg_c", "shuf_c", "smd_lvef", "smd_bnp", "smd_logbnp"] + [f"smd:{c}" for c in PH]
    # (a) step means
    agg = []
    for (var, s), g in R.groupby(["variant", "step"]):
        d = dict(variant=var, step=s, n_trials=g.trial.nunique())
        for m in MET + ["absd"]:
            d[m] = g[m].mean()
            d[f"{m}_median"] = g[m].median()
        agg.append(d)
    AG = pd.DataFrame(agg)
    AG.to_csv(OUT / "step_means.csv", index=False)
    # (b) paired sign-flip between steps (a - b; > 0 = imbalance lower at the later step)
    pairs = [("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S1", "S3"), ("S1", "S4"), ("S2", "S4")]
    tests = []
    W = E1.pivot(index="trial", columns="step")
    for m in ["ph_mean", "ph3_mean", "ecg_c", "shuf_c", "smd_lvef", "smd_logbnp", "smd_bnp", "absd"]:
        for x, y in pairs:
            d = (W[(m, x)] - W[(m, y)]).dropna().to_numpy()
            o, p = sign_flip(d) if len(d) else (np.nan, np.nan)
            tests.append(dict(set="38 trials (engine)", metric=m, a=x, b=y, n_trials=len(d), mean_a_minus_b=o,
                              k_decline=f"{int((d > 0).sum())}/{len(d)}", p_signflip=p))
    S0d = R[R.variant == "s0data"].pivot(index="trial", columns="step")
    if len(S0d):
        for m in ["ph_mean", "ph3_mean", "ecg_c", "shuf_c", "smd_lvef", "smd_logbnp", "smd_bnp"]:
            d = (S0d[(m, "S0")] - S0d[(m, "S1")]).dropna().to_numpy()
            o, p = sign_flip(d) if len(d) else (np.nan, np.nan)
            tests.append(dict(set="S0 trials (S0 data)", metric=m, a="S0", b="S1", n_trials=len(d), mean_a_minus_b=o,
                              k_decline=f"{int((d > 0).sum())}/{len(d)}", p_signflip=p))
        # trials with the same drug contrast share one S0 cohort (identical n, n_t): average d within a shared S0
        s0 = R[(R.variant == "s0data") & (R.step == "S0")].set_index("trial")
        grp = s0.n.astype(str) + "_" + s0.n_t.astype(str)
        for m in ["ph_mean", "ph3_mean", "ecg_c", "shuf_c", "smd_lvef", "smd_logbnp", "smd_bnp"]:
            dd = (S0d[(m, "S0")] - S0d[(m, "S1")]).groupby(grp.reindex(S0d.index)).mean().dropna().to_numpy()
            o, p = sign_flip(dd) if len(dd) else (np.nan, np.nan)
            tests.append(dict(set="S0 cohorts (shared S0 averaged)", metric=m, a="S0", b="S1", n_trials=len(dd),
                              mean_a_minus_b=o, k_decline=f"{int((dd > 0).sum())}/{len(dd)}", p_signflip=p))
        # nested only: trials whose S1 records are >= 99% contained in S0 (excludes switch_seq re-sampling designs)
        lg = json.load(open(OUT / "log.json"))
        nest = [t for t in S0d.index if lg.get(t, {}).get("s1_same_record_in_s0_frac", 0) >= 0.99]
        for m in ["ph_mean", "ecg_c", "smd_lvef", "smd_logbnp"]:
            d = (S0d.loc[nest, (m, "S0")] - S0d.loc[nest, (m, "S1")]).dropna().to_numpy()
            o, p = sign_flip(d)
            tests.append(dict(set="S0 trials, S1 nested in S0 (>=99%)", metric=m, a="S0", b="S1", n_trials=len(d),
                              mean_a_minus_b=o, k_decline=f"{int((d > 0).sum())}/{len(d)}", p_signflip=p))
    # monotone trend per trial (Spearman of metric vs step 1..4) -> sign-flip of per-trial slopes
    from scipy.stats import spearmanr
    for m in ["ph_mean", "ecg_c", "smd_lvef", "smd_logbnp"]:
        sl = []
        for n, g in E1.groupby("trial"):
            g = g.set_index("step").reindex(["S1", "S2", "S3", "S4"])[m]
            if g.notna().sum() >= 3:
                sl.append(spearmanr(np.arange(4)[g.notna().to_numpy()], g.dropna())[0])
        sl = -np.array(sl, float)
        sl = sl[~np.isnan(sl)]
        o, p = sign_flip(sl)
        tests.append(dict(set="38 trials (engine)", metric=m, a="trend", b="S1..S4 (-Spearman)", n_trials=len(sl),
                          mean_a_minus_b=o, k_decline=f"{int((sl > 0).sum())}/{len(sl)}", p_signflip=p))
    TS = pd.DataFrame(tests)
    TS.to_csv(OUT / "step_tests.csv", index=False)
    # (c) correlations across trials x matched steps S2-S4
    M = E1[E1.step.isin(["S2", "S3", "S4"])]
    cors = []
    for xm in ["ph_mean", "ph3_mean", "ecg_c"]:
        for ym in ["absd", "smd_lvef", "smd_logbnp", "smd_bnp"]:
            c = spearman_cluster_perm(M[xm], M[ym], M.trial, nperm=a.nperm)
            cors.append(dict(x=xm, y=ym, **c))
    for xm, ym in (("smd_lvef", "absd"), ("smd_logbnp", "absd"), ("shuf_c", "absd")):
        c = spearman_cluster_perm(M[xm], M[ym], M.trial, nperm=a.nperm)
        cors.append(dict(x=xm, y=ym, **c))
    M23 = E1[E1.step.isin(["S2", "S3"])]  # LVEF is in the clinical PS (T.core 'lvef'): not held out at S4
    for xm in ["ph_mean", "ecg_c"]:
        for ym in ["smd_lvef", "absd"]:
            c = spearman_cluster_perm(M23[xm], M23[ym], M23.trial, nperm=a.nperm)
            cors.append(dict(x=xm, y=ym, step="S2-S3", **c))
    for s in ("S1", "S2", "S3", "S4"):  # one point per trial (plain permutation = block permutation, block size 1)
        Ms = E1[E1.step == s]
        for xm, ym in (("ph_mean", "absd"), ("ecg_c", "absd"), ("ph_mean", "smd_lvef"), ("ph_mean", "smd_logbnp"),
                       ("ecg_c", "smd_lvef"), ("ecg_c", "smd_logbnp")):
            c = spearman_cluster_perm(Ms[xm], Ms[ym], Ms.trial, nperm=a.nperm)
            cors.append(dict(x=xm, y=ym, step=s, **{k: v for k, v in c.items() if not k.endswith("within")}))
    CR = pd.DataFrame(cors)
    CR["step"] = CR.get("step", pd.Series(index=CR.index, dtype=object)).fillna("S2-S4")
    CR.to_csv(OUT / "correlations.csv", index=False)
    per = R.copy()
    per.to_csv(OUT / "per_trial_steps.csv", index=False)
    figure(R)
    from v13_summarize import md
    L = ["## step means (mean over trials)\n", md(AG[["variant", "step", "n_trials", "ph_mean", "ph3_mean", "ecg_c", "shuf_c", "smd_lvef",
                                                     "smd_logbnp", "smd_bnp", "absd"]], 3),
         "\n## per-phenotype |SMD| means\n", md(AG[["variant", "step"] + [f"smd:{c}" for c in PH]], 3),
         "\n## step tests (two-sided sign-flip, v13_summarize.sign_flip; > 0 = lower imbalance at b)\n", md(TS, 4),
         "\n## correlations (Spearman; p = cluster (trial-block) permutation)\n", md(CR, 3)]
    S0t = R[R.trial.isin(R[R.step == "S0"].trial)].sort_values(["trial", "variant", "step"])
    L += ["\n## trials with S0: every step\n", md(S0t[["trial", "variant", "step", "n", "n_t", "n_c", "ph_mean", "ph3_mean", "ecg_c", "shuf_c",
                                                     "smd_lvef", "smd_logbnp", "absd"]], 3)]
    per = E1.pivot(index="trial", columns="step", values="ph_mean").join(
        E1.pivot(index="trial", columns="step", values="ecg_c"), lsuffix="_ph", rsuffix="_c").join(
        E1.pivot(index="trial", columns="step", values="absd").add_suffix("_absd")).reset_index()
    L += ["\n## per trial (engine): ph_mean, ecg_c and |Δlog HR| by step\n", md(per, 3)]
    (OUT / "tables.md").write_text("\n".join(L) + "\n")
    print(AG.to_string())
    print(TS.to_string())
    print(CR.to_string())


def figure(R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    DOCS.mkdir(parents=True, exist_ok=True)
    mets = [("ph_mean", "mean |SMD|, 5 AI-ECG phenotypes"), ("ecg_c", "ECG-PC C-statistic for treatment"),
            ("smd_lvef", "|SMD| echo LVEF (held out)"), ("smd_logbnp", "|SMD| log NT-proBNP (held out)")]
    panels = [t for t in FOCUS if t in set(R.trial)] + ["pooled"]
    fig, ax = plt.subplots(len(mets), len(panels), figsize=(3.1 * len(panels), 2.5 * len(mets)), sharey="row")
    col_ecg, col_s0 = "#1f5fa8", "#9aa6b2"
    for j, p in enumerate(panels):
        for i, (m, lab) in enumerate(mets):
            A_ = ax[i, j]
            if p == "pooled":
                E1 = R[R.variant == "engine"].groupby("step")[m]
                mu, se = E1.mean(), E1.std() / np.sqrt(E1.count())
                xs = [STEPS.index(s) for s in mu.index]
                A_.errorbar(xs, mu.to_numpy(), yerr=1.96 * se.to_numpy(), color=col_ecg, marker="o", capsize=2, lw=1.5,
                            label=f"all trials (n={R[R.variant == 'engine'].trial.nunique()})")
                s0 = R[R.variant == "s0data"]
                if len(s0):
                    g = s0.groupby("step")[m].mean()
                    A_.plot([STEPS.index(s) for s in g.index], g.to_numpy(), color=col_s0, marker="s", ls="--", lw=1.2,
                            label=f"S0 trials, S0 data (n={s0.trial.nunique()})")
                if i == 0:
                    A_.legend(fontsize=6.5, frameon=False)
            else:
                g = R[(R.trial == p) & (R.variant == "engine")].set_index("step")[m]
                A_.plot([STEPS.index(s) for s in g.index], g.to_numpy(), color=col_ecg, marker="o", lw=1.5)
                g0 = R[(R.trial == p) & (R.variant == "s0data")].set_index("step")[m]
                if len(g0):
                    A_.plot([STEPS.index(s) for s in g0.index], g0.to_numpy(), color=col_s0, marker="s", ls="--", lw=1.2)
            if m == "ecg_c":
                A_.axhline(0.5, color="#666", lw=0.7, ls=":")
            else:
                A_.axhline(0.1, color="#666", lw=0.7, ls=":")
            A_.set_xticks(range(5))
            A_.set_xticklabels(STEPS if i == len(mets) - 1 else [], fontsize=8)
            A_.tick_params(labelsize=7)
            A_.spines[["top", "right"]].set_visible(False)
            if j == 0:
                A_.set_ylabel(lab, fontsize=7.5)
            if i == 0:
                A_.set_title(p.upper() if p != "pooled" else "pooled (mean ± 95% CI)", fontsize=9)
    fig.suptitle("G1: ECG imbalance across design steps (S0 ungated initiators, S1 trial cohort, S2 sparse PS, S3 hdPS200, "
                 "S4 clinical PS)\nsolid = engine trial cohort data; dashed grey = S0-build data (S0-trained phenotype heads, "
                 "PCs of S0 embeddings)", fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(DOCS / "G1_design_steps.png", dpi=150)
    os.chmod(DOCS / "G1_design_steps.png", 0o644)


def cmd_queue(a):
    """S0 builds for many trials: at most len(gpus) concurrent, each started only on a GPU idle at that moment."""
    os.umask(0o077)
    gpus = [int(g) for g in a.gpus.split(",")]
    todo = [n for n in a.trials.split(",") if not (s0dir(n) / "READY").exists()]
    run = {}
    log = OUT / "queue.log"
    while todo or run:
        for g, (n, p) in list(run.items()):
            if p.poll() is not None:
                open(log, "a").write(f"{time.strftime('%H:%M:%S')} {n} exit {p.returncode}\n")
                del run[g]
        for g in gpus:
            if todo and g not in run and gpu_idle(g):
                n = todo.pop(0)
                p = subprocess.Popen([PY, str(HERE / "g1_design_steps.py"), "build", "--trial", n, "--gpu", str(g), "--reuse"],
                                     stdout=open(OUT / f"build_{n}.log", "w"), stderr=subprocess.STDOUT, cwd=str(HERE))
                run[g] = (n, p)
                open(log, "a").write(f"{time.strftime('%H:%M:%S')} {n} start GPU {g}\n")
        time.sleep(30)
    open(log, "a").write(f"{time.strftime('%H:%M:%S')} QUEUE DONE\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cohort")
    c.add_argument("--trial", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--threads", type=int, default=8)
    b = sub.add_parser("build")
    b.add_argument("--trial", required=True)
    b.add_argument("--gpu", type=int, required=True)
    b.add_argument("--reuse", action="store_true", help="copy already-embedded ECGs (same checkpoint) instead of re-embedding")
    r = sub.add_parser("run")
    r.add_argument("--trials", default="")
    r.add_argument("--workers", type=int, default=12)
    r.add_argument("--tag", default="")
    r.add_argument("--skip-comet", action="store_true")
    s = sub.add_parser("summarize")
    s.add_argument("--nperm", type=int, default=20000)
    q = sub.add_parser("queue")
    q.add_argument("--trials", required=True)
    q.add_argument("--gpus", required=True)
    a = ap.parse_args()
    {"cohort": cmd_cohort, "build": cmd_build, "run": cmd_run, "summarize": cmd_summarize, "queue": cmd_queue}[a.cmd](a)


if __name__ == "__main__":
    main()
