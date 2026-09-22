#!/usr/bin/env python3
"""Verified, outcome-blind R mice diagnostic pilot; never declares effect readiness."""
import argparse
from collections import Counter
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest
from build_comet_cached_baseline import discover
from audit_comet_numeric_candidates import profile

BASE = Path(__file__).resolve().parents[1]
VERSION = 'comet_mice_pilot_v1'


def model_spec(rows):
    contract=json.loads((BASE/'docs/COMET_PSM_TABLE_V2.json').read_text())
    features=[r['name'] for r in contract['covariates']]
    binary=[r['name'] for r in contract['covariates'] if r['type']=='binary_recorded_evidence']
    numeric=[f for f in features if f not in binary and f!='recorded_sex']
    fixed=['age_at_index','recorded_sex','index_year','outpatient_visits','ed_encounters','hospital_admissions','treatment_arm']
    columns=['treatment_arm']+features
    if not rows or len({r['patient_key'] for r in rows})!=len(rows):raise BuildError('empty_or_duplicate_roster')
    if {r['treatment_arm'] for r in rows}!={'carvedilol_candidate','metoprolol_tartrate_candidate'}:raise BuildError('treatment_arms_invalid')
    for r in rows:
        if not set(columns)<=set(r):raise BuildError('model_columns_missing')
        if any(r[f] is None for f in fixed):raise BuildError('fixed_predictor_missing')
        if any(r[f] is not None and (not isinstance(r[f],(int,float)) or isinstance(r[f],bool) or not math.isfinite(r[f])) for f in numeric+binary):raise BuildError('invalid_numeric_value')
        if any(r[f] not in (None,0,1) for f in binary):raise BuildError('nonbinary_indicator')
        if not isinstance(r['recorded_sex'],str) or not r['recorded_sex'].strip() or r['recorded_sex']=='__MISSING__':raise BuildError('sex_category_invalid')
        if r['index_year']<2015 or r['index_date'].year!=r['index_year']:raise BuildError('calendar_mismatch')
        if any(r[f]<0 or r[f]!=int(r[f]) for f in ['outpatient_visits','ed_encounters','hospital_admissions']):raise BuildError('invalid_count')
    if len({r['recorded_sex'] for r in rows})>10:raise BuildError('sex_category_cardinality')
    for f in features:
        observed=[r[f] for r in rows if r[f] is not None]
        if len(observed)<len(rows) and (len(observed)<20 or len(set(observed))<2):raise BuildError('insufficient_target_support_'+f)
    return dict(version=VERSION,columns=columns,binary=binary,numeric=numeric,m=5,iterations=20,seed=20260922,
                interpretation='Diagnostic outcome-blind pilot. Units unverified; imputed binary values represent recorded-evidence indicators, not gold-standard disease. No eligibility imputation.')


def validate_completed(original,completed,spec):
    if len(completed)!=len(original):raise BuildError('completed_roster_size')
    converted=[]
    for source,row in zip(original,completed):
        if list(row)!=spec['columns']:raise BuildError('completed_columns')
        result={}
        for f in spec['columns']:
            value=row[f]
            if f in spec['numeric']+spec['binary']:
                try:value=float(value)
                except (ValueError,TypeError):raise BuildError('unfilled_or_invalid_numeric')
                if not math.isfinite(value):raise BuildError('nonfinite_imputation')
            if source[f] is not None and value!=source[f]:
                if f not in spec['numeric'] or not math.isclose(value,source[f],rel_tol=1e-14,abs_tol=1e-14):raise BuildError('observed_value_changed')
                value=source[f]
            if f in spec['binary'] and value not in (0,1):raise BuildError('nonbinary_imputation')
            result[f]=value
        converted.append(result)
    # PMM must draw from this target's observed donor values.
    for f in spec['numeric']:
        donors={r[f] for r in original if r[f] is not None}
        for s,r in zip(original,converted):
            if s[f] is None and r[f] not in donors:
                match=next((v for v in donors if math.isclose(v,r[f],rel_tol=1e-14,abs_tol=1e-14)),None)
                if match is None:raise BuildError('pmm_outside_observed_donors')
                r[f]=match
    return converted


