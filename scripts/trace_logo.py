#!/usr/bin/env python
"""Trace the raster CarDS Lab logo (trialemulate.pptx ppt/media/image1.png, 240x242; no vector source exists)
into an SVG path: Lanczos upsampling, marching squares on the darkness field at 0.5, loop assembly,
Douglas-Peucker simplification, even-odd fill. Output: docs/presentation/assets/cards_logo.svg"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

PPTX = "/mnt/raid0/rbc58/ecg-tte/trialemulate.pptx"
OUT = Path(__file__).resolve().parents[1] / "docs/presentation/assets/cards_logo.svg"
UP, TOL, FILL = 6, 0.35, "#0E103C"


def field():
    raw = zipfile.ZipFile(PPTX).read("ppt/media/image1.png")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    W, H = im.size
    g = np.asarray(im.resize((W * UP, H * UP), Image.LANCZOS).convert("L"), float) / 255.0
    d = 1.0 - g  # darkness
    d = np.pad(d, 1, constant_values=0.0)
    return d, W, H


def march(d, lev=0.5):
    """Marching squares with linear interpolation; returns dict edge-point -> neighbours (segments)."""
    b = d > lev
    H, W = d.shape
    segs = []
    tl, tr, br, bl = b[:-1, :-1], b[:-1, 1:], b[1:, 1:], b[1:, :-1]
    code = tl * 8 + tr * 4 + br * 2 + bl * 1
    ys, xs = np.nonzero((code > 0) & (code < 15))
    def ip(y0, x0, y1, x1):
        a, c = d[y0, x0], d[y1, x1]
        t = (lev - a) / (c - a) if c != a else 0.5
        return (x0 + t * (x1 - x0), y0 + t * (y1 - y0))
    for y, x in zip(ys, xs):
        c = code[y, x]
        T, R, B, L = (lambda: ip(y, x, y, x + 1)), (lambda: ip(y, x + 1, y + 1, x + 1)), (lambda: ip(y + 1, x, y + 1, x + 1)), (lambda: ip(y, x, y + 1, x))
        ctr = (d[y, x] + d[y, x + 1] + d[y + 1, x + 1] + d[y + 1, x]) / 4 > lev
        table = {1: [(L, B)], 2: [(B, R)], 3: [(L, R)], 4: [(T, R)], 6: [(T, B)], 7: [(L, T)], 8: [(L, T)], 9: [(T, B)],
                 11: [(T, R)], 12: [(L, R)], 13: [(B, R)], 14: [(L, B)],
                 5: [(L, T), (B, R)] if ctr else [(L, B), (T, R)], 10: [(L, B), (T, R)] if ctr else [(L, T), (B, R)]}
        for p, q in table[c]:
            segs.append((p(), q()))
    return segs


def loops(segs):
    key = lambda p: (round(p[0], 6), round(p[1], 6))
    adj = {}
    for p, q in segs:
        adj.setdefault(key(p), []).append(key(q)); adj.setdefault(key(q), []).append(key(p))
    seen, out = set(), []
    for s in list(adj):
        if s in seen:
            continue
        loop, prev, curp = [s], None, s
        seen.add(s)
        while True:
            nb = [n for n in adj[curp] if n != prev and n not in seen]
            if not nb:
                break
            prev, curp = curp, nb[0]
            seen.add(curp); loop.append(curp)
        if len(loop) > 8:
            out.append(np.array(loop))
    return out


def dp(P, tol):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    ab = b - a
    n = np.hypot(*ab)
    dist = np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / n if n else np.hypot(*(P - a).T)
    i = int(np.argmax(dist))
    if dist[i] > tol:
        return np.vstack([dp(P[: i + 1], tol)[:-1], dp(P[i:], tol)])
    return np.vstack([a, b])


def main():
    d, W, H = field()
    L = loops(march(d))
    parts = []
    for P in L:
        P = np.vstack([P, P[:1]])
        Q = dp(P, TOL * UP / 2)
        Q = (Q - 1) / UP  # remove pad, back to original pixel units
        if len(Q) < 4:
            continue
        parts.append("M" + " ".join(f"{x:.2f} {y:.2f}" for x, y in Q[:-1]) + "Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           f'<path fill="{FILL}" fill-rule="evenodd" d="{"".join(parts)}"/></svg>\n')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(OUT, len(parts), "loops", f"{len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    sys.exit(main())
