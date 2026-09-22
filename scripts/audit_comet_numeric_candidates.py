#!/usr/bin/env python3
"""Read small mapped baseline artifacts for raw-scale QC; no unit assumptions or edits."""
import argparse
from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import time
import pyarrow.parquet as pq
from build_shared_tables import BuildError, digest, atomic_json
from build_comet_cached_baseline import discover

VERSION='comet_numeric_qc_v1'
FIELDS=('age_at_index','lvef','sbp','dbp','heart_rate','bmi','creatinine','potassium','sodium','hemoglobin')
SENTINEL_CANDIDATES={99999.,999999.,9999999.,-99999.,-999999.,-9999999.}
MIN_GROUP=20


def quantile(values,p):
    if not values:return None
    x=sorted(values);pos=(len(x)-1)*p;low=int(pos);high=min(low+1,len(x)-1)
    fraction=pos-low
    return (1-fraction)*x[low]+fraction*x[high]


def profile(values):
    finite=[float(v) for v in values if v is not None and isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)]
    bins=Counter()
    for v in finite:
        label='negative' if v<0 else 'zero' if v==0 else 'lt0.1' if v<.1 else '0.1_to_lt1' if v<1 else '1_to_lt10' if v<10 else '10_to_lt100' if v<100 else '100_to_lt1000' if v<1000 else '1000_to_lt10000' if v<10000 else 'ge10000'
        bins[label]+=1
    return dict(rows=len(values),nulls=sum(v is None for v in values),finite=len(finite),
        nonfinite_or_non_numeric=sum(v is not None for v in values)-len(finite),
        possible_sentinel_values=sum(v in SENTINEL_CANDIDATES for v in finite),
        quantiles={str(p):quantile(finite,p) for p in (.01,.05,.25,.5,.75,.95,.99)} if len(finite)>=MIN_GROUP else None,
        quantiles_suppressed=len(finite)<MIN_GROUP,magnitude_counts=dict(bins))


def verify(report):
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'manifest.json').read_text())
    if s.get('version')!='comet_baseline_resolution_v2_mapped_labs' or m.get('version')!=s['version'] or s.get('status')!='complete_resolution_candidate' or s.get('counts_valid') is not True:raise BuildError('complete_mapped_resolution_required')
    checks={report/'summary.json':digest(report/'summary.json'),report/'manifest.json':digest(report/'manifest.json')}
    for name,h in m['outputs'].items():
        p=report/name
        if p.is_symlink() or report.resolve() not in p.resolve().parents or digest(p)!=h:raise BuildError('mapped_artifact_changed')
        checks[p]=h
    needed={'restricted_baseline_resolution.parquet','restricted_feature_status.parquet','restricted_lab_selected_lineage.parquet','lab_mapping_report.json'}
    if not needed<=set(m['outputs']):raise BuildError('mapped_artifacts_missing')
    return s,m,checks


