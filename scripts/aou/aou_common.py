"""Shared configuration for the All of Us (AoU) replication of the TRACE-ECG pipeline without the ECG
(pipeline.md section 12; docs/aou/AOU_PLAN.md).

Runs inside the AoU Researcher Workbench (Controlled Tier). Nothing here reads Yale paths. Every output
directory is private (umask 077) under AOU_TTE_OUT (default ~/aou-tte). Restricted (participant-level)
files are named restricted_*; they never leave the Workbench and are never committed.

Dissemination rule (AoU Data and Statistics Dissemination Policy): participant counts 1-20 are never
written to an aggregate file, and neither is anything from which such a count can be derived
(suppress20 / suppress_frame). This is stricter than the repository's 1-10 rule and replaces it here.
The analysis rule "a cell with < 11 matched pairs is failed" (pipeline.md section 5) is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
ROOT = SCRIPTS.parent
for _p in (str(SCRIPTS), str(SCRIPTS / "v16")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

MIN_COUNT = 20          # AoU: counts 1..20 are suppressed
MIN_PAIRS = 11          # analysis rule (pipeline.md section 5), unchanged
SEED_SHUFFLE = 424242   # v13_common.Trial.shuffle_perm
SEED_IMPUTE = 20260923  # build_core_baseline.impute
ICD10_ERA_START = "2016-10-01"  # index floor: the 365-day look-back is entirely after the ICD-10-CM switch (2015-10-01)


# ---------------------------------------------------------------- paths
def out_root() -> Path:
    return Path(os.environ.get("AOU_TTE_OUT", str(Path.home() / "aou-tte"))).expanduser().resolve()


def paths() -> dict:
    R = out_root()
    return dict(root=R, extract=R / "extract", gold=R / "extract" / "gold", meds_gold=R / "extract" / "meds_gold",
                trials=R / "trials", grid=R / "grid", probe=R / "probe", share=R / "share")


def trial_dir(n: str) -> Path:
    return paths()["trials"] / n


def private_dir(p: Path, exist_ok: bool = True) -> Path:
    os.umask(0o077)
    p = Path(p)
    p.mkdir(parents=True, exist_ok=exist_ok, mode=0o700)
    return p


def cdr() -> str:
    """BigQuery dataset of the workspace CDR, e.g. 'fc-aou-cdr-prod-ct.C2024Q3R4' (set by the Workbench)."""
    v = os.environ.get("WORKSPACE_CDR")
    if not v:
        raise SystemExit("WORKSPACE_CDR is not set: run inside an AoU Workbench app (Controlled Tier workspace)")
    return v


def bq_client():
    from google.cloud import bigquery
    return bigquery.Client(project=os.environ.get("GOOGLE_PROJECT"))


def bq_df(sql: str, client=None) -> pd.DataFrame:
    client = client or bq_client()
    return client.query(sql).result().to_dataframe(create_bqstorage_client=True)


# ---------------------------------------------------------------- dissemination
def suppress20(n):
    """Count for an aggregate file: 0 or > 20 as is, 1-20 -> '<=20'."""
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return None
    n = int(n)
    return n if (n == 0 or n > MIN_COUNT) else f"<={MIN_COUNT}"


def round_count(n, base=100):
    """Rounded count for descriptive totals (e.g. table sizes); 1-20 -> '<=20'."""
    s = suppress20(n)
    return s if isinstance(s, str) or s == 0 else int(base * round(s / base)) if s >= base else s


COUNT_COLS = ("n", "n_t", "n_c", "n_pairs", "n_events", "events", "persons", "n_persons")
DERIVED_COLS = ("ess_t", "ess_c", "retain", "retain_main", "n_pairs_frac")


NONCOUNT_COLS = {"n_trials", "n_items", "n_draws", "n_vars", "n_cov", "n_codes_stored", "n_contrasts"}


def suppress_frame(D: pd.DataFrame, count_cols=COUNT_COLS, derived=DERIVED_COLS) -> pd.DataFrame:
    """Rows with any participant count 1-20 lose EVERY count and derived column (n = n_t + n_c would otherwise give
    the suppressed value back by differencing)."""
    D = D.copy()
    flag = np.zeros(len(D), bool)
    for c in count_cols:
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            flag |= ((v >= 1) & (v <= MIN_COUNT)).to_numpy()
    D["suppressed_le20"] = flag
    for c in list(count_cols) + list(derived):
        if c in D:
            D.loc[flag, c] = np.nan
    return D


def privacy_scan(root: Path) -> dict:
    """Scan every non-restricted csv under root for participant-count columns with values 1-20."""
    bad = []
    for f in sorted(Path(root).rglob("*.csv")):
        if f.name.startswith("restricted_"):
            continue
        D = pd.read_csv(f)
        for c in D.columns:
            if c in NONCOUNT_COLS:
                continue
            if c in COUNT_COLS or c.startswith(("n_", "count")) or c in ("persons", "events"):
                v = pd.to_numeric(D[c], errors="coerce")
                k = int(((v >= 1) & (v <= MIN_COUNT)).sum())
                if k:
                    bad.append(dict(file=str(f.relative_to(root)), column=c, cells=k))
    return dict(scanned=str(root), violations=bad, ok=not bad, when=time.strftime("%Y-%m-%d %H:%M"))


# ---------------------------------------------------------------- misc
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    os.umask(0o077)
    tmp = Path(str(path) + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, default=str))
    os.replace(tmp, path)


def git_sha() -> str:
    try:
        import subprocess
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


# ---------------------------------------------------------------- trials
def registry() -> dict:
    """name -> trial_specs key, the 41 registered Yale trial objects (v13_common.PRIMARY + EXTRA)."""
    from v13_common import EXTRA, PRIMARY
    return {n: k for n, (k, _) in {**PRIMARY, **EXTRA}.items()}


# display label (docs/emulation_quality_v2/quality_v2_final.json) -> registry name (= paper2_grid.LABEL_NAME)
LABEL_NAME = {"ARISTOTLE": "aristotle", "ROCKET-AF": "rocket-af", "RE-LY": "rely", "EAST-AFNET 4": "east-afnet4", "CABANA": "cabana-v2",
              "AFFIRM": "affirm", "AF-CHF": "af-chf", "FRAIL-AF": "frail-af", "LAAOS III": "laaos3", "PROTECT AF": "protect-af",
              "RAFT-AF": "raft-af", "ACTIVE W": "active-w", "COMET": "comet", "PARADIGM-HF": "paradigm-hf-seq",
              "TRANSFORM-HF": "transform-hf", "ELITE II": "elite-ii", "EMPEROR-Preserved": "emperor-preserved-v2", "LIFE": "life",
              "ALLHAT": "allhat", "VALUE": "value", "ASCOT-BPLA": "ascot", "INSIGHT": "insight", "PLATO": "plato",
              "VALIANT": "valiant", "EMPA-REG OUTCOME": "empa-reg", "CAROLINA": "carolina", "LEADER": "leader",
              "SUSTAIN-6": "sustain6", "REWIND": "rewind", "DECLARE-TIMI 58": "declare", "CANVAS Program": "canvas",
              "TECOS": "tecos", "CARMELINA": "carmelina", "ONTARGET": "ontarget", "PRECISION": "precision", "AMPLIFY": "amplify",
              "LODESTAR": "lodestar", "PROVE IT-TIMI 22": "prove-it"}
S38 = list(LABEL_NAME.values())


def analysed_sets() -> dict:
    """S38 (all emulated) and the provisional quality-v2 analysed set (docs/emulation_quality_v2/quality_v2_final.json)."""
    q = json.loads((ROOT / "docs" / "emulation_quality_v2" / "quality_v2_final.json").read_text())
    sq = [LABEL_NAME[x] for x in q["analysed_set"]]
    return {"S38": list(S38), f"Q{len(sq)}": sq}


def comparator_clusters() -> dict:
    """trial -> comparator cluster (docs/v17/trial_selection.json; = v17_confirm.cluster_of)."""
    J = json.loads((ROOT / "docs" / "v17" / "trial_selection.json").read_text())["comparator_clusters"]["clusters"]
    return {t: c for c, ts in J.items() for t in ts}
