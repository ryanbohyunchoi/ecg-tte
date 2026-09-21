#!/usr/bin/env python3
"""Fixed-roster COMET eligibility feasibility; signals are not clinical eligibility."""
import argparse
from collections import Counter
from datetime import date
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import re
import time

from audit_comet_beta_history import verify, classify, NAMES
from build_shared_tables import BuildError, atomic_json, digest, open_table
from build_comet_candidates import records

# Candidate name leads only. No ID, route, dose, continuity or class completeness claims.
ACE=set('captopril enalapril lisinopril ramipril benazepril fosinopril quinapril perindopril trandolapril moexipril'.split())
DIURETICS=set('furosemide bumetanide torsemide torasemide hydrochlorothiazide bendroflumethiazide'.split())
ALPHA=set('prazosin doxazosin terazosin phenoxybenzamine phentolamine'.split())
WINDOWS=(14,30,90,180,365)
# Every original criterion remains visible, even when its source is unavailable.
CRITERIA={
 'adult':('DOB mapping unavailable',()),
 'symptomatic_hf_nyha':('NYHA and clinical chronicity unvalidated',()),
 'ventricular_function':('Numeric EF screen only; units/availability unvalidated; alternative LV dimensions unavailable',('ef_le35','ef_lt40')),
 'cardiovascular_admission_2years':('Hospital DX file does not establish admission reason or setting',()),
 'stable_diuretic_2weeks':('Orders do not establish dose equivalence or stability',('diuretic_prior14to365',)),
 'ace_inhibitor_4weeks_or_exception':('Orders do not establish duration or intolerance',('ace_prior28to365',)),
 'recent_hf_therapy_change':('Class initiation and current regimen unvalidated',()),
 'recent_oral_beta_alpha_blocker':('Names/all routes; orders do not establish active oral treatment',('beta_prior14','alpha_prior14')),
 'iv_inotrope_requirement':('Requirement and route unvalidated',()),
 'diltiazem_verapamil':('Recent order signal only, not current treatment',('diltiazem_verapamil_prior14',)),
 'amiodarone_dose':('Recent name signal; dose and current use unavailable',('amiodarone_prior14',)),
 'recent_unstable_angina':('Incident event phenotype unvalidated',()),
 'recent_mi':('Two-calendar-month ICD10 family lead; diagnosis date is not event onset',('mi_recent',)),
 'recent_revascularization':('Procedure mapping unavailable',()),
 'uncontrolled_hypertension':('Validated baseline BP unavailable',()),
 'significant_valve_disease':('Hemodynamic significance not established by echo labels',()),
 'ventricular_arrhythmia':('Symptoms, sustained rhythm and adequacy of treatment unavailable',()),
 'class_i_antiarrhythmics':('Medication class mapping pending',()),
 'bradycardia':('Validated baseline pulse unavailable',()),
 'resting_symptomatic_pad':('Rest symptoms unvalidated',()),
 'conduction_disease_pacemaker_exception':('Conduction and device mapping pending',()),
 'hypotension':('Validated baseline BP unavailable',()),
 'asthma_copd':('Diagnosis phenotype mapping pending',()),
 'unstable_insulin_dependent_diabetes':('Instability unvalidated',()),
 'hepatic_disease':('Labs/units/upper reference limit unavailable',()),
 'recent_stroke':('Two-calendar-month cerebrovascular family lead, not adjudicated stroke',('stroke_recent',)),
 'endocrine_conditions':('Condition and treatment-status mappings pending',()),
 'limited_life_expectancy':('Prognosis unavailable',()),
 'pregnancy_contraception':('Status unavailable',()),
 'substance_use_or_compliance':('Clinical ascertainment unavailable; orders are not adherence',()),
 'investigational_drug':('Trial participation mapping unavailable',()),
 'informed_consent':('RCT consent not reproduced; research authorization is separate',()),
}


def two_months_before(day):
    import calendar
    year,month=divmod(day.year*12+day.month-1-2,12);month+=1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))


@lru_cache(maxsize=16384)
def code_leads(cell):
    if len(cell)>4096:raise BuildError('oversized_code_cell')
    if not cell.strip() or cell.strip().upper()=='NULL':return ('missing_code',)
    tokens=[t.strip().upper() for t in re.split('[,;|]',cell)]
    if not all(re.fullmatch(r'[A-Z][0-9][A-Z0-9](?:\.?[A-Z0-9]{1,4})?',t) for t in tokens):return ('unresolved_code',)
    families={t.replace('.','')[:3] for t in tokens}
    return tuple(k for k,v in [('mi',{'I21','I22'}),('stroke',{'I60','I61','I62','I63','I64'})] if families&v)