def run(report,output):
    report,output=map(Path,(report,output))
    if any(not p.is_absolute() or p.is_symlink() for p in (report,output)):raise BuildError('absolute_nonsymlink_paths_required')
    a,b=report.resolve(),output.resolve()
    if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    source,manifest,checks=verify(report)
    rows=pq.read_table(report/'restricted_baseline_resolution.parquet').to_pylist();bykey={r['patient_key']:r for r in rows}
    if len(rows)!=len(bykey) or len(rows)!=source['rows'] or dict(Counter(r['treatment_arm'] for r in rows))!=source['denominators']:raise BuildError('roster_mismatch')
    if not all(set(FIELDS)<=r.keys() for r in rows):raise BuildError('numeric_columns_missing')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700);start=time.monotonic()
    summary=dict(version=VERSION,status='running',counts_valid=False,ready_for_mice=False,restricted_until_reviewed=True,
        source_report=str(report),rows=len(rows),denominators=source['denominators'],
        interpretation='Raw-scale observed-value distributions only. No unit inference, clinical range approval, sentinel removal, winsorization, imputation or effects. Selected quantiles suppress groups with fewer than20 finite values; no identifiers, dates or raw examples in summary.')
    atomic_json(output/'summary.json',summary)
    try:
        strata=defaultdict(list);joint=Counter();year=Counter();pair_flags=Counter()
        for r in rows:
            arm=r['treatment_arm']
            for f in FIELDS:strata[arm,f].append(r[f])
            missing=tuple(f for f in FIELDS if r[f] is None)
            joint[arm,missing]+=1
            for f in FIELDS:year[arm,int(r['index_year']),f,r[f] is not None]+=1
            if r['sbp'] is not None and r['dbp'] is not None:
                pair_flags[arm,'paired_bp_candidates']+=1
                if r['sbp']<r['dbp']:pair_flags[arm,'bp_first_below_second']+=1
        component_values=defaultdict(dict);seen=[]
        for r in pq.read_table(report/'restricted_lab_selected_lineage.parquet').to_pylist():
            k=r['patient_key'];target=r['target']
            if k not in bykey or target not in ('creatinine','potassium','sodium','hemoglobin'):raise BuildError('lineage_roster_or_target_mismatch')
            if r['result_day'] is None or not 1<=(bykey[k]['index_date']-r['result_day']).days<=90:raise BuildError('lineage_outside_baseline_window')
            if r['status']!='mapped_numeric_units_unverified':continue
            v=bykey[k][target]
            if v is None:raise BuildError('lineage_numeric_status_mismatch')
            try:raw=float(r['raw_value'])
            except (TypeError,ValueError):raise BuildError('lineage_value_unparsed')
            if not math.isfinite(raw) or raw!=v:raise BuildError('lineage_value_mismatch')
            key=(bykey[k]['treatment_arm'],target,r['source'],r['component_id'])
            component_values[key][k]=v
            seen.append((k,target))
        if set(seen)!={(r['patient_key'],f) for r in rows for f in ('creatinine','potassium','sodium','hemoglobin') if r[f] is not None}:raise BuildError('missing_numeric_lab_lineage')
        if any(digest(p)!=h for p,h in checks.items()):raise BuildError('inputs_changed')
        summary.update(status='complete_numeric_candidate_qc',counts_valid=True,
            observed_distributions=[dict(arm=a,feature=f,**profile(v)) for (a,f),v in sorted(strata.items())],
            lab_component_distributions=[dict(arm=a,target=t,source=s,component_id=c,**profile(list(v.values()))) for (a,t,s,c),v in sorted(component_values.items())],
            joint_missingness=[dict(arm=a,missing_features=list(fs),patient_keys=n) for (a,fs),n in sorted(joint.items())],
            calendar_availability=[dict(arm=a,index_year=y,feature=f,has_candidate_value=v,patient_keys=n) for (a,y,f,v),n in sorted(year.items())],
            paired_bp_qc=[dict(arm=a,flag=f,patient_keys=n) for (a,f),n in sorted(pair_flags.items())],
            possible_sentinel_policy='Exact +/-99999,999999,9999999 flagged for review only; not an exhaustive or source-validated sentinel list.',
            next_step='Review scales, tails, repeated extreme-value flags and component differences; approve explicit measurement and imputation contracts. Balance evaluation is required after matching and before outcome estimation.')
        atomic_json(output/'manifest.json',dict(version=VERSION,input_checksums={str(p):h for p,h in checks.items()},script_sha256=digest(Path(__file__))))
    except Exception as e:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-report',type=Path);p.add_argument('--project-root',type=Path,default=Path('/mnt/raid0/rbc58/ecg-tte'));p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:run(a.source_report or discover(a.project_root,'audits/comet-mapped-baseline-*/report/summary.json','comet_baseline_resolution_v2_mapped_labs','complete_resolution_candidate'),a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Numeric candidate QC complete; review summary locally. No values changed.');return 0

if __name__=='__main__':raise SystemExit(main())
