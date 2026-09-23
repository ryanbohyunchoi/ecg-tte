#!/usr/bin/env python3
"""Review saved aggregate balance tables only; no patient reads or new matching."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import statistics
from build_shared_tables import BuildError,atomic_json,digest

FOCUS=('lvef','atrial_fibrillation','age_at_index','recorded_sex=Female','arni_order','creatinine','hemoglobin','sbp','dbp','heart_rate','bmi')

def read_csv(path):
    with path.open() as f:return list(csv.DictReader(f))

def stats(values,absolute=False):
    finite=[]
    for x in values:
        try:v=float(x)
        except (TypeError,ValueError):continue
        if math.isfinite(v):finite.append(abs(v) if absolute else v)
    return dict(min=min(finite),median=statistics.median(finite),max=max(finite),defined=len(finite)) if finite else dict(min=None,median=None,max=None,defined=0)

def combine(completed,observed,summary):
    by={(r['method'],int(r['imputation']),r['feature']):r for r in completed}
    ob={(r['method'],int(r['imputation']),r['feature']):r for r in observed}
    if len(by)!=len(completed) or len(ob)!=len(observed):raise BuildError('duplicate_balance_rows')
    allowed={c['name'] for c in json.loads((Path(__file__).resolve().parents[1]/'docs/COMET_PSM_TABLE_V2.json').read_text())['covariates']}
    features=sorted({f for _,_,f in ob})
    if any(f not in allowed and f not in ('recorded_sex=Female','recorded_sex=Male') for f in features):raise BuildError('unexpected_evaluation_feature')
    result=[]
    for method,infos in summary['methods'].items():
        for feature in features:
            ids=[(method,int(i['imputation']),feature) for i in infos]
            if any(k not in by or k not in ob for k in ids):raise BuildError('incomplete_feature_evaluation')
            c=[by[k] for k in ids];o=[ob[k] for k in ids]
            record=dict(method=method,feature=feature,
                completed_pre_abs_smd=stats([r['smd_pre'] for r in c],True),
                completed_post_abs_smd=stats([r['smd_post'] for r in c],True),
                observed_pre_abs_smd=stats([r['smd_pre'] for r in o],True),
                observed_post_abs_smd=stats([r['smd_post'] for r in o],True),
                observed_post_signed_smd=stats([r['smd_post'] for r in o]),
                completed_post_carvedilol_mean=stats([r['post_carvedilol_mean'] for r in c]),
                completed_post_metoprolol_mean=stats([r['post_metoprolol_mean'] for r in c]))
            for arm,sourcearm in (('carvedilol','carvedilol_candidate'),('metoprolol','metoprolol_tartrate_candidate')):
                pre=[int(r['pre_observed_'+arm]) for r in o];post=[int(r['post_observed_'+arm]) for r in o]
                if any(n<0 or n>summary['denominators'][sourcearm] for n in pre) or any(n<0 or n>i['pairs'] for n,i in zip(post,infos)):raise BuildError('invalid_observed_counts')
                record['pre_observed_'+arm]=stats(pre);record['post_observed_'+arm]=stats(post)
                record['post_observed_fraction_'+arm]=stats([n/i['pairs'] for n,i in zip(post,infos)])
            field='recorded_sex' if feature.startswith('recorded_sex=') else feature
            missing=[by.get((method,int(i['imputation']),'missing:'+field)) for i in infos]
            if any(r is None for r in missing):raise BuildError('missing_missingness_diagnostic')
            record['missingness_post_abs_smd']=stats([r['smd_post'] for r in missing],True)
            result.append(record)
    return result

def run(reports,out):
    if not out.is_absolute() or out.is_symlink() or any(not p.is_absolute() or p.is_symlink() for p in reports):raise BuildError('absolute_nonsymlink_paths_required')
    if any(p.resolve()==out.resolve() or p.resolve() in out.resolve().parents or out.resolve() in p.resolve().parents for p in reports):raise BuildError('source_output_overlap')
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    checks={};reviews=[];signatures=[]
    for root in reports:
        s=json.loads((root/'summary.json').read_text());m=json.loads((root/'manifest.json').read_text())
        if s.get('status')!='complete_exploratory_comparison' or not s.get('counts_valid'):raise BuildError('complete_comparison_required')
        for name in ('summary.json','manifest.json','comparison_balance.csv','comparison_observed_balance.csv'):
            p=root/name;h=digest(p)
            if p.is_symlink() or (name.endswith('.csv') and m['outputs'].get(name)!=h):raise BuildError('aggregate_artifact_changed')
            checks[str(p)]=h
        signatures.append((s['common_rows'],s['denominators'],s['contract']['checkpoint_weights_sha256']))
        rows=combine(read_csv(root/'comparison_balance.csv'),read_csv(root/'comparison_observed_balance.csv'),s)
        reviews.append(dict(report=str(root),version=s['version'],caliper=s['contract']['cosine_caliper'],common_rows=s['common_rows'],denominators=s['denominators'],features=rows))
    if any(s!=signatures[0] for s in signatures):raise BuildError('different_comparison_populations')
    if any(digest(Path(p))!=h for p,h in checks.items()):raise BuildError('inputs_changed')
    atomic_json(out/'all_feature_review.json',dict(reviews=reviews,restricted_until_reviewed=True))
    # Compact display uses a declared focus list; the full artifact includes every feature.
    focus=[]
    for r in reviews:
        focus.append(dict(caliper=r['caliper'],features=[dict(method=f['method'],feature=f['feature'],
            completed_median_abs_smd=f['completed_post_abs_smd']['median'],observed_median_abs_smd=f['observed_post_abs_smd']['median'],
            observed_signed_smd_range=[f['observed_post_signed_smd']['min'],f['observed_post_signed_smd']['max']],
            observed_n_carvedilol=[f['post_observed_carvedilol']['min'],f['post_observed_carvedilol']['max']],
            observed_n_metoprolol=[f['post_observed_metoprolol']['min'],f['post_observed_metoprolol']['max']]) for f in r['features'] if f['feature'] in FOCUS]))
    summary=dict(version='comet_observed_balance_review_v1',status='complete_saved_aggregate_review',restricted_until_reviewed=True,ready_for_effects=False,
        interpretation='Completed and observed-only SMDs have different fixed pre-match denominators. Available-case balance does not validate MAR or represent all patients. Signed SMD is carvedilol minus metoprolol. Focus list is descriptive after prior results; all features retained in full artifact.',reviews=focus)
    atomic_json(out/'summary.json',summary)
    atomic_json(out/'manifest.json',dict(input_checksums=checks,script_sha256=digest(Path(__file__)),outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reports',nargs='+',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:result=run(a.reports,a.output_dir)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Saved aggregate review:',a.output_dir/'summary.json')
    print('Caliper | Method | Feature | Completed abs SMD | Observed abs SMD | Observed N carvedilol / metoprolol')
    for i,review in enumerate(result['reviews']):
        for f in review['features']:
            if i and f['method']!='cosine':continue
            fmt=lambda v:'NA' if v is None else f'{v:.3f}'
            print(f"{review['caliper']} | {f['method']} | {f['feature']} | {fmt(f['completed_median_abs_smd'])} | {fmt(f['observed_median_abs_smd'])} | {f['observed_n_carvedilol']} / {f['observed_n_metoprolol']}")
