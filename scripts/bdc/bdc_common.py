"""Shared helpers for the NHLBI BioData Catalyst (BDC, Seven Bridges) RCT work (docs/bdc/BDC_FEASIBILITY.md).

Runs inside a BDC Seven Bridges Data Studio. Nothing here reads Yale paths. Outputs go to a private directory
(umask 077): $BDC_TTE_OUT, else /sbgenomics/output-files/bdc-tte (saved to the project when the Data Studio
stops), else ~/bdc-tte. Participant-level files are named restricted_*; they never leave BDC and are never
committed.

Dissemination rule (CLAUDE.md, dbGaP DUC): aggregates only; participant counts 1-10 are written as '1-10', and
no participant-level value, identifier, date or file name is written to an aggregate file.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MIN_COUNT = 10  # counts 1..10 are suppressed

# Where Seven Bridges Data Studio mounts project files (read-only) and saves outputs.
SB_INPUT_ROOTS = ("/sbgenomics/project-files",)  # the workspace holds our own code and outputs, not inputs
SB_OUTPUT = Path("/sbgenomics/output-files")


def out_root() -> Path:
    env = os.environ.get("BDC_TTE_OUT")
    if env:
        p = Path(env)
    elif SB_OUTPUT.exists():
        p = SB_OUTPUT / "bdc-tte"
    else:
        p = Path.home() / "bdc-tte"
    os.umask(0o077)
    p.mkdir(parents=True, exist_ok=True)
    return p


def suppress(n):
    """Count for an aggregate file: 0 or > 10 as is, 1-10 -> '1-10'."""
    if n is None:
        return None
    n = int(n)
    return n if (n == 0 or n > MIN_COUNT) else f"1-{MIN_COUNT}"


def round_count(n, base=100):
    """Rounded count for descriptive totals; 1-10 -> '1-10'."""
    s = suppress(n)
    if isinstance(s, str) or s == 0 or s < base:
        return s
    return int(base * round(s / base))


def write_json(path: Path, obj) -> None:
    os.umask(0o077)
    tmp = Path(str(path) + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=1, default=str))
    os.replace(tmp, path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)
