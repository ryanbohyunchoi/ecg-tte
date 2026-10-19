#!/usr/bin/env python
"""Standalone BCL ECG encoder + GE MUSE XML converter, for running the paper's ECG embedding inside BDC.

The encoder is a minimal copy of the maintained lab model (CNN0 encoder + lead-time transformer, 256-d
record-level output; upstream modules/models_torch.py CNN0SignalBackbone) and of its inference preprocessing
(upstream modules/utils_torch.process_ecg): a 10 s, 500 Hz, 12-lead signal in MICROVOLTS (the checkpoint was
trained on uV), minus a 500-sample running median per lead (baseline wander), as [batch, 1, 5000, 12].
Parity with the upstream embedder on MIMIC ECGs is tested in tests/test_bdc_ecg_bcl.py (on the H100 only).

MUSE XML (SPRINT/ACCORD/WHI on BDC): the Rhythm waveform stores 8 leads (I, II, V1-V6) as base64 little-endian
int16 x LeadAmplitudeUnitsPerBit (uV). III, aVR, aVL, aVF are derived (Einthoven/Goldberger), giving the Yale lead
order I, II, III, aVR, aVL, aVF, V1-V6.

Weights: a slim encoder-only checkpoint (make_slim) is uploaded to the BDC project by the user; never committed.

BDC usage (step 2; restricted in, restricted out, aggregate report):
  python scripts/bdc/ecg_bcl.py embed --ckpt /sbgenomics/project-files/<slim>.pt \
      [--cohort /sbgenomics/workspace/bdc-restricted/sprint_cohort.parquet] [--batch 64]
"""
from __future__ import annotations

import argparse
import base64
import math
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

# sha256 of the slim encoder exported 2026-10-15 from trained_12lead_30.pt (bcl_lead_time_transformer_e30_encoder.pt)
SLIM_SHA256 = "0ba4be5a8f871072e71828eae46136ed8efef22af200f6ec4c151333f8f0ba75"
LEADS12 = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
FS, N = 500, 5000


# ---------------------------------------------------------------- MUSE XML -> (5000, 12) uV
def muse_to_uv(data: bytes) -> np.ndarray:
    """(5000, 12) float32 microvolts in Yale lead order from GE MUSE XML bytes. Raises ValueError(reason)."""
    root = ET.fromstring(data)
    wave = None
    for w in root.iter("Waveform"):
        if (w.findtext("WaveformType") or "").strip() == "Rhythm":
            wave = w
            break
    if wave is None:
        raise ValueError("no_rhythm_waveform")
    fs = int(float(wave.findtext("SampleBase") or 0))
    if fs not in (250, 500):
        raise ValueError(f"fs_{fs}")
    leads = {}
    for ld in wave.iter("LeadData"):
        lid = (ld.findtext("LeadID") or "").strip().upper()
        raw = ld.findtext("WaveFormData")
        if not raw:
            continue
        units = (ld.findtext("LeadAmplitudeUnits") or "MICROVOLTS").strip().upper()
        if units != "MICROVOLTS":
            raise ValueError(f"units_{units}")
        upb = float(ld.findtext("LeadAmplitudeUnitsPerBit") or 1.0)
        leads[lid] = np.frombuffer(base64.b64decode(raw), dtype="<i2").astype(np.float64) * upb
    need = ["I", "II", "V1", "V2", "V3", "V4", "V5", "V6"]
    if any(k not in leads for k in need):
        raise ValueError("missing_leads")
    n_src = 10 * fs
    if any(len(leads[k]) < n_src for k in need):
        raise ValueError("short")
    x = {k: leads[k][:n_src] for k in need}
    i_, ii = x["I"], x["II"]
    derived = {"III": ii - i_, "AVR": -(i_ + ii) / 2, "AVL": i_ - ii / 2, "AVF": ii - i_ / 2}
    for k in ("III", "AVR", "AVL", "AVF"):  # use stored derived leads if present (12-lead exports)
        if k in leads and len(leads[k]) >= n_src:
            derived[k] = leads[k][:n_src]
    sig = np.stack([i_, ii, derived["III"], derived["AVR"], derived["AVL"], derived["AVF"]]
                   + [x[k] for k in ("V1", "V2", "V3", "V4", "V5", "V6")], axis=1)
    if fs != FS:
        from scipy.signal import resample
        sig = resample(sig, N, axis=0)
    if not np.isfinite(sig).all():
        raise ValueError("nonfinite")
    if (np.ptp(sig, axis=0) == 0).any():
        raise ValueError("flat_lead")
    return sig.astype(np.float32)


