#!/usr/bin/env python
"""Post hoc per-trial patterns (V17_PATTERNS.md): per-trial ECG balance/gap changes by clinical domain and blinded
ECG relevance, and trial emulation by category. Reproduces claude-v17-confirm/per_trial_patterns.csv and
emulation_by_category.csv (code as run interactively on 2026-09-27). Aggregates only."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
A = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v17-confirm")
DOM = {'comet': 'HF', 'paradigm-hf-seq': 'HF', 'transform-hf': 'HF', 'elite-ii': 'HF', 'emperor-preserved-v2': 'HF', 'life': 'HTN/LVH',
       'allhat': 'HTN', 'value': 'HTN', 'ascot': 'HTN', 'ontarget': 'Vascular', 'insight': 'HTN', 'valiant': 'post-MI', 'plato': 'ACS',
       'aristotle': 'AF-OAC', 'rocket-af': 'AF-OAC', 'rely': 'AF-OAC', 'east-afnet4': 'AF-rhythm', 'cabana-v2': 'AF-rhythm',
       'affirm': 'AF-rhythm', 'af-chf': 'AF-rhythm', 'empa-reg': 'DM', 'carolina': 'DM', 'leader': 'DM', 'sustain6': 'DM', 'rewind': 'DM',
       'declare': 'DM', 'canvas': 'DM', 'tecos': 'DM', 'carmelina': 'DM', 'precision': 'NSAID', 'amplify': 'VTE', 'lodestar': 'Statin',
       'prove-it': 'Statin'}
CAT = {'AF-rhythm': 'AF', 'AF-OAC': 'AF', 'ACS': 'ACS/post-MI', 'post-MI': 'ACS/post-MI', 'HF': 'HF', 'DM': 'Diabetes', 'HTN': 'HTN',
       'HTN/LVH': 'HTN', 'Vascular': 'Other', 'NSAID': 'Other', 'VTE': 'Other', 'Statin': 'Other'}
rk = lambda n: n.replace('-v2', '').replace('-', '_')


def sf(d):
    d = np.asarray(d, float)
    sg = np.array(list(itertools.product([1, -1], repeat=len(d))))
    return ((sg * np.abs(d)).mean(1) <= d.mean() + 1e-12).mean()


def main():
    R = pd.read_csv(A / 'results_all.csv')
    R = R[R.half == 'full']
    sc = [c for c in R.columns if c.startswith('smd:')]
    S = json.load(open(ROOT / 'docs/v17/trial_selection.json'))['trials']
    lt = lambda r: 100 * (r[sc].astype(float).abs() < 0.1).sum() / r[sc].notna().sum()
    rows = []
    for t, g in R.groupby('trial'):
        u = g[g.arm_role == 'unmatched'].iloc[0]
        for ps in ('P1', 'P2'):
            h = g[g.ps == ps]
            a = {r: h[h.arm_role == r].iloc[0] for r in ['base', 'ECG', 'shufECG']}
            s = S.get(rk(t), {})
            rows.append(dict(trial=t, set=g.set.iloc[0], ps=ps, domain=DOM.get(t, '?'), ecg_rel=s.get('ecg_relevance'),
                             fid=s.get('fidelity_include'), n=int(a['base'].n), lt_u=lt(u), lt_b=lt(a['base']), lt_e=lt(a['ECG']),
                             d_lt=lt(a['ECG']) - lt(a['base']), d_lt_shuf=lt(a['shufECG']) - lt(a['base']),
                             absd_b=abs(a['base'].loghr - a['base'].rb), absd_e=abs(a['ECG'].loghr - a['ECG'].rb)))
    D = pd.DataFrame(rows)
    D['d_absd'] = D.absd_e - D.absd_b
    D.to_csv(A / 'per_trial_patterns.csv', index=False)
    D0 = D[['trial', 'domain', 'ecg_rel']].drop_duplicates().assign(cat=lambda x: x.domain.map(CAT))
    rng = np.random.default_rng(0)
    allrb = R[R.arm_role == 'base'].drop_duplicates('trial').set_index('trial')
    out = []
    for ps in ('P1', 'P2'):
        X = {r: R[(R.ps == ps) & (R.arm_role == r)].set_index('trial') for r in ('base', 'ECG', 'shufECG')}
        for cat, g in list(D0.groupby('cat')) + [('ECG relevance high (blinded)', D0[D0.ecg_rel == 'high']), ('All 33', D0)]:
            ts = list(g.trial)
            b, e, s = [X[r].loc[ts] for r in ('base', 'ECG', 'shufECG')]
            ab, ae, as_ = [np.abs(x.loghr - x.rb) for x in (b, e, s)]
            zb = (b.loghr - b.rb) ** 2 / (b.se ** 2 + b.rs ** 2)
            ze = (e.loghr - e.rb) ** 2 / (e.se ** 2 + e.rs ** 2)
            obs = (ae - ab).mean()
            null = np.array([(np.abs(e.loghr.values - q) - np.abs(b.loghr.values - q)).mean()
                             for q in (allrb.rb.values[rng.choice(len(allrb), len(ts), replace=False)] for _ in range(10000))])
            small = len(ts) <= 20
            out.append(dict(PS=ps, category=cat, n=len(ts), gap_base=ab.mean(), gap_ecg=ae.mean(), closer=f'{int((ae < ab).sum())}/{len(ts)}',
                            p_gap=sf(ae - ab) if small else np.nan, p_vs_shuf=sf(ae - as_) if small else np.nan,
                            shuffleRCT_p=(null <= obs).mean(), z2_base=zb.mean(), z2_ecg=ze.mean(), p_z2=sf(ze - zb) if small else np.nan,
                            consistent=f'{int((np.sqrt(zb) < 1.96).sum())}->{int((np.sqrt(ze) < 1.96).sum())}/{len(ts)}'))
    pd.DataFrame(out).to_csv(A / 'emulation_by_category.csv', index=False)


if __name__ == '__main__':
    main()
