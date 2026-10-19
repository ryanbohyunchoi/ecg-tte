#!/usr/bin/env python
"""CHS CLMBR-T transfer (EXPLORATORY, post hoc; docs/bdc/CHS_EHR_EXPLORATORY.md, part B).

Three steps on BDC:
  timeline  (BDC analysis python, PYTHONPATH=pylib) CHS dbGaP tables + chs_emulations + the code map (chs_clmbr_map.json,
            made locally by chs_clmbr_map.py and uploaded by the user) -> restricted MEDS-like pseudo-timelines
            chs_clmbr_events.parquet (one subject per emulation x person; exposure flags of that emulation removed) and
            chs_clmbr_queries.parquet (emulation row -> subject, cutoff). Aggregate coverage: chs_clmbr/timeline.json.
  download  (clmbr env) StanfordShahLab/clmbr-t-base at the Yale revision, with the user's own Hugging Face login;
            files are checked against the Yale copy's SHA-256 (the exact weights used at Yale and in MIMIC-IV).
  encode    (clmbr env) frozen CLMBR-T, code-only, femr 0.2.3 / meds 0.1.3, as scripts/mimic/encode_mimic_clmbr.py:
            torch seed 20260923, the latest token representation before the cutoff (768-d raw). One forward pass per
            subject; because the transformer is causal, the representation at the last token before each row's cutoff
            equals encoding that row's truncated timeline (checked on a sample: --verify). Output (restricted):
            chs_clmbr.parquet (row, c0..c767); aggregate chs_clmbr/encode.json. Runs on CPU (no GPU needed).

Timeline per person (pseudo-calendar: CHS has study days only; entry = 1989-06-15 for the original cohort and
1992-12-15 for the new cohort, birth = entry - (AGEBL + 0.5) years; no sex or race token, as at Yale):
  - entry history (day 0): prior MI, angina, HF, stroke, hypertension, diabetes, AF -> one SNOMED code each
  - adjudicated incident events (MI, angina, angioplasty, bypass, HF, stroke, AF) at their study day
  - each annual clinic visit: Visit/OP + the medication-class flags recorded there -> RxNorm clinical drugs (crude)
  - each hospital admission (ICD9 table): Visit/IP + ICD-9-CM codes -> SNOMED (Maps to) + ICD9Proc codes in vocabulary
Cutoff for an emulation row = end of the visit k-1 study day (events on or before the k-1 day; held-out items, PS
covariates and the ECG are also from visit k-1). Lab and vital codes are not written (protocol measurements, done on
everyone; values are held out). Exposure drugs of each emulation (chs_cohort.EXPOSURE_FLAGS) are removed from that
emulation's timelines, as for PS-Codes.

Usage:
  python scripts/bdc/chs_clmbr.py timeline --map /sbgenomics/workspace/chs_clmbr_map.json [--skip CYST_C_YR5]
  env -u PYTHONPATH $ENV/bin/python scripts/bdc/chs_clmbr.py download --model-root /sbgenomics/workspace/clmbr-t-base
  env -u PYTHONPATH $ENV/bin/python scripts/bdc/chs_clmbr.py encode --model-root /sbgenomics/workspace/clmbr-t-base
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

REPO = "StanfordShahLab/clmbr-t-base"
REVISION = "5504b35aabd41a9615efed4231356a918114ae6a"  # the Yale copy (/mnt/raid0/eo287/clmbr, git HEAD)
MODEL_SHA256 = {"config.json": "9c8b9835ed5628a9b6d9498577a93ac4d9e6e269beecfbd69ca3b5dcab915e2a",
                "dictionary.msgpack": "481ddac70a37e79bbfadde1411ad674544a161e3c1948149989cd159a34203ee",
                "model.safetensors": "f56e2ece082b9daf87767c7de93419db1b6c0eaf21311e06c8f329b7ab4b81a2"}
MAP_VERSIONS = ("chs_clmbr_map_v1", "chs_clmbr_map_v2")
# chronic ICD-9-CM categories re-emitted at every later clinic visit with --rich (problem-list style, as an EHR re-codes
# ongoing conditions at each encounter): cardiometabolic, renal, lung, neuro, cancer history, and status V-codes
CHRONIC = re.compile(r"^(250|27[0-2]|274|278|244|24[0-6]|40[1-5]|41[0-4]|42[4-8]|39[3-8]|43[3-8]|44[0-3]|49[0-6]|58[5-6]|71[4-6]|73[3]|33[1-2]|29[0-4]|296|311|30[3-5]|34[05]|365|366|57[1-2]|600|1[4-9]\d|20[0-8]|V10|V12|V15|V42|V43|V45|V58)")
ENTRY = {2: dt.datetime(1989, 6, 15), 5: dt.datetime(1992, 12, 15)}
SEED = 20260923
DIM = 768


def rdir() -> Path:
    p = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    os.umask(0o077)
    p.mkdir(parents=True, exist_ok=True)
    return p


def out_dir() -> Path:
    import bdc_common as BC
    o = BC.out_root() / "chs_clmbr"
    o.mkdir(parents=True, exist_ok=True)
    return o


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sup(n) -> object:
    n = int(n)
    return "1-10" if 1 <= n <= 10 else n


# ---------------------------------------------------------------- timeline
def icd9cm_dotted(c: str) -> str:
    c = c.strip().upper().replace(".", "")
    head = 4 if c.startswith("E") else 3
    return c[:head] + ("." + c[head:] if len(c) > head else "")


def map_dx(c: str, M: dict) -> list:
    d = icd9cm_dotted(c)
    while d:
        if d in M:
            return M[d]
        d = d[:-1].rstrip(".") if len(d) > 3 else ""
    return []


def map_px(c: str, P: set, rules: dict | None = None) -> list:
    """Exact in-vocabulary ICD9Proc code, else the longest curated category rule (map v2), else a truncated
    in-vocabulary ICD9Proc code."""
    c = c.strip().replace(".", "")
    if len(c) < 2:
        return []
    full = c[:2] + ("." + c[2:] if len(c) > 2 else "")
    if full in P:
        return ["ICD9Proc/" + full]
    for k in range(len(c), 1, -1):
        if rules and c[:k] in rules:
            return list(rules[c[:k]])
    for k in (3, 2):
        d = c[:2] + ("." + c[2:k] if k > 2 else "")
        if d in P:
            return ["ICD9Proc/" + d]
    return []


def is_chronic(c: str) -> bool:
    return bool(CHRONIC.match(c.strip().upper().replace(".", "")))


def person_events(T, CH, CC, Mp: dict, L: pd.DataFrame, entry: dict, rich: bool = False) -> tuple:
    """Long (id, day, order, code, flag) events for every person (before emulation-specific exclusions) and per-person
    calendar anchors. order: 0 history, 1 clinic visit, 2 medication, 3 admission, 4 admission codes.
    rich: ongoing conditions (entry history, adjudicated events, chronic hospital diagnoses) are repeated at every later
    clinic visit (no new information; a denser, EHR-like rendering of the same history)."""
    key = CH.key
    ev = []
    # clinic visits and medication flags
    day = L[L.item == "day"][["id", "visit", "value"]].rename(columns={"value": "day"})
    ev.append(pd.DataFrame({"id": day.id, "day": day.day, "order": 1, "code": Mp["visit"].get("clinic"), "flag": "",
                            "chronic": False}))
    med = {f.upper(): c for f, c in Mp["med"].items()}
    for t, D in T.items():
        if t not in CH.TABLE_VISIT or not len(D) or t == "CYST_C_YR5":
            continue
        flags = [c for c in D.columns if str(c).upper() in med and med[str(c).upper()]]
        if not flags:
            continue
        on = D[flags].apply(pd.to_numeric, errors="coerce").eq(1)
        on.insert(0, "id", key(D).to_numpy())
        lg = on.melt(id_vars="id", var_name="flag", value_name="on")
        lg = lg[lg.on].assign(visit=CH.TABLE_VISIT[t]).merge(day, on=["id", "visit"])
        lg["flag"] = lg.flag.str.upper()
        for f, g in lg.groupby("flag"):
            for c in med[f]:
                ev.append(pd.DataFrame({"id": g.id, "day": g.day, "order": 2, "code": c, "flag": f, "chronic": False}))
    # hospital admissions
    H = T.get("ICD9", pd.DataFrame())
    stats = dict(dx_codes=0, dx_mapped=0, px_codes=0, px_mapped=0, admissions=0)
    unmapped = {"dx": pd.Series(dtype=int), "px": pd.Series(dtype=int)}
    if len(H):
        hid = key(H)
        ad = pd.to_numeric(H.get("ADDAYS58"), errors="coerce")
        P, rules = set(Mp["icd9proc"]), Mp.get("icd9proc_rules", {})
        ok = ad.notna()
        stats["admissions"] = int(ok.sum())
        ev.append(pd.DataFrame({"id": hid[ok], "day": ad[ok], "order": 3, "code": Mp["visit"].get("admission"), "flag": "",
                                "chronic": False}))
        for i in range(1, 11):
            for col, fn, kind in ((f"DCODE{i}", lambda c: map_dx(c, Mp["icd9cm"]), "dx"),
                                  (f"PCODE{i}", lambda c: map_px(c, P, rules), "px")):
                if col not in H:
                    continue
                v = H[col].astype(str).str.strip()
                use = ok & ~v.isin(["nan", "", ".", "None"])
                codes = v[use].map(fn)
                stats[f"{kind}_codes"] += int(use.sum())
                stats[f"{kind}_mapped"] += int(codes.map(bool).sum())
                cat = v[use][~codes.map(bool)].str.replace(".", "", regex=False).str[:3]
                unmapped[kind] = unmapped[kind].add(cat.value_counts(), fill_value=0)
                chron = v[use].map(is_chronic) if kind == "dx" else pd.Series(False, index=v[use].index)
                x = pd.DataFrame({"id": hid[use], "day": ad[use], "codes": codes, "chronic": chron}).explode("codes").dropna(subset=["codes"])
                ev.append(pd.DataFrame({"id": x.id, "day": x.day, "order": 4, "code": x.codes, "flag": "",
                                        "chronic": x.chronic.astype(bool)}))
    # entry history and adjudicated incident events
    hx = Mp["history"]
    ES, BB, AF = T.get("EVENT_SUMMARY", pd.DataFrame()), T.get("BASEBOTH", pd.DataFrame()), T.get("CARE_AFIB", pd.DataFrame())

    def add(D, cond, when, name):
        if name in hx and len(D):
            for c in hx[name]:
                ev.append(pd.DataFrame({"id": key(D)[cond], "day": when[cond], "order": 0, "code": c, "flag": "",
                                        "chronic": True}))

    num = lambda D, c: pd.to_numeric(D[c], errors="coerce") if c in D else pd.Series(np.nan, index=D.index)  # noqa: E731
    if len(ES):
        zero = pd.Series(0.0, index=ES.index)
        for prev, name in (("MIBLMOD", "MI"), ("ANBLMOD", "ANGINA"), ("CHBLMOD", "HF"), ("STBLMOD", "STROKE")):
            add(ES, num(ES, prev) == 1, zero, name)
        for inc, tto, name in (("INCMI", "TTOMI", "MI"), ("INCANG", "TTOANG", "ANGINA"), ("INCANGIO", "TTOANGI", "ANGIOPLASTY"),
                               ("INCBYPS", "TTOBYPS", "BYPASS"), ("INCCHF", "TTOCHF", "HF"), ("INCSTRK", "TTOSTK", "STROKE")):
            add(ES, (num(ES, inc) == 1) & num(ES, tto).notna(), num(ES, tto), name)
    if len(BB):
        zero = pd.Series(0.0, index=BB.index)
        add(BB, num(BB, "BPHI") == 1, zero, "HTN")
        add(BB, num(BB, "DIABADA").isin([3, 4]), zero, "DIABETES")
    if len(AF):
        zero = pd.Series(0.0, index=AF.index)
        add(AF, num(AF, "PREVALENT") == 1, zero, "AF")
        add(AF, (num(AF, "INCAFIB") == 1) & num(AF, "TTOAFIB").notna(), num(AF, "TTOAFIB"), "AF")
    E = pd.concat(ev, ignore_index=True).dropna(subset=["code", "day"])
    E["id"] = E.id.astype(str)
    E = E.drop_duplicates(["id", "day", "code"])
    if rich:  # repeat ongoing conditions at every later clinic visit
        pr = E[E.chronic][["id", "day", "code"]].drop_duplicates(["id", "code"], keep="first")
        vi = E[(E.order == 1)][["id", "day"]].rename(columns={"day": "vday"}).drop_duplicates()
        cf = pr.merge(vi, on="id")
        cf = cf[cf.day < cf.vday]
        stats["carried_forward_events"] = int(len(cf))
        E = pd.concat([E, pd.DataFrame({"id": cf.id, "day": cf.vday, "order": 1, "code": cf.code, "flag": "",
                                        "chronic": False})], ignore_index=True).drop_duplicates(["id", "day", "code"])
    for kind in ("dx", "px"):  # aggregate: most frequent unmapped categories (counts >= 11 only)
        u = unmapped[kind].sort_values(ascending=False)
        stats[f"top_unmapped_{kind}"] = {k: int(n) for k, n in u[u >= 11].head(30).items()}
    # calendar anchors
    age = pd.Series(dtype=float)
    if len(BB):
        age = pd.Series(num(BB, "AGEBL").to_numpy(), index=key(BB).astype(str)).groupby(level=0).first()
    anchors = pd.DataFrame({"entry_visit": pd.Series(entry)}).rename_axis("id").reset_index()
    anchors["id"] = anchors.id.astype(str)
    anchors["AGEBL"] = anchors.id.map(age)
    return E, anchors, stats


def cmd_timeline(a) -> None:
    import bdc_common as BC
    import cohort_count as CC
    import chs_cohort as CH
    Mp = json.loads(Path(a.map).read_text())
    if Mp.get("version") not in MAP_VERSIONS:
        raise SystemExit(f"code map version {Mp.get('version')} not in {MAP_VERSIONS}")
    if a.rich and Mp["version"] == "chs_clmbr_map_v1":
        BC.log("note: --rich with map v1 (no curated procedure rules)")
    t0 = time.time()
    rd = rdir()
    R = None
    for suf in (".parquet", ".pkl"):
        p = rd / ("chs_emulations" + suf)
        if p.exists():
            R = pd.read_parquet(p) if suf == ".parquet" else pd.read_pickle(p)
            break
    if R is None:
        raise SystemExit("missing chs_emulations (run chs_cohort.py first)")
    CH.SKIP.clear()
    CH.SKIP.update(a.skip)
    BC.log("indexing project files ...")
    files = CC.index(Path(a.root))
    T, _U, _seen = CH.load(files)
    L, entry = CH.long_measures(T)
    BC.log("tables read; building timelines ...")
    E, anchors, stats = person_events(T, CH, CC, Mp, L, entry, rich=a.rich)
    anchors = anchors.dropna(subset=["AGEBL"])
    anc = anchors.set_index("id")
    R = R.copy()
    R["id"] = R.id.astype(str)
    n_rows_in = len(R)
    R = R[R.id.isin(anc.index) & R.day_k1.notna()]
    subjects = R[["EMU", "id"]].drop_duplicates().reset_index(drop=True)
    subjects["subject_id"] = np.arange(len(subjects), dtype=np.int64)
    R = R.merge(subjects, on=["EMU", "id"])
    last = R.groupby("subject_id").day_k1.max()
    ent = anc.entry_visit.map(lambda v: ENTRY.get(int(v), ENTRY[2]))
    birth = ent - pd.to_timedelta((anc.AGEBL + 0.5) * 365.25, unit="D")
    parts = []
    for emu, S in subjects.groupby("EMU"):
        rx = re.compile(CH.EXPOSURE_FLAGS.get(emu, r"$^"))
        e = E[E.id.isin(set(S.id))]
        e = e[~e.flag.str.fullmatch(rx.pattern)]
        e = e.merge(S[["id", "subject_id"]], on="id")
        e = e[e.day <= e.subject_id.map(last)]
        parts.append(e)
    X = pd.concat(parts, ignore_index=True)
    X["time"] = X.id.map(ent) + pd.to_timedelta(X.day, unit="D") + pd.to_timedelta(8 + X.order, unit="h")
    X = X[X.time > X.id.map(birth)]
    B = pd.DataFrame({"subject_id": subjects.subject_id, "time": subjects.id.map(birth).to_numpy(), "code": "MEDS_BIRTH"})
    X = pd.concat([B, X[["subject_id", "time", "code"]]], ignore_index=True).sort_values(["subject_id", "time", "code"])
    X["time"] = X.time.dt.floor("s")
    Q = pd.DataFrame({"row": R.row.to_numpy(), "subject_id": R.subject_id.to_numpy(),
                      "cutoff": (R.id.map(ent) + pd.to_timedelta(R.day_k1 + 1, unit="D")).to_numpy()})
    tag = f"_{a.tag}" if a.tag else ""
    X.to_parquet(rd / f"chs_clmbr{tag}_events.parquet", index=False)
    Q.to_parquet(rd / f"chs_clmbr{tag}_queries.parquet", index=False)
    n_ev = X[X.code != "MEDS_BIRTH"].merge(Q, on="subject_id")
    n_ev = n_ev[n_ev.time < n_ev.cutoff].groupby("row").size().reindex(Q.row, fill_value=0)
    info = dict(when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), map_sha256=sha(Path(a.map)),
                map_version=Mp["version"], tag=a.tag, rich=a.rich,
                subjects=sup(len(subjects)), rows=sup(len(Q)), rows_dropped_no_age_or_day=sup(n_rows_in - len(Q)),
                persons_without_AGEBL=sup(len(entry) - len(anchors)),
                events_per_row_p5_p50_p95=[float(x) for x in np.percentile(n_ev, [5, 50, 95])], coverage=stats,
                dx_mapped_share=round(stats["dx_mapped"] / max(stats["dx_codes"], 1), 3),
                px_mapped_share=round(stats["px_mapped"] / max(stats["px_codes"], 1), 3),
                seconds=round(time.time() - t0))
    o = out_dir()
    (o / f"timeline{tag}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))
    BC.log(f"restricted: {rd}/chs_clmbr{tag}_events.parquet, chs_clmbr{tag}_queries.parquet (stay in BDC)")


# ---------------------------------------------------------------- model download
def cmd_download(a) -> None:
    from huggingface_hub import snapshot_download
    root = Path(a.model_root)
    snapshot_download(REPO, revision=a.revision, local_dir=str(root),
                      allow_patterns=list(MODEL_SHA256) + ["LICENSE", "README.md"])
    bad = {n: sha(root / n) for n in MODEL_SHA256 if sha(root / n) != MODEL_SHA256[n]}
    print(json.dumps(dict(model_root=str(root), revision=a.revision, sha256_ok=not bad, mismatch=list(bad)), indent=1))
    if bad and not a.allow_other:
        raise SystemExit("model files differ from the Yale copy (use --allow-other to proceed, and record it)")


# ---------------------------------------------------------------- encode
def import_femr():
    shim = os.environ.get("CHS_CLMBR_FORCE_SHIM") == "1"  # tests: use the shim even where real xformers exists
    if not shim:
        try:
            import xformers.ops  # noqa: F401
        except ImportError:
            shim = True
    if shim:
        sys.path.insert(0, str(HERE / "xformers_shim"))
        import xformers.ops  # noqa: F401
    import meds
    import torch
    from femr.models.config import FEMRModelConfig
    from femr.models.processor import FEMRBatchProcessor
    from femr.models.tokenizer import FEMRTokenizer
    from femr.models.transformer import FEMRModel
    return shim, meds, torch, FEMRModelConfig, FEMRBatchProcessor, FEMRTokenizer, FEMRModel


def load_exact(model, path):
    from safetensors.torch import load_file
    state = load_file(str(path), device="cpu")
    exp = model.state_dict()
    if set(state) != set(exp) or any(state[k].shape != v.shape or state[k].dtype != v.dtype for k, v in exp.items()):
        raise SystemExit("checkpoint keys/shapes/dtypes do not match the femr model")
    model.load_state_dict(state, strict=True)


def to_patient(pid, g, birth_code):
    events = []
    for t, h in g.groupby("time", sort=True):
        events.append({"time": t.to_pydatetime(),
                       "measurements": [{"code": birth_code if c == "MEDS_BIRTH" else c} for c in h.code]})
    return {"patient_id": int(pid), "events": events}


def cmd_encode(a) -> None:
    import importlib.metadata as md
    shim, meds, torch, FEMRModelConfig, FEMRBatchProcessor, FEMRTokenizer, FEMRModel = import_femr()
    versions = {p: md.version(p) for p in ("femr", "meds", "torch", "transformers", "numpy", "pyarrow")}
    if versions["femr"] != "0.2.3" or versions["meds"] != "0.1.3":
        raise SystemExit(f"requires femr 0.2.3 and meds 0.1.3, found {versions}")
    os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"
    t0 = time.time()
    mr = Path(a.model_root)
    hashes = {n: sha(mr / n) for n in MODEL_SHA256}
    if hashes != MODEL_SHA256 and not a.allow_other:
        raise SystemExit("model files differ from the Yale copy (run download, or --allow-other and record it)")
    rd = rdir()
    tag = f"_{a.tag}" if a.tag else ""
    X = pd.read_parquet(a.events or rd / f"chs_clmbr{tag}_events.parquet")
    Q = pd.read_parquet(a.queries or rd / f"chs_clmbr{tag}_queries.parquet")
    if a.limit:
        keep = np.sort(Q.subject_id.unique())[: a.limit]
        Q, X = Q[Q.subject_id.isin(keep)], X[X.subject_id.isin(keep)]
    dev = "cuda" if (a.device == "auto" and torch.cuda.is_available()) or a.device == "cuda" else "cpu"
    torch.manual_seed(SEED)
    torch.set_num_threads(max(1, a.threads))
    cfg = FEMRModelConfig.from_pretrained(str(mr), local_files_only=True)
    tok = FEMRTokenizer.from_pretrained(str(mr))
    if tok.is_hierarchical:
        raise SystemExit("hierarchical tokenizer not supported")
    proc = FEMRBatchProcessor(tok)
    model = FEMRModel(cfg)
    load_exact(model, mr / "model.safetensors")
    model = model.eval().to(dev)
    for p_ in model.parameters():
        p_.requires_grad_(False)

    def move(x):
        if isinstance(x, dict):
            return {k: move(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return type(x)(move(v) for v in x)
        return x.to(dev) if torch.is_tensor(x) else x

    def forward(patient):
        pre = proc.convert_patient(patient)
        n = int(pre["transformer"]["valid_tokens"].sum())
        raw = proc.convert_patient(patient, offset=max(0, n - a.max_tokens), max_length=a.max_tokens, tensor_type="pt")
        with torch.inference_mode():
            _, res = model(**move(proc.collate([raw])))
        return (res["representations"].float().cpu().numpy(), res["timestamps"].cpu().numpy(), n)

    def pick(reps, ts, cutoff):
        c = pd.Timestamp(cutoff).replace(tzinfo=dt.timezone.utc).timestamp()
        idx = np.nonzero(ts < c)[0]
        return reps[idx[-1]] if len(idx) else None, (len(idx) if len(idx) else 0)

    qs = {s: g for s, g in Q.groupby("subject_id")}
    rows, vecs, stats = [], [], dict(subjects=0, truncated=0, rows_birth_only=0, attempted=0, accepted=0)
    verify, diffs = set(sorted(s for s, g in qs.items() if len(g) > 1)[: a.verify]), []
    for sid, g in X.groupby("subject_id", sort=True):
        if sid not in qs:
            continue
        patient = to_patient(sid, g, meds.birth_code)
        tok.start_patient()
        for e in patient["events"]:
            for m in e["measurements"]:
                if m["code"] != meds.birth_code:
                    stats["attempted"] += 1
                    stats["accepted"] += int(bool(tok.get_feature_codes(e["time"], m)[0]))
        reps, ts, n = forward(patient)
        stats["subjects"] += 1
        trunc = n > a.max_tokens
        stats["truncated"] += int(trunc)
        for r_, cutoff in qs[sid][["row", "cutoff"]].itertuples(index=False):
            if trunc:  # prefix extraction is only exact without truncation: encode this row's own timeline
                sub = dict(patient, events=[e for e in patient["events"] if e["time"] < pd.Timestamp(cutoff)])
                rr, tt, _ = forward(sub)
                v, k = pick(rr, tt, cutoff)
            else:
                v, k = pick(reps, ts, cutoff)
            if v is None or not np.all(np.isfinite(v)):
                raise SystemExit("no representation before a cutoff (birth event after cutoff?)")
            stats["rows_birth_only"] += int(k == 1)
            rows.append(int(r_))
            vecs.append(v.astype(np.float32))
        if sid in verify and not trunc:  # causal-prefix check: re-encode the first row's truncated timeline
            r0 = qs[sid].sort_values("cutoff").iloc[0]
            sub = dict(patient, events=[e for e in patient["events"] if e["time"] < pd.Timestamp(r0.cutoff)])
            rr, tt, _ = forward(sub)
            diffs.append(float(np.abs(rr[-1] - pick(reps, ts, r0.cutoff)[0]).max()))
        if stats["subjects"] % 1000 == 0:
            print(time.strftime("%H:%M:%S"), "subjects", stats["subjects"], flush=True)
    V = np.vstack(vecs) if vecs else np.zeros((0, DIM), np.float32)
    if V.shape[1] != DIM:
        raise SystemExit(f"unexpected representation size {V.shape[1]}")
    out = pd.DataFrame(V, columns=[f"c{j}" for j in range(DIM)])
    out.insert(0, "row", rows)
    name = f"chs_clmbr{tag}" if not a.limit else f"chs_clmbr{tag}_smoke"
    out.to_parquet(rd / f"{name}.parquet", index=False)
    info = dict(when=time.strftime("%Y-%m-%d %H:%M"), device=dev, xformers_shim=shim, runtime=versions,
                model_sha256_ok=hashes == MODEL_SHA256, max_tokens=a.max_tokens, limit=a.limit,
                subjects=sup(stats["subjects"]), rows=sup(len(rows)), truncated_subjects=sup(stats["truncated"]),
                rows_birth_only=sup(stats["rows_birth_only"]),
                accepted_share=round(stats["accepted"] / max(stats["attempted"], 1), 3),
                prefix_check_n=len(diffs), prefix_check_max_abs_diff=max(diffs) if diffs else None,
                mean_norm=round(float(np.linalg.norm(V, axis=1).mean()), 3) if len(V) else None,
                seconds=round(time.time() - t0))
    o = out_dir()
    (o / (f"encode{tag}.json" if not a.limit else f"encode{tag}_smoke.json")).write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))
    if diffs and max(diffs) > a.tol:
        raise SystemExit(f"causal-prefix check failed: max |diff| {max(diffs):.2e} > {a.tol}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("timeline")
    t.add_argument("--map", required=True, help="chs_clmbr_map.json (uploaded by the user)")
    t.add_argument("--root", default="/sbgenomics/project-files")
    t.add_argument("--skip", nargs="*", default=["CYST_C_YR5"])
    t.add_argument("--rich", action="store_true", help="repeat ongoing conditions at every later clinic visit")
    t.add_argument("--tag", default="", help="output name suffix, e.g. rich -> chs_clmbr_rich_*")
    d = sp.add_parser("download")
    d.add_argument("--model-root", required=True)
    d.add_argument("--revision", default=REVISION)
    d.add_argument("--allow-other", action="store_true")
    e = sp.add_parser("encode")
    e.add_argument("--model-root", required=True)
    e.add_argument("--events", default=None)
    e.add_argument("--queries", default=None)
    e.add_argument("--tag", default="", help="timeline/embedding name suffix (as timeline --tag)")
    e.add_argument("--max-tokens", type=int, default=4096)
    e.add_argument("--limit", type=int, default=0, help="first N subjects only (smoke test; output chs_clmbr_smoke)")
    e.add_argument("--verify", type=int, default=50, help="subjects re-encoded for the causal-prefix check")
    e.add_argument("--tol", type=float, default=1e-3)
    e.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    e.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    e.add_argument("--allow-other", action="store_true")
    a = ap.parse_args(argv)
    {"timeline": cmd_timeline, "download": cmd_download, "encode": cmd_encode}[a.cmd](a)


if __name__ == "__main__":
    main()