def medication_signals(names,lag):
    if any(len(n)>4096 for n in names):raise BuildError('oversized_medication_name')
    label,_=classify(names);words=set(re.findall('[a-z]+',' '.join(names).lower()))
    out=[]
    if label!='no_name_match':
        family='beta' if label=='named_generic' else 'unresolved_beta'
        if lag is None:out.append(family+'_undated')
        elif lag==0:out.append(family+'_same_day')
        else:out.extend(family+'_prior'+str(w) for w in WINDOWS if 1<=lag<=w)
    if lag is None or lag<1:return out
    if lag<=14:
        if words&ALPHA:out.append('alpha_prior14')
        if words&{'diltiazem','verapamil'}:out.append('diltiazem_verapamil_prior14')
        if 'amiodarone' in words:out.append('amiodarone_prior14')
    if 14<=lag<=365 and words&DIURETICS:out.append('diuretic_prior14to365')
    if 28<=lag<=365 and words&ACE:out.append('ace_prior28to365')
    return out


def ef_screen(echo,index,threshold):
    if echo is None:return 'unknown'
    if (index-echo['day']).days>365 or len(echo['values'])!=1:return 'unknown'
    value=next(iter(echo['values']))
    if value is None:return 'unknown'
    return 'meets_numeric_screen' if (value<=35 if threshold==35 else value<40) else 'fails_numeric_screen'


