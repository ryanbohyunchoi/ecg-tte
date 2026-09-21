#!/usr/bin/env python3
"""Count-only HF phenotype sensitivities on a fixed COMET candidate roster."""
import argparse
from collections import Counter
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import re
import time

from build_shared_tables import BuildError, atomic_json, digest, open_table
from build_comet_candidates import records
from check_comet_runs import check
from hf_joint_evidence import HF, SYSTOLIC

DIASTOLIC={'I503','I5030','I5031','I5032','I5033'}
COMBINED={'I504','I5040','I5041','I5042','I5043'}
VIEWS=('DX_DATE','CALC_DX_DATE')
SCENARIOS=('systolic_or_ef_lt40','general_hf_or_ef_lt40',
 'general_exclude_isolated_diastolic_or_hfpef_code_branch',
 'general_exclude_isolated_diastolic_or_hfpef_entire_patient',
 'general_exclude_any_diastolic_or_hfpef_code_branch',
 'general_exclude_any_diastolic_or_hfpef_entire_patient')


@lru_cache(maxsize=16384)
def dx_flags(cell,name):
    # Explicit lexical diagnostics, not NLP or a validated phenotype. No names exported.
    if len(cell)>4096 or len(name)>4096:raise BuildError('diagnosis_cell_exceeds_review_bound')
    raw=[t.strip().upper() for t in re.split('[,;|]',cell)]
    valid=bool(raw) and all(re.fullmatch(r'[A-Z][0-9][A-Z0-9](?:\.?[A-Z0-9]{1,4})?',t) for t in raw)
    tokens={t.replace('.','') for t in raw} if valid else set()
    # HFpEF abbreviations, HF with preserved EF/ejection fraction, and isolated
    # diastolic codes are distinct from combined systolic/diastolic codes.
    hfpef=bool(re.search(r'\bhf\s*p\s*ef\b|\bpreserved\s+(?:left\s+ventricular\s+)?(?:ejection\s+fraction|ef)\b',name,re.I))
    diastolic_mention=bool(re.search(r'\bdiastolic\b',name,re.I))
    return frozenset(label for label,on in (
        ('general',bool(tokens&HF)),('systolic',bool(tokens&SYSTOLIC)),
        ('isolated_diastolic',bool(tokens&DIASTOLIC)),('combined',bool(tokens&COMBINED)),
        ('hfpef_mention',hfpef),('diastolic_mention',diastolic_mention),
        ('unresolved_code',not valid)) if on)


def scenarios(flags,low):
    general='general' in flags
    isolated=bool(flags&{'isolated_diastolic','hfpef_mention'})
    any_diastolic=bool(flags&{'isolated_diastolic','combined','hfpef_mention','diastolic_mention'})
    return dict(zip(SCENARIOS,(
        'systolic' in flags or low, general or low,
        (general and not isolated) or low, (general or low) and not isolated,
        (general and not any_diastolic) or low, (general or low) and not any_diastolic)))


def echo_state(echo,index):
    if echo is None:return 'no_prior_echo'
    if (index-echo['day']).days>365:return 'stale_over365'
    if len(echo['values'])!=1:return 'latest_day_disagreement'
    value=next(iter(echo['values']))
    if value=='missing':return 'missing'
    if value=='invalid':return 'invalid_or_scale_unresolved'
    if value<40:return 'gt1_lt40'
    if value==40:return 'eq40'
    return 'gt40_le100'


def discover(root):
    found=[p/'report' for p in sorted(Path(root).glob('comet-candidates-*'))
           if p.is_dir() and check(p).get('check')=='complete_candidate_artifact_verified']
    if len(found)!=1:raise BuildError('need_exactly_one_verified_candidate_run_or_explicit_report')
    return found[0]


