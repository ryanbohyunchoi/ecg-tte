#!/usr/bin/env python
"""v1.8 Plan B (docs/v17/V18_PLANS.md, fixed before results): the v1.7 analyses with CLMBR-T (code-only EHR
foundation-model embedding, 64 PCs = v13_common.Trial.clm_pc) instead of / in addition to the ECG (32 BCL PCs).
Exploratory; every cell is reported. Aggregates only; OUT has umask 077.

Code path = scripts/v17/v17_confirm.py (imported, unchanged): trial list ALL (E.TRIALS 18 + v13_common.V17 15),
halves s1_ladder.halves(T, i) (seed 16060 + i), E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1)), PS L2 C=1,
matched-sample capture S8._LAST, covars2b panel V.xpanel / PS-overlap exclusion as V.task.
PS designs:  P1 = T.demo (v1.7 P1);  P5 = demo + hypertension_v11, t2d, cad_ihd + atrial_fibrillation + HF
             (= scripts/v17/s11_p5.py);  P2 = P5 + obesity (= v1.7 P2).  nan_to_num on the P5/P2 base (V.designs).
Arms per PS (columns appended to the base design in this order):
  base | CLMBR (+T.clm_pc) | ECG (+T.ecg_pc) | CLMBR+ECG | shufCLMBR (+T.clm_pc[T.shuffle_perm]) |
  noise64 (+N(0,1) 64 dims, np.random.default_rng(NOISE64_SEED0 + i), i = trial index in ALL, drawn for all rows)
  and, as placebos for the ECG-involving contrasts: shufECG (+T.ecg_pc[T.shuffle_perm]) | noise32 (+T.noise32) |
  CLMBR+shufECG | ECG+shufCLMBR;  plus unmatched once per half.
Balance endpoints:
  (i)  lt01      % of the 58-panel variables with |SMD| < 0.1 (E.VARS)
  (ii) nc_lt01   same, NON-CODED physiology subset = 58-panel groups Vitals & core labs, Other labs, Echo:* (group
                 "Coded record" excluded)  -> PRIMARY balance endpoint for CLMBR comparisons
  (iii) lv_lt01  covars2b non-proximal panel (V.xpanel + per-PS exclusions as v1.7), restricted to dictionary domain
                 lab_vital (all code-derived domains comorbidity/elixhauser/charlson/medication/utilisation/
                 device_procedure/preventive/score and calendar/social dropped); lvv_lt01 = lab_vital values only
                 (measurement-presence indicators *_missing and n_bp_readings_365 dropped; sensitivity).
  x_lt01 = the v1.7 full covars2b non-proximal panel (reproduction only).
Emulation endpoints: |Δlog HR| vs RCT (absd), z² (Δ²/(se²+se_RCT²)), consistency (|z| < 1.96).

Usage:
  v18_clmbr.py leakage [--workers 12]   STEP 0: CLMBR input leakage facts -> OUT/leakage.csv (aggregates, suppressed)
  v18_clmbr.py run [--trials a,b] [--workers 24] [--tag all]  -> OUT/results_<tag>.csv, OUT/log_<tag>.json
  v18_clmbr.py verify [--tag all]       base/ECG/shufECG/noise32/unmatched rows vs claude-v17-confirm results_all (P1,P2)
                                        and results_p5 (P5) -> OUT/verify_<tag>.csv, max deviation
  v18_clmbr.py summarize                -> OUT/summary.csv, OUT/per_category.csv, OUT/per_trial.csv, OUT/tables.md
  v18_clmbr.py tables                   -> OUT/tables.md (markdown, aggregates)
  v18_clmbr.py figure                   -> docs/v18/CLMBR_vs_ECG.png
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v17"))
sys.path.insert(0, str(HERE.parent / "v16"))
sys.path.insert(0, str(HERE.parent))
import v17_confirm as V  # noqa: E402  (imports v16_engine, s6_balance, s8_headline with the matched-sample capture)
from s1_ladder import halves  # noqa: E402

E, S6, S8 = V.E, V.S6, V.S8
A = V.A
OUT = A / "claude-v18-clmbr"
DOCS = HERE.parent.parent / "docs" / "v18"
ALL, OLD, NEW, KEY = V.ALL, V.OLD, V.NEW, V.KEY
NOISE64_SEED0 = 640_000
PSS = ["P1", "P5", "P2"]
P5DX = ["hypertension_v11", "t2d", "cad_ihd"]
P2DX = ["hypertension_v11", "t2d", "cad_ihd", "obesity"]
ARMS = ["base", "CLMBR", "ECG", "CLMBR+ECG", "shufCLMBR", "noise64", "shufECG", "noise32", "CLMBR+shufECG", "ECG+shufCLMBR"]
NONCODED = [c for c, _, g in E.VARS if g != "Coded record"]
CATEGORY = {**{t: "AF" for t in ("aristotle", "rocket-af", "rely", "east-afnet4", "cabana-v2", "affirm", "af-chf")},
            **{t: "HF" for t in ("comet", "paradigm-hf-seq", "transform-hf", "elite-ii", "emperor-preserved-v2")},
            **{t: "DM" for t in ("empa-reg", "carolina", "leader", "sustain6", "rewind", "declare", "canvas", "tecos", "carmelina")},
            **{t: "HTN" for t in ("life", "allhat", "value", "ascot", "insight")},
            **{t: "ACS/post-MI" for t in ("plato", "valiant")},
            **{t: "Other" for t in ("ontarget", "precision", "amplify", "lodestar", "prove-it")}}
MIN_CELL = 11
# leakage sensitivity sets, fixed in docs/v18/CLMBR_LEAKAGE.md before any result
EXCL_NOOWN = ["paradigm-hf-seq", "east-afnet4", "affirm", "af-chf", "sustain6", "insight"]
EXCL_NOEXPO = ["transform-hf", "aristotle", "rocket-af", "rely", "east-afnet4", "sustain6", "insight", "affirm", "af-chf", "amplify"]


def meds_dirs(n):
    if n == "comet":
        return A.parent / "shared/comet-meds-v1-3hgAkgoB/meds", A / "comet-clmbr-full-NAyb4G2x/report"
    return A.parent / f"shared/claude-{n}-meds-v2/meds", A / f"claude-{n}-clmbr-codeonly/report"


def sup(k):
    k = int(k)
    return k if (k == 0 or k >= MIN_CELL) else f"<{MIN_CELL}"


def pct(k, n):
    return round(100.0 * k / n, 2) if (k == 0 or k >= MIN_CELL) else f"<{MIN_CELL} pts"


# ================================================================ STEP 0: leakage
def _keys(n):
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    C = T.clm_pc
    return n, list(T.keys), bool(np.isfinite(C).all()), C.shape, len(T.t)


def leakage(workers):
    import duckdb
    from build_shared_tables import digest
    from trial_common import rp
    from trial_specs import TRIALS as SPECS
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    G = "/mnt/raid0/rbc58/omop/gold"
    vocab = set(Path(os.environ.get("CLMBR_VOCAB", "")).read_text().split("\n")) if os.environ.get("CLMBR_VOCAB") else None
    if vocab is None:
        import subprocess
        mos = "/mnt/raid0/rbc58/ecg-tte/software/mosaic-env"
        code = ("import msgpack,sys;d=msgpack.load(open('/mnt/raid0/eo287/clmbr/dictionary.msgpack','rb'));"
                "sys.stdout.write('\\n'.join(sorted({x['code_string'] for x in d['vocab'] if x['type']=='code'})))")
        vocab = set(subprocess.run([f"{mos}/bin/python", "-c", code], capture_output=True, text=True, check=True).stdout.split("\n"))
    con = duckdb.connect()
    con.execute("SET threads=16")
    # exposure concept sets: ingredient concepts of drug orders whose '-'-split source value contains an arm keyword
    # (the cohort builder's token rule), kept only if the concept name contains an arm keyword (removes combination-row
    # cross-mapping, e.g. 'metoprolol-hydrochlorothiazide' -> metoprolol concept for a thiazide keyword)
    D = con.execute(f"SELECT DISTINCT drug_concept_id cid, lower(drug_source_value) s FROM {rp(G, 'drug_exposure')} "
                    "WHERE drug_source_value IS NOT NULL AND drug_concept_id > 0").df()
    D["tok"] = D.s.str.split("-")
    D = D.explode("tok")
    CN = con.execute("SELECT concept_id cid, lower(concept_name) nm, vocabulary_id v, concept_code c FROM read_csv("
                     "'/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv', delim='\t', quote='', header=true, all_varchar=true) "
                     "WHERE domain_id IN ('Drug', 'Procedure')").df()
    CN["cid"] = CN.cid.astype("int64")
    CN = CN.set_index("cid")
    P = con.execute(f"SELECT DISTINCT procedure_concept_id cid, upper(procedure_source_value) s FROM {rp(G, 'procedure_occurrence')} "
                    "WHERE procedure_source_value IS NOT NULL AND procedure_concept_id > 0").df()

    def arm_cids(spec_arm, is_proc):
        name, kws = spec_arm
        if is_proc:
            c = set(P[P.s.apply(lambda s: any(s.startswith(k.upper()) for k in kws))].cid)
        else:
            kl = [k.lower() for k in kws]
            c = set(D[D.tok.isin(kl)].cid)
            c = {x for x in c if x in CN.index and any(k in CN.loc[x, "nm"] for k in kl)}
        return c

    with Pool(min(workers, 12)) as p:
        KK = {n: (keys, fin, shp, nn) for n, keys, fin, shp, nn in p.map(_keys, ALL, chunksize=1)}
    rows = []
    for n in ALL:
        keys, fin, shp, nn = KK[n]
        spec = SPECS[KEY[n]]
        mroot, croot = meds_dirs(n)
        man = json.loads((croot / "manifest.json").read_text())
        lineage_ok = digest(mroot / "manifest.json") == man["meds_manifest_sha256"]
        summ = json.loads((croot / "summary.json").read_text())
        ro = pd.read_parquet(mroot / "restricted_cohort.parquet")
        st = pd.read_parquet(croot / "restricted_patient_status.parquet")
        enc = set(st[st.status == "encoded"].patient_key)
        ro = ro[ro.patient_key.isin(set(keys))].copy()
        arms = [a for a, _ in spec["arms"]]
        ro["arm_idx"] = ro.treatment_arm.map({a: i for i, a in enumerate(arms)})
        coh = pd.read_parquet(A / {**V.PRIMARY, **V.EXTRA}[n][1] / "restricted_cohort.parquet").set_index("patient_key")
        same_index = bool((pd.to_datetime(coh.index_date.reindex(ro.patient_key)).dt.date.to_numpy()
                           == pd.to_datetime(ro.index_date).dt.date.to_numpy()).all())
        ro["idx"] = pd.to_datetime(ro.index_date)
        ro = ro[["subject_id", "arm_idx", "idx"]]
        con.register("ro", ro)
        glob = f"{mroot}/data/*.parquet"
        tim = con.execute(f"""SELECT count(*) FILTER (WHERE m.time >= r.idx) n_at_or_after_index,
              count(*) n_events, count(DISTINCT m.subject_id) FILTER (WHERE CAST(m.time AS DATE) = CAST(r.idx AS DATE) - 1) n_pat_lastday,
              max(m.time - r.idx) max_offset
            FROM read_parquet('{glob}') m JOIN ro r USING (subject_id) WHERE m.source_domain <> 'birth'""").fetchone()
        is_proc = [spec.get("design") == "procedure" or (spec.get("design") == "proc_vs_drug" and i == 0) for i in range(len(arms))]
        ex = []
        for i, sa in enumerate(spec["arms"]):
            dom = "procedure_occurrence" if is_proc[i] else "drug_exposure"
            for c in arm_cids(sa, is_proc[i]):
                code = f"{CN.loc[c, 'v']}/{CN.loc[c, 'c']}" if c in CN.index else ""
                ex.append((i, dom, c, code in vocab))
        prior = []
        if spec.get("prior_class"):
            pc_ = arm_cids(("prior", spec["prior_class"]), False)
            prior = [(9, "drug_exposure", c, f"{CN.loc[c, 'v']}/{CN.loc[c, 'c']}" in vocab) for c in pc_]
        X = pd.DataFrame(ex + prior, columns=["arm_e", "dom", "cid", "in_vocab"])
        con.register("ex", X)
        H = con.execute(f"""SELECT m.subject_id, e.arm_e, bool_or(e.in_vocab) any_vocab,
              min(date_diff('day', CAST(m.time AS DATE), CAST(r.idx AS DATE))) min_days
            FROM read_parquet('{glob}') m JOIN ro r USING (subject_id)
            JOIN ex e ON e.dom = m.source_domain AND e.cid = CAST(m.source_concept_id AS BIGINT)
            GROUP BY 1, 2""").df().merge(ro[["subject_id", "arm_idx"]], on="subject_id")
        N = len(ro)
        own = H[H.arm_e == H.arm_idx]
        oth = H[(H.arm_e != H.arm_idx) & (H.arm_e != 9)]
        anyx = H[H.arm_e != 9]

        def cnt(df, extra=None):
            d = df if extra is None else df[extra(df)]
            return d.subject_id.nunique()
        r = dict(trial=n, key=KEY[n], design=spec.get("design") or "new_user", n_analysed=N, n_keys_trial=nn,
                 clmbr_encoded_pct=round(100 * len(set(keys) & enc) / len(keys), 2), clm_pc_shape=f"{shp[0]}x{shp[1]}",
                 clm_pc_finite=fin, meds_lineage_ok=lineage_ok, clmbr_numeric_mode=summ.get("numeric_mode"),
                 max_tokens=summ.get("max_tokens"), index_date_matches_cohort=same_index,
                 events_at_or_after_index=sup(tim[0]), max_event_offset_vs_index_midnight=str(tim[3]),
                 pct_pat_last_event_on_index_minus1=pct(tim[2], N),
                 n_exposure_concepts=int((X.arm_e != 9).sum()), n_exposure_concepts_in_vocab=int(X[X.arm_e != 9].in_vocab.sum()),
                 pct_any_exposure_token=pct(cnt(anyx), N), pct_any_exposure_token_vocab=pct(cnt(anyx, lambda d: d.any_vocab), N),
                 pct_any_exposure_token_365d=pct(cnt(anyx, lambda d: d.min_days <= 365), N),
                 pct_own_arm_token=pct(cnt(own), N), pct_own_arm_token_vocab=pct(cnt(own, lambda d: d.any_vocab), N),
                 pct_own_arm_token_30d=pct(cnt(own, lambda d: d.min_days <= 30), N),
                 pct_own_arm_token_index_minus1=pct(cnt(own, lambda d: d.min_days <= 1), N),
                 pct_other_arm_token=pct(cnt(oth), N), pct_other_arm_token_vocab=pct(cnt(oth, lambda d: d.any_vocab), N),
                 pct_other_arm_token_365d=pct(cnt(oth, lambda d: d.min_days <= 365), N),
                 pct_prior_class_token_365d=pct(H[(H.arm_e == 9) & (H.min_days <= 365)].subject_id.nunique(), N) if prior else "")
        rows.append(r)
        print(n, flush=True)
    L = pd.DataFrame(rows)
    L.to_csv(OUT / "leakage.csv", index=False)
    pd.set_option("display.width", 250)
    print(L.T.to_string())


# ================================================================ STEP 1: run
def designs(T, n, dx):
    """= v17_confirm.designs with the dx list as a parameter (P5: P5DX, P2: P2DX)."""
    d1, d2 = V.cdirs(n)
    C1 = pd.read_parquet(d1 / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    C2 = pd.read_parquet(d2 / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    miss = [c for c in dx if c not in C1]
    if miss:
        raise RuntimeError(f"{n}: covars v1 columns missing {miss}")
    hf = "hf_any_365" if "hf_any_365" in C2 else "elx_chf"
    base = np.column_stack([T.cov[T.demo].to_numpy(float), C1[dx].to_numpy(float),
                            T.cov["atrial_fibrillation"].to_numpy(float), C2[hf].to_numpy(float)])
    return np.nan_to_num(base), list(T.demo) + dx + ["atrial_fibrillation", hf], hf


def task(args):
    n, half = args
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    b5, psn5, hf = designs(T, n, P5DX)
    b2, psn2, _ = designs(T, n, P2DX)
    Xe, ovl = V.xpanel(T, V.cdirs(n)[1])
    dom = pd.read_csv(V.cdirs(n)[1] / "dictionary.csv").set_index("variable").domain
    r = halves(T, i)[half]
    t = T.t[r]
    cov = T.cov.iloc[r]
    X1 = cov[T.demo].to_numpy(float)
    CL = T.clm_pc
    assert CL.shape == (len(T.t), 64) and np.isfinite(CL).all()
    nz64 = np.random.default_rng(NOISE64_SEED0 + i).normal(size=(len(T.t), 64))
    blk = {"clm": CL[r], "shc": CL[T.shuffle_perm][r], "nz64": nz64[r], "ecg": T.ecg_pc[r], "she": T.ecg_pc[T.shuffle_perm][r],
           "nz32": T.noise32[r]}
    comp = {"base": [], "CLMBR": ["clm"], "ECG": ["ecg"], "CLMBR+ECG": ["clm", "ecg"], "shufCLMBR": ["shc"], "noise64": ["nz64"],
            "shufECG": ["she"], "noise32": ["nz32"], "CLMBR+shufECG": ["clm", "she"], "ECG+shufCLMBR": ["ecg", "shc"]}
    P = {"P1": (X1, list(T.demo)), "P5": (b5[r], psn5), "P2": (b2[r], psn2)}
    out = []

    def xv(psn):
        drop = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)}
        U = Xe.drop(columns=sorted(drop)).iloc[r]
        U = U.loc[:, U.notna().sum() > 0]
        U = U.loc[:, U.nunique() > 1]
        lv = [c for c in U.columns if dom.get(c, "") == "lab_vital"]
        lvv = [c for c in lv if not c.endswith("_missing") and c not in ("n_bp_readings_365", "weight_change_missing")]
        return U.to_numpy(float), U[lv].to_numpy(float), U[lvv].to_numpy(float), len(drop)

    def pref(d, p):
        return {k.replace("x_", p + "_", 1): v for k, v in d.items()}

    def rec(ps, role, X, XV, nd):
        S8._LAST.clear()
        o = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1))
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if X is None else S8._LAST["m"]
        XA, XL, XLV = XV
        out.append(dict(trial=n, key=KEY[n], set="new15" if n in NEW else "old18", category=CATEGORY[n], idx=i, half=half, ps=ps,
                        arm_role=role, rb=T.rb, rs=T.rs, x_ndrop=nd, **o, **V.xsmd(XA, t, s_idx, s_w),
                        **pref(V.xsmd(XL, t, s_idx, s_w), "lv"), **pref(V.xsmd(XLV, t, s_idx, s_w), "lvv")))

    *XV0, nd0 = xv([])
    rec("none", "unmatched", None, XV0, nd0)
    for ps, (X, psn) in P.items():
        *XV, nd = xv(psn)
        for role in ARMS:
            rec(ps, role, np.hstack([X] + [blk[b] for b in comp[role]]), XV, nd)
    log = dict(trial=n, half=half, idx=i, seed_halves=16060 + i, seed_noise64=NOISE64_SEED0 + i, hf_column=hf,
               x_ncols_panel=int(Xe.shape[1]), n_lab_vital_cols=int(sum(dom.get(c, "") == "lab_vital" for c in Xe.columns)),
               secs=round(time.time() - t0, 1))
    print(f"{n} {half} {time.time() - t0:.0f}s", flush=True)
    return out, log


def run(trials, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in trials:
        if n in NEW and not (A / f"claude-v17-trials/{n}.READY").exists():
            raise RuntimeError(f"{n} not READY")
    tk = [(n, h) for n in trials for h in ("full", "A", "B")]
    tk.sort(key=lambda x: (x[0] not in ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare"), x[1] != "full"))
    with Pool(min(workers, len(tk), 24)) as p:
        res = p.map(task, tk, chunksize=1)
    pd.DataFrame([x for o, _ in res for x in o]).to_csv(OUT / f"results_{tag}.csv", index=False)
    (OUT / f"log_{tag}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    print("done", tag, flush=True)


def verify(tag):
    R = pd.read_csv(OUT / f"results_{tag}.csv")
    ref = {"P1": (pd.read_csv(V.OUT / "results_all.csv"), "P1"), "P2": (pd.read_csv(V.OUT / "results_all.csv"), "P2"),
           "P5": (pd.read_csv(V.OUT / "results_p5.csv"), "P2")}
    cols = ["loghr", "se", "n_pairs", "mean_smd", "cstat", "x_pct_lt10", "x_mean", "x_nvars"] + [f"smd:{c}" for c, _, _ in E.VARS]
    rows = []
    for ps, (Rf, lab) in ref.items():
        for role in ("unmatched", "base", "ECG", "shufECG", "noise"):
            mine = "noise32" if role == "noise" else role
            a = R[(R.ps == ("none" if role == "unmatched" else ps)) & (R.arm_role == mine)].set_index(["trial", "half"])
            b = Rf[(Rf.ps == ("none" if role == "unmatched" else lab)) & (Rf.arm_role == role)].set_index(["trial", "half"])
            ix = a.index.intersection(b.index)
            for c in cols:
                x, y = a.loc[ix, c].to_numpy(float), b.loc[ix, c].to_numpy(float)
                bad = int((np.isnan(x) ^ np.isnan(y)).sum())
                d = np.nanmax(np.abs(x - y)) if np.isfinite(x - y).any() else 0.0
                rows.append(dict(ps=ps, arm=role, col=c, n_rows=len(ix), n_rows_ref=len(b), maxdev=float(d), nan_mismatch=bad))
    Vv = pd.DataFrame(rows)
    Vv.to_csv(OUT / f"verify_{tag}.csv", index=False)
    print(Vv.groupby(["ps", "arm"]).agg(n=("n_rows", "max"), nref=("n_rows_ref", "max"), maxdev=("maxdev", "max"),
                                         nan_mismatch=("nan_mismatch", "sum")).to_string())
    print("overall max deviation", Vv.maxdev.max(), "nan mismatches", Vv.nan_mismatch.sum())


# ================================================================ STEP 2: summaries
HIGHER = {"lt01", "nc_lt01", "lv_lt01", "lvv_lt01", "x_lt01", "cons"}
METRICS = ["nc_lt01", "lt01", "lv_lt01", "lvv_lt01", "nc_mean", "absd", "z2", "cons"]
CONTRASTS = [  # (a, b, sidedness): positive d = a better; one-sided H1 a better unless "two"
    ("CLMBR", "base", "one"), ("ECG", "base", "one"), ("CLMBR+ECG", "base", "one"),
    ("CLMBR", "ECG", "two"), ("CLMBR+ECG", "CLMBR", "one"), ("CLMBR+ECG", "ECG", "one"),
    ("shufCLMBR", "base", "one"), ("noise64", "base", "one"), ("shufECG", "base", "one"), ("noise32", "base", "one"),
    ("CLMBR", "shufCLMBR", "one"), ("CLMBR", "noise64", "one"), ("ECG", "shufECG", "one"), ("ECG", "noise32", "one"),
    ("CLMBR+ECG", "CLMBR+shufECG", "one"), ("CLMBR+ECG", "ECG+shufCLMBR", "one")]


def trial_metrics(g):
    sm = g[[f"smd:{c}" for c, _, _ in E.VARS]].abs()
    nc = g[[f"smd:{c}" for c in NONCODED]].abs()
    z = (g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)
    return pd.DataFrame({"lt01": (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy(),
                         "nc_lt01": (100 * (nc < 0.1).sum(1) / nc.notna().sum(1)).to_numpy(), "nc_mean": nc.mean(1).to_numpy(),
                         "lv_lt01": g.lv_pct_lt10.to_numpy(), "lvv_lt01": g.lvv_pct_lt10.to_numpy(), "x_lt01": g.x_pct_lt10.to_numpy(),
                         "absd": (g.loghr - g.rb).abs().to_numpy(), "z2": (z ** 2).to_numpy(), "cons": (100.0 * (z.abs() < 1.96)).to_numpy(),
                         "loghr": g.loghr.to_numpy(), "se": g.se.to_numpy(), "rb": g.rb.to_numpy(), "rs": g.rs.to_numpy(),
                         "n_pairs": g.n_pairs.to_numpy()}, index=g.trial.to_numpy())


def p2s(d):
    return min(1.0, 2 * min(V.signflip_1s(d), V.signflip_1s(-np.asarray(d, float))))


def analyse(M, trials, BENCH, nperm=10000, seed=0, halves_=True, loo=True, cluster=True):
    """Paired contrasts across `trials`. Benchmark shuffle (absd, z2): per draw, the analysed trials receive RCT
    benchmarks (log HR, SE) drawn without replacement from all 33 RCTs (BENCH); p = P(null <= observed)."""
    CLm = V.cluster_of()
    out = []
    rb_all, rs_all = BENCH
    for ps in PSS:
        F = {r: M["full"][ps][r].loc[trials] for r in ARMS}
        for a, b, side in CONTRASTS:
            for m in METRICS:
                sgn = 1 if m in HIGHER else -1
                d = sgn * (F[a][m] - F[b][m])
                pf = V.signflip_1s if side == "one" else p2s
                row = dict(ps=ps, contrast=f"{a} vs {b}", sided=side, metric=m, n=len(trials), mean_a=F[a][m].mean(),
                           mean_b=F[b][m].mean(), diff_a_minus_b=(F[a][m] - F[b][m]).mean(),
                           k_a_better=f"{int((d > 0).sum())}/{int(d.notna().sum())}", p=pf(d.to_numpy()))
                if cluster:
                    cl = pd.Series(d.to_numpy(), index=[CLm[KEY[t]] for t in trials]).groupby(level=0).mean()
                    row.update(n_clusters=len(cl), cluster_p=pf(cl.to_numpy()))
                if loo and len(trials) > 2:
                    row["loo_max_p"] = max(pf(d.drop(t).to_numpy()) for t in trials)
                if halves_:
                    for h in ("A", "B"):
                        row[f"p_{h}"] = pf((sgn * (M[h][ps][a].loc[trials][m] - M[h][ps][b].loc[trials][m])).to_numpy())
                if m in ("absd", "z2"):
                    la, sa, lb, sb = F[a].loghr.to_numpy(), F[a].se.to_numpy(), F[b].loghr.to_numpy(), F[b].se.to_numpy()

                    def st(q, v):
                        if m == "absd":
                            return (np.abs(la - q) - np.abs(lb - q)).mean()
                        return ((la - q) ** 2 / (sa ** 2 + v ** 2) - (lb - q) ** 2 / (sb ** 2 + v ** 2)).mean()
                    obs = st(F[a].rb.to_numpy(), F[a].rs.to_numpy())
                    rng = np.random.default_rng(seed)
                    k = len(trials)
                    null = np.empty(nperm)
                    for j in range(nperm):
                        ix = rng.permutation(len(rb_all))[:k]
                        null[j] = st(rb_all[ix], rs_all[ix])
                    row.update(bshuf_obs=obs, bshuf_null_mean=null.mean(),
                               bshuf_p=float((null <= obs + 1e-12).mean()) if side == "one" else
                               float(min(1.0, 2 * min((null <= obs + 1e-12).mean(), (null >= obs - 1e-12).mean()))))
                out.append(row)
    return out


def load_M():
    R = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("results_*.csv"))], ignore_index=True)
    R = R.drop_duplicates(["trial", "half", "ps", "arm_role"], keep="last")
    R = R[R.arm_role != "unmatched"]
    M = {h: {ps: {r: trial_metrics(R[(R.half == h) & (R.ps == ps) & (R.arm_role == r)]) for r in ARMS} for ps in PSS}
         for h in ("full", "A", "B")}
    return R, M


def summarize():
    R, M = load_M()
    F0 = M["full"]["P1"]["base"].loc[ALL]
    BENCH = (F0.rb.to_numpy(), F0.rs.to_numpy())
    rows = [dict(scope="all33", **r) for r in analyse(M, ALL, BENCH)]
    rows += [dict(scope="old18", **r) for r in analyse(M, OLD, BENCH, loo=False)]
    rows += [dict(scope="new15", **r) for r in analyse(M, NEW, BENCH, loo=False)]
    rows += [dict(scope="S_noown", **r) for r in analyse(M, [t for t in ALL if t not in EXCL_NOOWN], BENCH, loo=False)]
    rows += [dict(scope="S_noexpo", **r) for r in analyse(M, [t for t in ALL if t not in EXCL_NOEXPO], BENCH, loo=False)]
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary.csv", index=False)
    cr = []
    for cat in ("AF", "HF", "DM", "HTN", "ACS/post-MI", "Other"):
        tr = [t for t in ALL if CATEGORY[t] == cat]
        cr += [dict(category=cat, **r) for r in analyse(M, tr, BENCH, halves_=False, loo=False, cluster=False)]
    C = pd.DataFrame(cr)
    C.to_csv(OUT / "per_category.csv", index=False)
    pt = []
    for n in ALL:
        rec = dict(trial=n, category=CATEGORY[n], set="new15" if n in NEW else "old18", rct_hr=float(np.exp(M["full"]["P1"]["base"].loc[n, "rb"])))
        for ps in PSS:
            for r in ("base", "CLMBR", "ECG", "CLMBR+ECG", "shufCLMBR", "noise64"):
                f = M["full"][ps][r].loc[n]
                rec.update({f"{ps}|{r}|hr": np.exp(f.loghr), f"{ps}|{r}|absd": f.absd, f"{ps}|{r}|nc_lt01": f.nc_lt01,
                            f"{ps}|{r}|lt01": f.lt01, f"{ps}|{r}|lv_lt01": f.lv_lt01, f"{ps}|{r}|n_pairs": f.n_pairs})
        pt.append(rec)
    P = pd.DataFrame(pt)
    P.to_csv(OUT / "per_trial.csv", index=False)
    print("written", len(S), len(C), len(P))


def tables():
    """markdown tables (aggregates) -> OUT/tables.md; pasted into docs/v18/CLMBR_RESULTS.md."""
    from v13_summarize import md
    S = pd.read_csv(OUT / "summary.csv")
    C = pd.read_csv(OUT / "per_category.csv")
    P = pd.read_csv(OUT / "per_trial.csv")
    L = []
    cols = ["ps", "contrast", "mean_a", "mean_b", "diff_a_minus_b", "k_a_better", "p", "cluster_p", "loo_max_p", "p_A", "p_B"]
    lab = {"nc_lt01": "(ii) NON-CODED physiology subset of the 58-panel, % |SMD| < 0.1 (PRIMARY balance endpoint)",
           "lt01": "(i) full 58-panel, % |SMD| < 0.1", "lv_lt01": "(iii) covars2b non-proximal lab/vital panel, % |SMD| < 0.1",
           "lvv_lt01": "(iii-b) covars2b lab/vital values only (no measurement-presence indicators), % |SMD| < 0.1",
           "nc_mean": "non-coded subset, mean |SMD| (lower = better)", "absd": "|Δlog HR| vs RCT (lower = better)",
           "z2": "z² vs RCT (lower = better)", "cons": "% consistent with RCT (|z| < 1.96)"}
    for scope, title in (("all33", "All 33 trials"), ("old18", "v1.6 18 trials"), ("new15", "v1.7 15 trials"),
                         ("S_noown", "Leakage sensitivity S_noown (27 trials)"), ("S_noexpo", "Leakage sensitivity S_noexpo (23 trials)")):
        L.append(f"\n### {title}\n")
        for m in (METRICS if scope == "all33" else ["nc_lt01", "lv_lt01", "absd", "z2"]):
            q = S[(S.scope == scope) & (S.metric == m)]
            c = cols + (["bshuf_p"] if m in ("absd", "z2") else [])
            c = [x for x in c if x in q and q[x].notna().any()]
            L.append(f"\n**{lab[m]}**\n\n" + md(q[c].rename(columns={"diff_a_minus_b": "a−b", "k_a_better": "a better"}), 3))
    L.append("\n### Per category (full cohort; one-sided exact sign-flip; benchmark shuffle from all 33 RCTs)\n")
    K = ["CLMBR vs base", "ECG vs base", "CLMBR+ECG vs base", "CLMBR vs ECG", "CLMBR+ECG vs CLMBR", "CLMBR+ECG vs ECG",
         "CLMBR vs shufCLMBR", "ECG vs shufECG"]
    for m in ("nc_lt01", "absd"):
        q = C[(C.metric == m) & C.contrast.isin(K)]
        c = ["ps", "category", "contrast", "n", "mean_a", "mean_b", "diff_a_minus_b", "k_a_better", "p"] + (["bshuf_p"] if m == "absd" else [])
        L.append(f"\n**{lab[m]}**\n\n" + md(q[c].rename(columns={"diff_a_minus_b": "a−b", "k_a_better": "a better"}), 3))
    L.append("\n### Per trial (full cohort): non-coded % |SMD| < 0.1 and |Δlog HR| vs RCT\n")
    for ps in PSS:
        rows = []
        for _, r in P.iterrows():
            d = dict(trial=r.trial, category=r.category, rct_hr=r.rct_hr)
            for a in ("base", "CLMBR", "ECG", "CLMBR+ECG", "shufCLMBR"):
                d[f"nc {a}"] = r[f"{ps}|{a}|nc_lt01"]
            for a in ("base", "CLMBR", "ECG", "CLMBR+ECG"):
                d[f"HR {a}"] = r[f"{ps}|{a}|hr"]
            for a in ("base", "CLMBR", "ECG", "CLMBR+ECG"):
                d[f"gap {a}"] = r[f"{ps}|{a}|absd"]
            rows.append(d)
        L.append(f"\n**{ps}**\n\n" + md(pd.DataFrame(rows), 2))
    (OUT / "tables.md").write_text("\n".join(L) + "\n")
    print("tables written")


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S = pd.read_csv(OUT / "summary.csv")
    S = S[S.scope == "all33"]
    arms = [("CLMBR", "CLMBR-T 64", "#2a78d6"), ("ECG", "ECG 32", "#eb6834"), ("CLMBR+ECG", "CLMBR + ECG", "#4a3aa7"),
            ("shufCLMBR", "shuffled CLMBR", "#8d8c88"), ("noise64", "noise 64", "#b5b4af"),
            ("shufECG", "shuffled ECG", "#8d8c88"), ("noise32", "noise 32", "#b5b4af")]
    mets = [("nc_lt01", "Balance gain vs base\n(pp of non-coded physiology vars |SMD|<0.1)"),
            ("absd", "Change in |Δlog HR| vs RCT\n(negative = closer to RCT)")]
    plt.rcParams.update({"font.size": 8.5, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(2, 3, figsize=(13, 7.2), sharey="row")
    for j, ps in enumerate(PSS):
        for i, (m, lab) in enumerate(mets):
            a = ax[i, j]
            vals, ps_, cols = [], [], []
            for r, nm, c in arms:
                q = S[(S.ps == ps) & (S.metric == m) & (S.contrast == f"{r} vs base")].iloc[0]
                vals.append(q.diff_a_minus_b)
                ps_.append((q.p, q.bshuf_p) if m == "absd" else (q.p,))
                cols.append(c)
            y = np.arange(len(arms))[::-1]
            a.barh(y, vals, color=cols, height=0.7)
            a.axvline(0, color="#333", lw=0.8)
            span = max(abs(v) for v in vals) or 1
            fp = lambda p: f"={p:.3f}" if p >= 0.001 else "<0.001"
            for yy, v, p in zip(y, vals, ps_):
                if len(p) == 1:
                    a.text(v + (0.03 * span if v >= 0 else -0.03 * span), yy, f"p{fp(p[0])}", va="center",
                           ha="left" if v >= 0 else "right", fontsize=7.5, color="#333")
                else:  # gap row: labels right of max(v, 0) so they never cross the bars or tick labels
                    a.text(max(v, 0) + 0.04 * span, yy, f"sign-flip p{fp(p[0])}\nshuffle p{fp(p[1])}", va="center",
                           ha="left", fontsize=7, color="#333", linespacing=1.1)
            a.set_xlim((-1.45 * span, 1.45 * span) if i == 0 else (-1.15 * span, 1.35 * span))
            a.set_yticks(y)
            a.set_yticklabels([nm for _, nm, _ in arms])
            if i == 0:
                a.set_title({"P1": "P1: demographics", "P5": "P5: demo + 5 dx", "P2": "P2: demo + 6 dx"}[ps], fontsize=10)
            if j == 0:
                a.set_ylabel(lab)
    fig.text(0.5, 0.005, "33 trials, 1:1 caliper-0.2 PS matching, full cohort. Balance p: one-sided exact sign-flip; "
             "gap: sign-flip p and benchmark-shuffle p (RCT HRs drawn from all 33, 10,000 draws; tests trial-specificity).", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    DOCS.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS / "CLMBR_vs_ECG.png", dpi=160)
    print("figure written")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["leakage", "run", "verify", "summarize", "tables", "figure"])
    ap.add_argument("--trials", default=",".join(ALL))
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--tag", default="all")
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "leakage":
        leakage(a.workers)
    elif a.cmd == "run":
        run(a.trials.split(","), a.workers, a.tag)
    elif a.cmd == "verify":
        verify(a.tag)
    elif a.cmd == "summarize":
        summarize()
    elif a.cmd == "tables":
        tables()
    else:
        figure()


if __name__ == "__main__":
    main()