def run(source,output,rscript='Rscript'):
    source,output=Path(source),Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (source,output)):raise BuildError('absolute_nonsymlink_paths_required')
    if source.resolve()==output.resolve() or source.resolve() in output.resolve().parents or output.resolve() in source.resolve().parents:raise BuildError('source_output_overlap')
    s=json.loads((source/'summary.json').read_text());m=json.loads((source/'manifest.json').read_text())
    if s.get('version')!='comet_mice_preparation_v1' or m.get('version')!=s['version'] or s.get('status')!='complete_mice_preparation' or s.get('counts_valid') is not True:raise BuildError('complete_preparation_required')
    checks={source/n:digest(source/n) for n in ('summary.json','manifest.json')}
    for name,h in m['outputs'].items():
        p=source/name
        if p.is_symlink() or source.resolve() not in p.resolve().parents or digest(p)!=h:raise BuildError('preparation_changed')
        checks[p]=h
    name='restricted_cleaned_baseline.parquet'
    if name not in m['outputs']:raise BuildError('baseline_unmanifested')
    rows=pq.read_table(source/name).to_pylist()
    if len(rows)!=s['rows'] or dict(Counter(r['treatment_arm'] for r in rows))!=s['denominators']:raise BuildError('roster_mismatch')
    spec=model_spec(rows)
    if shutil.which(rscript) is None:raise BuildError('Rscript_not_found')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    summary=dict(version=VERSION,status='running',counts_valid=False,ready_for_psm=False,ready_for_effects=False,restricted_until_reviewed=True,rows=len(rows),denominators=s['denominators'],source_report=str(source))
    atomic_json(output/'summary.json',summary);start=time.monotonic()
    try:
        atomic_json(output/'model_spec.json',spec)
        with (output/'restricted_model_input.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=spec['columns']);writer.writeheader()
            for row in rows:writer.writerow({f:'__MISSING__' if row[f] is None else int(row[f]) if f in spec['binary'] else row[f] for f in spec['columns']})
        atomic_json(output/'restricted_row_keys.json',[r['patient_key'] for r in rows])
        atomic_json(output/'restricted_missingness_mask.json',[{f:r[f] is None for f in spec['columns']} for r in rows])
        (output/'tmp').mkdir(mode=0o700)
        env=dict(os.environ,TMPDIR=str(output/'tmp'))
        with (output/'restricted_engine.log').open('w') as log:
            proc=subprocess.run([rscript,'--vanilla',str(BASE/'scripts/comet_mice_engine.R'),str(output/'restricted_model_input.csv'),str(output)],stdout=log,stderr=log,env=env)
        if proc.returncode:raise BuildError('mice_engine_failed_check_restricted_log')
        engine=json.loads((output/'engine_summary.json').read_text())
        distributions=[];bp=[]
        for i in range(1,spec['m']+1):
            with (output/f'restricted_completed_{i:02d}.csv').open() as stream:completed=list(csv.DictReader(stream))
            values=validate_completed(rows,completed,spec)
            import pyarrow as pa
            pq.write_table(pa.Table.from_pylist([dict(r,patient_key=o['patient_key'],index_date=o['index_date']) for o,r in zip(rows,values)]),output/f'restricted_completed_{i:02d}.parquet')
            for arm in sorted(s['denominators']):
                bp.append(dict(imputation=i,arm=arm,sbp_below_dbp=sum(r['sbp']<r['dbp'] for r in values if r['treatment_arm']==arm)))
                for f in spec['numeric']+spec['binary']:
                    for kind in ('observed','imputed'):
                        selected=[r[f] for o,r in zip(rows,values) if r['treatment_arm']==arm and ((o[f] is None)==(kind=='imputed'))]
                        distributions.append(dict(imputation=i,arm=arm,feature=f,kind=kind,**profile(selected)))
        if any(digest(p)!=h for p,h in checks.items()):raise BuildError('inputs_changed')
        atomic_json(output/'distribution_diagnostics.json',distributions)
        needs=bool(engine['warning_count'] or engine['logged_event_count'] or engine['predictor_matrix_changed'] or engine['method_changed'] or not engine['convergence_available'])
        summary.update(status='complete_pilot_requires_review',counts_valid=True,imputations=spec['m'],iterations=spec['iterations'],engine=engine,model_events_require_review=needs,bp_order_checks=bp,
                       interpretation='Computational pilot only; no convergence pass, missingness-assumption validation, matching or effects. Review traces, events, distributions and source limitations before reuse.')
        atomic_json(output/'manifest.json',dict(version=VERSION,input_checksums={str(p):h for p,h in checks.items()},code_checksums={str(p):digest(p) for p in [Path(__file__),BASE/'scripts/comet_mice_engine.R',BASE/'docs/COMET_PSM_TABLE_V2.json']},outputs={p.name:digest(p) for p in output.iterdir() if p.is_file() and p.name!='summary.json'}))
    except Exception as e:
        summary.update(status='failed_pilot',counts_valid=False,reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-report',type=Path);p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--rscript',default='Rscript');a=p.parse_args()
    try:run(a.source_report or discover(Path('/mnt/raid0/rbc58/ecg-tte'),'audits/comet-mice-prep-*/report/summary.json','comet_mice_preparation_v1','complete_mice_preparation'),a.output_dir,a.rscript)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('MICE pilot completed; review summary and diagnostics locally. Not cleared for PSM.');return 0
if __name__=='__main__':raise SystemExit(main())