def run(report,output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    report,output=Path(report),Path(output)
    if not report.is_absolute() or not output.is_absolute() or output.is_symlink():raise BuildError('absolute_paths_required')
    s,m=verify(report);core=Path(s['core_snapshot']);cohort=report/'restricted_broad_candidates.parquet'
    for source in (core.resolve(),report.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    with pq.ParquetFile(cohort) as f:
        if not 0<f.metadata.num_rows<=1000000:raise BuildError('cohort_size_limit')
        rows=f.read(columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
    anchors={r['patient_key']:r for r in rows}
    if len(anchors)!=len(rows) or any(not r['patient_key'] or r['candidate_order_day'] is None or r['candidate_arm'] not in ('carvedilol_candidate','metoprolol_tartrate_candidate') for r in rows):raise BuildError('invalid_candidate_anchors')
    os.umask(0o077);output.mkdir(parents=True,mode=0o700,exist_ok=False);start=time.monotonic()
    summary=dict(version='comet_eligibility_feasibility_v1',status='building',counts_valid=False,restricted_until_reviewed=True,
        interpretation='Fixed-roster source feasibility only; no clinical exclusions, index changes, imputation, PSM or effects.',
        clinical_eligible_patients=None,cohort_report=str(report),core_snapshot=str(core),
        timing='Strict prior calendar days; recent DX uses two calendar months. Undated/same-day medication leads separate. No future eligibility evidence.',
        limitations='Exact trimmed identity unvalidated; code families and drug names are leads. No signal does not prove absence. EF percent/availability unvalidated. Failed extension not read.',
        source_status=dict(core='required_complete',demographics_vitals_labs='not_used_extension_not_available_as_complete_snapshot'))
    atomic_json(output/'summary.json',summary)
    try:
        signals={p:{} for p in anchors};echoes={};stamps={}
        def add(p,signal,source,row,day):
            # Retain one deterministic supporting record per signal; not a patient-wide absence proof.
            proof=(source,row,day)
            old=signals[p].get(signal)
            if old is None or proof[:2]<old[:2]:signals[p][signal]=proof
        def table(name):
            t=open_table(core,name)
            stamps.update({p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in t.files})
            return t
        print('Scanning medication evidence',flush=True)
        for r in records(table('medication_orders'),['__patient_key','__source_row','__day_ORDER_INST',*NAMES]):
            p=r['__patient_key']
            if p not in anchors:continue
            day=r['__day_ORDER_INST'];lag=None if day is None else (anchors[p]['candidate_order_day']-day).days
            for signal in medication_signals(tuple(r[n] or '' for n in NAMES),lag):add(p,signal,'medication_orders',r['__source_row'],day)
        print('Scanning echo evidence',flush=True)
        for r in records(table('echo_studies'),['__patient_key','__source_row','__day_EchoDate','EF']):
            p=r['__patient_key'];day=r['__day_EchoDate']
            if p not in anchors or day is None or day>=anchors[p]['candidate_order_day']:continue
            v=r['EF'];v=v if not isinstance(v,bool) and isinstance(v,(float,int)) and math.isfinite(v) and 1<v<=100 else None
            old=echoes.get(p)
            if old is None or day>old['day']:echoes[p]=dict(day=day,values={v},row=r['__source_row'])
            elif day==old['day']:old['values'].add(v);old['row']=min(old['row'],r['__source_row'])
        for name in ('hospital_diagnoses','outpatient_diagnoses'):
            print('Scanning diagnosis evidence: '+name,flush=True)
            for r in records(table(name),['__patient_key','__source_row','__day_DX_DATE','CURRENT_ICD10_LIST']):
                p=r['__patient_key'];day=r['__day_DX_DATE']
                if p not in anchors:continue
                index=anchors[p]['candidate_order_day']
                if day is not None and not two_months_before(index)<=day<index:continue
                for lead in code_leads(r['CURRENT_ICD10_LIST'] or ''):
                    add(p,lead+('_undated' if day is None else '_recent'),name,r['__source_row'],day)
        den=Counter(r['candidate_arm'] for r in rows);screens=Counter();signal_counts=Counter();overlaps=Counter();private=[]
        for p,r in anchors.items():
            arm=r['candidate_arm'];ef=echoes.get(p)
            a=ef_screen(ef,r['candidate_order_day'],35);b=ef_screen(ef,r['candidate_order_day'],40)
            screens[arm,'ef_le35',a]+=1;screens[arm,'ef_lt40',b]+=1
            for signal,(source,ordinal,day) in signals[p].items():
                signal_counts[arm,signal]+=1
                private.append(dict(patient_key=p,arm=arm,signal=signal,source=source,source_row=ordinal,evidence_day=day))
            if ef is not None:
                private.append(dict(patient_key=p,arm=arm,signal='latest_prior_echo_'+a,source='echo_studies',source_row=ef['row'],evidence_day=ef['day']))
            overlaps[arm,a,'beta_prior365' in signals[p],'mi_recent' in signals[p],'stroke_recent' in signals[p]]+=1
        for w in WINDOWS:
            for arm in den:
                count=sum(r['candidate_arm']==arm and 'beta_prior'+str(w) in signals[p] for p,r in anchors.items())
                if count>den[arm]:raise BuildError('denominator_invariant')
        if digest(cohort)!=m['output_sha256'] or digest(core/'manifest.json')!=m['core_manifest_sha256'] or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=stamp for p,stamp in stamps.items()):raise BuildError('input_changed')
        schema=pa.schema([('patient_key',pa.string()),('arm',pa.string()),('signal',pa.string()),('source',pa.string()),('source_row',pa.int64()),('evidence_day',pa.date32())])
        path=output/'restricted_evidence.parquet';pq.write_table(pa.Table.from_pylist(private,schema=schema),path,compression='zstd')
        atomic_json(output/'manifest.json',dict(version=summary['version'],cohort_sha256=m['output_sha256'],core_manifest_sha256=m['core_manifest_sha256'],output_sha256=digest(path),
            implementation_sha256={n:digest(Path(__file__).with_name(n)) for n in ('audit_comet_eligibility.py','audit_comet_beta_history.py','build_comet_candidates.py','build_shared_tables.py')},evidence_rows=len(private)))
        summary.update(status='complete_core_feasibility',counts_valid=True,denominators=dict(den),
            criterion_register=[dict(criterion=k,limitation=why,available_screens=list(parts),by_arm={a:dict(meets=0,fails=0,unknown=n) for a,n in den.items()}) for k,(why,parts) in CRITERIA.items()],
            numeric_screens=[dict(arm=a,screen=k,status=v,patient_keys=n) for (a,k,v),n in sorted(screens.items())],
            signal_counts=[dict(arm=a,signal=k,found=n,not_found=den[a]-n) for (a,k),n in sorted(signal_counts.items())],
            beta_lookback_counts=[dict(arm=a,days=w,named_lead_found=signal_counts[a,'beta_prior'+str(w)],no_named_lead_found=n-signal_counts[a,'beta_prior'+str(w)]) for a,n in sorted(den.items()) for w in WINDOWS],
            overlapping_evidence_groups=[dict(arm=a,ef35_screen=e,beta_prior365=bb,mi_recent=mi,stroke_recent=st,patient_keys=n) for (a,e,bb,mi,st),n in sorted(overlaps.items())],
            attrition='Not applied: clinical rules and missing-data policies not frozen. Numeric screens and lead absence are not eligibility.')
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'audit_failed_no_raw_error_export')
        raise
    finally:
        classify.cache_clear();code_leads.cache_clear();summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohort-report',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:r=run(a.cohort_report,a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