def run(candidate_report,output):
    import pyarrow.parquet as pq
    started=time.monotonic()
    candidate_report,output=Path(candidate_report),Path(output)
    if not candidate_report.is_absolute() or not output.is_absolute() or output.is_symlink():raise BuildError('absolute_paths_required')
    if check(candidate_report.parent).get('check')!='complete_candidate_artifact_verified':raise BuildError('candidate_artifact_not_verified')
    manifest=json.loads((candidate_report/'restricted_manifest.json').read_text())
    snapshot=Path(manifest['core_snapshot'])
    if digest(snapshot/'manifest.json')!=manifest['core_manifest_sha256']:raise BuildError('core_manifest_changed')
    for source in (candidate_report.resolve(),snapshot.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    report=dict(version='comet_hf_variants_v1',status='building',counts_valid=False,restricted_until_reviewed=True,
        interpretation='Count-only sensitivities on fixed lexical candidate anchors; not new users, clinical HFrEF validation or final eligibility.',
        rules=dict(echo='Latest strictly prior within365 days; numeric >1 and <40 hypothesis, EF=40 separate; units/availability unvalidated; no older fallback.',
                   diagnoses='Any strictly prior I50 search evidence; independent DX_DATE/CALC_DX_DATE. No ICD9; unvalidated source availability.',
                   exclusions='Any prior flag for patient, not merely removal of individual code rows; same-day/future excluded. Name matching is lexical, not negation-aware NLP.',
                   code_branch='Exclude code pathway only; low EF can qualify.',entire_patient='Exclude even if low EF qualifies.'),
        candidate_report=str(candidate_report),core_snapshot=str(snapshot),candidate_sha256=manifest['candidate_sha256'])
    atomic_json(output/'summary.json',report)
    try:
        tables={n:open_table(snapshot,n) for n in ('echo_studies','hospital_diagnoses','outpatient_diagnoses')}
        stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for t in tables.values() for p in t.files}
        with pq.ParquetFile(candidate_report/'restricted_candidates.parquet') as pf:
            if pf.metadata.num_rows>1000000:raise BuildError('candidate_limit')
            candidates={}
            for batch in pf.iter_batches(columns=['patient_key','candidate_arm','candidate_order_day']):
                for row in batch.to_pylist():
                    key=row['patient_key']
                    if key in candidates or not key or row['candidate_order_day'] is None:raise BuildError('invalid_candidate_anchor')
                    candidates[key]=row
        flags={p:{v:set() for v in VIEWS} for p in candidates}; echoes={}; undated_echo=set()
        print('Reading projected echo columns.',flush=True)
        for row in records(tables['echo_studies'],['__patient_key','__day_EchoDate','EF']):
            key=row['__patient_key']
            if key not in candidates:continue
            day=row['__day_EchoDate']
            if day is None:undated_echo.add(key);continue
            if day>=candidates[key]['candidate_order_day']:continue
            value=row['EF']
            value=('missing' if value is None else 'invalid' if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 1<value<=100 else value)
            old=echoes.get(key)
            if old is None or day>old['day']:echoes[key]=dict(day=day,values={value})
            elif day==old['day']:old['values'].add(value)
        for table in ('hospital_diagnoses','outpatient_diagnoses'):
            print('Reading '+table+' code/name/date projections.',flush=True)
            for row in records(tables[table],['__patient_key','__day_DX_DATE','__day_CALC_DX_DATE','CURRENT_ICD10_LIST','DX_NAME']):
                key=row['__patient_key']
                if key not in candidates:continue
                views=[v for v in VIEWS if row['__day_'+v] is not None and row['__day_'+v]<candidates[key]['candidate_order_day']]
                if not views:continue
                f=dx_flags(row['CURRENT_ICD10_LIST'] or '',row['DX_NAME'] or '')
                for v in views:flags[key][v].update(f)
        totals=Counter(); strata=Counter(); exclusions=Counter(); denominators=Counter()
        for key,row in candidates.items():
            arm=row['candidate_arm'];denominators[arm]+=1
            state=echo_state(echoes.get(key),row['candidate_order_day']);low=state=='gt1_lt40'
            for view in VIEWS:
                f=flags[key][view];values=scenarios(f,low)
                for label,on in values.items():totals[arm,view,label]+=int(on)
                for label in f:exclusions[arm,view,label]+=1
                strata[arm,view,'systolic' if 'systolic' in f else 'general_other' if 'general' in f else 'no_hf_code',state]+=1
        if digest(snapshot/'manifest.json')!=manifest['core_manifest_sha256'] or digest(candidate_report/'restricted_candidates.parquet')!=manifest['candidate_sha256'] or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=s for p,s in stamps.items()):raise BuildError('input_changed')
        report.update(status='complete_count_only',counts_valid=True,denominators=dict(denominators),
            undated_echo_candidate_keys=len(undated_echo),
            scenario_counts=[dict(arm=a,date_view=v,scenario=s,patient_keys=n,
                difference_from_systolic_or_ef_lt40=n-totals[a,v,'systolic_or_ef_lt40']) for (a,v,s),n in sorted(totals.items())],
            overlapping_diagnosis_flags=[dict(arm=a,date_view=v,flag=f,patient_keys=n) for (a,v,f),n in sorted(exclusions.items())],
            evidence_strata=[dict(arm=a,date_view=v,code_evidence=c,echo_state=e,patient_keys=n) for (a,v,c,e),n in sorted(strata.items())])
    except Exception as exc:
        report.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'count_failed_no_raw_error_export')
        raise
    finally:
        dx_flags.cache_clear();report['elapsed_seconds']=round(time.monotonic()-started,3)
        atomic_json(output/'summary.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--candidate-report',type=Path);group.add_argument('--audit-root',type=Path)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:r=run(a.candidate_report or discover(a.audit_root),a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