def preprocess(x_uv: np.ndarray) -> np.ndarray:
    """Upstream process_ecg for 10 s / 500 Hz / 12 leads: remove a 500-sample running median per lead."""
    from scipy.ndimage import median_filter
    x = np.asarray(x_uv, dtype=np.float64)[:N]
    if x.shape != (N, 12):
        raise ValueError(f"expected ({N}, 12), got {x.shape}")
    sig = x - median_filter(x, size=(FS, 1))
    return np.ascontiguousarray(sig[None, :, :], dtype=np.float32)


# ---------------------------------------------------------------- model (minimal copy of the lab backbone)
def _pooled_length(n):
    for p in (2, 2, 2, 4, 2, 2, 4):
        n = math.ceil(n / p)
    return n


def build_model(cfg: dict):
    import torch
    from torch import nn

    class ConvBNPool(nn.Sequential):
        def __init__(self, i, o, k, p):
            super().__init__(nn.Conv2d(i, o, kernel_size=(k, 1), padding=(k // 2, 0), bias=False),
                             nn.BatchNorm2d(o, eps=1e-3, momentum=0.01), nn.ReLU(),
                             nn.MaxPool2d(kernel_size=(p, 1), stride=(p, 1), ceil_mode=True))

    class CNN0Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            spec = ((1, 16, 7, 2), (16, 16, 7, 2), (16, 16, 5, 2), (16, 32, 5, 4), (32, 32, 3, 2), (32, 64, 3, 2),
                    (64, 64, 3, 4))
            self.blocks = nn.Sequential(*[ConvBNPool(*s) for s in spec])

        def forward(self, x):
            return self.blocks(x)

    class Backbone(nn.Module):
        def __init__(self, signal_length=5000, num_leads=12, token_dim=256, transformer_layers=2,
                     transformer_heads=8, transformer_ff_dim=1024, transformer_dropout=0.1):
            super().__init__()
            self.pooled_time = _pooled_length(signal_length)
            self.encoder = CNN0Encoder()
            self.token_projection = nn.Linear(64, token_dim)
            self.time_embedding = nn.Parameter(torch.zeros(self.pooled_time, token_dim))
            self.lead_embedding = nn.Parameter(torch.zeros(num_leads, token_dim))
            self.cls_token = nn.Parameter(torch.zeros(1, 1, token_dim))
            layer = nn.TransformerEncoderLayer(d_model=token_dim, nhead=transformer_heads,
                                               dim_feedforward=transformer_ff_dim, dropout=transformer_dropout,
                                               activation="gelu", batch_first=True, norm_first=True)
            self.transformer = nn.TransformerEncoder(layer, num_layers=transformer_layers, enable_nested_tensor=False)
            self.final_norm = nn.LayerNorm(token_dim)
            self.embed_dim = token_dim

        def forward(self, signal):
            f = self.encoder(signal)                      # [B, 64, T', 12]
            tok = self.token_projection(f.permute(0, 2, 3, 1))
            tok = tok + self.time_embedding[None, :, None, :] + self.lead_embedding[None, None, :, :]
            tok = tok.flatten(1, 2)
            cls = self.cls_token.expand(len(tok), -1, -1)
            tok = self.transformer(torch.cat((cls, tok), dim=1))
            return self.final_norm(tok[:, 0])

    if cfg.get("signal_representation") != "lead_time_transformer":
        raise ValueError(f"only lead_time_transformer is supported, got {cfg.get('signal_representation')}")
    keys = ("token_dim", "transformer_layers", "transformer_heads", "transformer_ff_dim", "transformer_dropout")
    return Backbone(signal_length=int(cfg["ecg_seconds"]) * int(cfg["ecg_freq"]), num_leads=int(cfg["num_leads"]),
                    **{k: cfg[k] for k in keys if k in cfg})


def load_encoder(path: str, device="cpu"):
    import torch
    ck = torch.load(path, map_location="cpu", weights_only=False)
    cfg = ck.get("config", {})
    state = ck.get("model_state_dict", ck.get("model", ck.get("state_dict", ck)))
    state = {k[len("module."):] if k.startswith("module.") else k: v for k, v in state.items()
             if not k.startswith(("projection_head.", "module.projection_head."))}
    model = build_model(cfg)
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        raise ValueError(f"checkpoint mismatch: missing={missing} unexpected={unexpected}")
    return model.to(device).eval(), cfg


def make_slim(src: str, dst: str) -> None:
    """Encoder-only checkpoint (no optimizer / projection head) for upload to BDC."""
    import torch
    ck = torch.load(src, map_location="cpu", weights_only=False)
    st = {k: v for k, v in ck["model_state_dict"].items() if not k.startswith("projection_head.")}
    keep = ("mode", "signal_representation", "ecg_seconds", "ecg_freq", "num_leads", "token_dim",
            "transformer_layers", "transformer_heads", "transformer_ff_dim", "transformer_dropout")
    torch.save(dict(model_state_dict=st, config={k: ck["config"][k] for k in keep if k in ck["config"]},
                    epoch=ck.get("epoch"), source=os.path.basename(src)), dst)


def embed_arrays(model, arrays, batch=64, device="cpu"):
    """arrays: iterable of (1, 5000, 12) float32 -> (n, 256) float32."""
    import torch
    out = []
    buf = []
    with torch.inference_mode():
        for a in arrays:
            buf.append(a)
            if len(buf) == batch:
                out.append(model(torch.from_numpy(np.stack(buf)).to(device)).float().cpu().numpy())
                buf = []
        if buf:
            out.append(model(torch.from_numpy(np.stack(buf)).to(device)).float().cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, 256), np.float32)


# ---------------------------------------------------------------- BDC step 2: embed the cohort's baseline ECGs
def _convert_one(path):
    """(array, None) or (None, failure reason) for one XML file (process-pool worker)."""
    try:
        return preprocess(muse_to_uv(Path(path).read_bytes())), None
    except Exception as e:  # noqa: BLE001
        return None, (str(e) if isinstance(e, ValueError) else type(e).__name__)


def find_ckpt(given: str) -> str:
    """The given path if it exists, else the first *.pt under /sbgenomics whose sha256 matches the slim encoder."""
    if given and Path(given).is_file():
        return given
    import hashlib
    hits = []
    for root in ("/sbgenomics/project-files", "/sbgenomics/projects", "/sbgenomics/workspace", str(Path.home())):
        for p in Path(root).rglob("*.pt") if Path(root).exists() else []:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            if h == SLIM_SHA256:
                return str(p)
            hits.append(str(p))
    raise SystemExit(f"encoder checkpoint not found (given {given!r}). *.pt files seen: {hits[:10]}. Upload "
                     "bcl_lead_time_transformer_e30_encoder.pt to the project and add it to this Data Studio analysis "
                     "(or drag it into /sbgenomics/workspace in JupyterLab), then pass --ckpt <path>.")


def cmd_embed(a) -> None:
    import pandas as pd
    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import bdc_common as BC
    S = BC.suppress
    a.ckpt = find_ckpt(a.ckpt)
    BC.log(f"checkpoint: {a.ckpt}")
    if BC.sha256(Path(a.ckpt)) != SLIM_SHA256 and not a.allow_other_ckpt:
        raise SystemExit("checkpoint sha256 does not match the exported BCL encoder; pass --allow-other-ckpt to override")
    cohort = Path(a.cohort)
    C = pd.read_parquet(cohort) if cohort.suffix == ".parquet" else pd.read_pickle(cohort)
    idc = a.id_col or ("MASKID" if "MASKID" in C else "id")
    # one embedding per ECG file (CHS: the same prior-visit ECG can serve several emulations)
    C = C[C.ECG_XML_PATH.notna()].drop_duplicates("ECG_XML_PATH").reset_index(drop=True)
    prev = None
    if a.reuse:  # embed only ECG files not already in <name>_ecg_bcl, then append (same checkpoint enforced below)
        for q in (cohort.parent / f"{a.name}_ecg_bcl.parquet", cohort.parent / f"{a.name}_ecg_bcl.pkl"):
            if q.exists():
                prev = pd.read_parquet(q) if q.suffix == ".parquet" else pd.read_pickle(q)
                break
        if prev is not None:
            done = set(prev.ECG_FILE)
            C = C[~C.ECG_XML_PATH.map(lambda x: Path(x).name).isin(done)].reset_index(drop=True)
            BC.log(f"--reuse: {len(done)} files already embedded; {len(C)} new files to embed")
            if not len(C):
                BC.log("nothing new to embed; existing embeddings kept unchanged")
                return
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, cfg = load_encoder(a.ckpt, device)
    t0 = time.time()
    ok, fails, parts = [], {}, []
    from concurrent.futures import ProcessPoolExecutor
    t_emb = 0.0
    paths = C.ECG_XML_PATH.tolist()
    # convert + embed in blocks so memory stays flat (2026-10-16: holding all converted arrays ran out of memory)
    with ProcessPoolExecutor(a.workers) as ex:  # XML decode + running-median filter: CPU-bound, ~0.4 s per ECG per core
        for start in range(0, len(paths), a.block):
            block = paths[start:start + a.block]
            arrays = []
            for j, (arr, why) in enumerate(ex.map(_convert_one, block, chunksize=4)):
                if arr is not None:
                    arrays.append(arr)
                    ok.append(start + j)
                else:
                    fails[why] = fails.get(why, 0) + 1
            te = time.time()
            if arrays:
                parts.append(embed_arrays(model, arrays, batch=a.batch, device=device))
            t_emb += time.time() - te
            del arrays
            BC.log(f"converted + embedded {min(start + a.block, len(paths))}/{len(paths)} ({time.time() - t0:.0f} s)")
    E = np.concatenate(parts) if parts else np.zeros((0, 256), np.float32)
    t2 = time.time()
    t1 = t2 - t_emb
    emb = pd.DataFrame(E, columns=[f"e{j}" for j in range(E.shape[1])])
    emb.insert(0, "ECG_FILE", [Path(x).name for x in C.ECG_XML_PATH.iloc[ok]])
    emb.insert(0, idc, C[idc].iloc[ok].to_numpy())
    if prev is not None:
        emb = pd.concat([prev, emb], ignore_index=True).drop_duplicates(["ECG_FILE"], keep="first")
    rdir = cohort.parent
    try:
        emb.to_parquet(rdir / f"{a.name}_ecg_bcl.parquet", index=False)
        rfile = rdir / f"{a.name}_ecg_bcl.parquet"
    except Exception:  # noqa: BLE001
        emb.to_pickle(rdir / f"{a.name}_ecg_bcl.pkl")
        rfile = rdir / f"{a.name}_ecg_bcl.pkl"
    # aggregate checks: degeneracy (the mV-input bug gave pairwise cosine ~1) and a sex/age linear probe
    Z = E / np.linalg.norm(E, axis=1, keepdims=True)
    rng = np.random.default_rng(0)
    s = rng.choice(len(Z), size=min(2000, len(Z)), replace=False)
    cos = Z[s] @ Z[s].T
    R = dict(when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), device=device, ckpt=os.path.basename(a.ckpt),
             ckpt_sha256_ok=BC.sha256(Path(a.ckpt)) == SLIM_SHA256,
             n_cohort_with_xml=S(len(C)), n_embedded=S(len(ok)), failures={k: S(v) for k, v in fails.items()},
             seconds_convert=round(t1 - t0), seconds_embed=round(t2 - t1),
             mean_pairwise_cosine=round(float(cos[np.triu_indices(len(s), 1)].mean()), 4),
             norm_p5_p50_p95=[round(float(v), 2) for v in np.percentile(np.linalg.norm(E, axis=1), [5, 50, 95])])
    Cm = C.iloc[ok].reset_index(drop=True)
    R["probe"] = probe(E, Cm)
    out = BC.out_root() / f"{a.name}_ecg"
    out.mkdir(parents=True, exist_ok=True)
    BC.write_json(out / "report.json", R)
    print(f"# {a.name.upper()} ECG embedding ({R['when']}, git {R['git'][:10]})")
    for k, v in R.items():
        if k not in ("when", "git"):
            print(f"- {k}: {v}")
    BC.log(f"restricted embeddings: {rfile} (stays in BDC); report: {out}/report.json")


