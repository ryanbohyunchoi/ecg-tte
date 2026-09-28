#!/usr/bin/env python
"""S11 (exploratory, PI request 2026-09-27): P5 = demographics + 5 disease codes (HTN, T2D, CAD, AF, HF) = the v1.7 P2
design without obesity. Identical code path to v17_confirm.py (monkeypatched P2DX); P1 rows are recomputed and must
equal results_all.csv. Output: claude-v17-confirm/results_p5.csv (ps label "P2" there = P5 here)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v17_confirm as V  # noqa: E402

V.P2DX = ["hypertension_v11", "t2d", "cad_ihd"]
if __name__ == "__main__":
    V.run(V.ALL, 32, "p5")