PROBES = [("female_auc", ["FEMALE", "!MALE"], "bin"), ("age_r2", ["AGE"], "cont"), ("egfr_r2", ["EGFR"], "cont"),
          ("log_ntprobnp_r2", ["LOG_NTPROBNP"], "cont"), ("cornell_voltage_r2", ["ECG_CV"], "cont"),
          ("echo_lv_mass_r2", ["echo_lv_mass"], "cont"), ("creatinine_r2", ["lab_creatinine"], "cont"),
          ("sbp_r2", ["vital_sbp"], "cont"), ("ldl_r2", ["LDL_CALC", "lab_ldl"], "cont")]


def probe(E, C) -> dict:
    """5-fold ridge probes on standardised embeddings, for whichever target columns the cohort has (sanity gate: sex
    AUC >= 0.80; LDL is the negative control). '!MALE' = 1 - MALE."""
    import pandas as pd
    X = (E - E.mean(0)) / (E.std(0) + 1e-8)
    folds = np.random.default_rng(1).integers(0, 5, len(X))
    res = {}
    for name, cands, kind in PROBES:
        col = next((c for c in cands if c.lstrip("!") in C.columns), None)
        if col is None:
            continue
        y = pd.to_numeric(C[col.lstrip("!")], errors="coerce")
        if col.startswith("!"):
            y = 1 - y
        m = y.notna().to_numpy()
        if m.sum() < 100:
            continue
        yy, XX, ff = y.to_numpy()[m], X[m], folds[m]
        pred = np.zeros(len(yy))
        for k in range(5):
            tr, te = ff != k, ff == k
            A = np.c_[np.ones(tr.sum()), XX[tr]]
            w = np.linalg.solve(A.T @ A + 10.0 * np.eye(A.shape[1]), A.T @ yy[tr])  # ridge
            pred[te] = np.c_[np.ones(te.sum()), XX[te]] @ w
        if kind == "bin":
            from scipy.stats import rankdata
            r = rankdata(pred)
            n1 = yy.sum()
            res[name] = round(float((r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1))), 3)
        else:
            res[name] = round(float(1 - ((yy - pred) ** 2).sum() / ((yy - yy.mean()) ** 2).sum()), 3)
    return res


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("embed")
    e.add_argument("--ckpt", default="", help="slim encoder .pt (searched for under /sbgenomics if omitted)")
    e.add_argument("--cohort", default="/sbgenomics/workspace/bdc-restricted/sprint_cohort.parquet")
    e.add_argument("--name", default="sprint", help="output names: <name>_ecg_bcl.parquet, report <out>/<name>_ecg/")
    e.add_argument("--id-col", default="", help="participant ID column (default MASKID if present, else id)")
    e.add_argument("--batch", type=int, default=64)
    e.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 2) - 1)))
    e.add_argument("--block", type=int, default=512, help="ECGs converted and embedded per block (memory bound)")
    e.add_argument("--allow-other-ckpt", action="store_true", help="run with a checkpoint whose sha256 differs")
    e.add_argument("--reuse", action="store_true", help="keep the existing <name>_ecg_bcl embeddings; embed only new files")
    s = sub.add_parser("slim")
    s.add_argument("src")
    s.add_argument("dst")
    a = ap.parse_args(argv)
    if a.cmd == "embed":
        cmd_embed(a)
    else:
        make_slim(a.src, a.dst)


if __name__ == "__main__":
    main()
