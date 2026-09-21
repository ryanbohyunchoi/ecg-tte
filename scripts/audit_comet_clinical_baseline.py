#!/usr/bin/env python3
"""Cohort-specific demographic linkage, encounter keys and vital catalog QC."""
import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from audit_comet_beta_history import verify
from build_shared_tables import BuildError, digest, open_table, atomic_json
from build_comet_candidates import records
from build_clinical_shared_tables import EXPECTED
from medication_quality import missing_kind

IDS={p.split('/')[0].replace('-','_')+'_'+p.split('/')[1].removeprefix('CarDS_2435227_').removesuffix('.txt').lower() for p in EXPECTED}


def discover(root):
    found=[]
    for p in Path(root).glob('clinical-sources-v1-*/snapshot/manifest.json'):
        m=json.loads(p.read_text())
        if m.get('status')=='complete' and set(m.get('stages',{}))==IDS:found.append(p.parent)
    if len(found)!=1:raise BuildError('need_one_complete_clinical_snapshot_or_explicit_path')
    return found[0]


def age_state(values,index):
    if not values:return 'no_demographic_match',None
    if len(values)!=1:return 'dob_conflict',None
    birth=next(iter(values))
    if birth is None:return 'dob_unusable',None
    age=index.year-birth.year-((index.month,index.day)<(birth.month,birth.day))
    if age<0 or age>120:return 'age_out_of_review_range',None
    return ('under18' if age<18 else 'adult_numeric'),age


def value_shape(value):
    if missing_kind(value):return 'missing_marker'
    if re.fullmatch(r'\s*[+-]?\d+(?:\.\d+)?\s*',value):return 'numeric_unvalidated'
    if re.fullmatch(r'\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s*',value):return 'slash_pair_unvalidated'
    return 'other_unparsed'


def run(cohort_report,snapshot,output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    cohort_report,snapshot,output=map(Path,(cohort_report,snapshot,output))
    if not all(p.is_absolute() for p in (cohort_report,snapshot,output)) or any(p.is_symlink() for p in (snapshot,output)):raise BuildError('absolute_nonsymlink_paths_required')
    _,cm=verify(cohort_report);manifest=snapshot/'manifest.json';mh=digest(manifest);m=json.loads(manifest.read_text())
    if m.get('status')!='complete' or set(m.get('stages',{}))!=IDS:raise BuildError('complete_exact_clinical_inventory_required')
    for source in (snapshot.resolve(),cohort_report.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    p=cohort_report/'restricted_broad_candidates.parquet'
    with pq.ParquetFile(p) as f:
        if not 0<f.metadata.num_rows<=1000000:raise BuildError('cohort_limit')
        cohort=f.read(columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
    anchors={r['patient_key']:r for r in cohort}
    if len(anchors)!=len(cohort) or any(not r['patient_key'] or not isinstance(r['candidate_order_day'],date) for r in cohort):raise BuildError('invalid_anchors')
    output.mkdir(parents=True,exist_ok=False,mode=0o700);os.chmod(output,0o700);os.umask(0o077);started=time.monotonic()
    summary=dict(version='comet_clinical_baseline_qc_v1',status='building',counts_valid=False,restricted_until_reviewed=True,
        clinical_snapshot=str(snapshot),cohort_report=str(cohort_report),
        interpretation='Exact-key linkage and pre-index record QC only; no clinical setting mapping, unit conversion, eligibility exclusions, MICE or PSM.',
        timing='Encounter source dates and RECORDED_TIME strictly prior days1-365; vital90-day flag separate. Demographic extract availability at index unvalidated.',
        clinical_eligible_patients=None)
    atomic_json(output/'summary.json',summary);db=None
    try:
        db=sqlite3.connect(output/'restricted_encounter_qc.sqlite');db.execute('PRAGMA temp_store=MEMORY')
        db.execute('CREATE TABLE events(source TEXT,patient TEXT,csn TEXT,day TEXT,PRIMARY KEY(source,patient,csn,day)) WITHOUT ROWID')
        births=defaultdict(set);sexes=defaultdict(set);demorows=Counter();scanqc=Counter();catalog=Counter();catalog_patients=defaultdict(set);settings=Counter();stamps={}
        for source in sorted(IDS):
            print('Auditing clinical source: '+source,flush=True)
            t=open_table(snapshot,source);stamps.update({q:(Path(q).stat().st_size,Path(q).stat().st_mtime_ns) for q in t.files})
            demo=source.endswith('_patients');vital=source.endswith('_vitals');hospital=source.endswith('_hosp_enc')
            if demo:cols=['__patient_key','__day_BIRTH_DATE','SEX_C','SEX']
            elif vital:cols=['__patient_key','__day_RECORDED_TIME','FLO_MEAS_ID','FLO_MEAS_NAME','DISP_NAME','MEAS_VALUE','UNIT']
            else:cols=['__patient_key','PAT_ENC_CSN_ID','__day_HOSP_ADMSN_DATE' if hospital else '__day_CONTACT_DATE']+(['ED_YN','INP_YN'] if hospital else [])
            for r in records(t,cols):
                key=r['__patient_key']
                if key not in anchors:continue
                arm=anchors[key]['candidate_arm'];index=anchors[key]['candidate_order_day']
                if demo:
                    demorows[key]+=1;births[key].add(r['__day_BIRTH_DATE'])
                    sex=tuple(None if missing_kind(r[n] or '') else r[n].strip() for n in ('SEX_C','SEX'))
                    if any(v is not None and len(v)>256 for v in sex):raise BuildError('oversized_demographic_label')
                    sexes[key].add(sex);continue
                day=r['__day_RECORDED_TIME' if vital else '__day_HOSP_ADMSN_DATE' if hospital else '__day_CONTACT_DATE']
                if day is None:scanqc[source,arm,'undated_rows']+=1;continue
                lag=(index-day).days
                if not 1<=lag<=365:continue
                scanqc[source,arm,'prior365_rows']+=1
                if vital:
                    values=tuple(r[n] or '' for n in ('FLO_MEAS_ID','FLO_MEAS_NAME','DISP_NAME','UNIT'))
                    if any(len(v)>256 for v in values) or len(r['MEAS_VALUE'] or '')>4096:raise BuildError('oversized_vital_catalog_value')
                    token=(source,arm,*values,'days1_90' if lag<=90 else 'days91_365',value_shape(r['MEAS_VALUE'] or ''))
                    if token not in catalog and len(catalog)>=20000:raise BuildError('catalog_limit_no_omission')
                    catalog[token]+=1;catalog_patients[token].add(key)
                    continue
                csn=r['PAT_ENC_CSN_ID'] or ''
                if missing_kind(csn):scanqc[source,arm,'missing_encounter_key_rows']+=1;continue
                csn=csn.strip()
                if len(csn)>256:raise BuildError('oversized_encounter_key')
                db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?)',(source,key,csn,day.isoformat()))
                if hospital:
                    vals=tuple(r[n] or '' for n in ('ED_YN','INP_YN'))
                    if any(len(v)>256 for v in vals):raise BuildError('oversized_setting_label')
                    settings[(source,arm,*vals)]+=1
            db.commit()
        den=Counter(r['candidate_arm'] for r in cohort);dqc=Counter();private=[];sexcat=Counter()
        for key,r in anchors.items():
            state,age=age_state(births[key],r['candidate_order_day']);sex=sexes[key]
            ss='no_match' if not sex else 'conflict' if len(sex)>1 else 'missing_or_partial' if None in next(iter(sex)) else 'single_raw_pair'
            dqc[r['candidate_arm'],state,ss]+=1
            for pair in sex:sexcat[pair]+=1
            private.append(dict(patient_key=key,arm=r['candidate_arm'],age_candidate=age,age_status=state,sex_status=ss,demographic_rows=demorows[key]))
        eqc=[]
        for source in sorted(IDS):
            if not (source.endswith('_hosp_enc') or source.endswith('_outpatient_enc')):continue
            counts=dict(db.execute('SELECT patient,COUNT(DISTINCT csn) FROM events WHERE source=? GROUP BY patient',(source,)))
            for arm,n in den.items():
                subset=[counts.get(k,0) for k,r in anchors.items() if r['candidate_arm']==arm]
                eqc.append(dict(source=source,arm=arm,patients_with_prior_key=sum(v>0 for v in subset),patients_without_prior_key=sum(v==0 for v in subset),distinct_patient_encounter_keys=sum(subset)))
        overlap=db.execute('SELECT COUNT(*) FROM (SELECT patient,csn FROM events GROUP BY patient,csn HAVING COUNT(DISTINCT source)>1)').fetchone()[0]
        conflicting=db.execute('SELECT COUNT(*) FROM (SELECT patient,csn FROM events GROUP BY patient,csn HAVING COUNT(DISTINCT day)>1)').fetchone()[0]
        multikey=db.execute('SELECT COUNT(*) FROM (SELECT csn FROM events GROUP BY csn HAVING COUNT(DISTINCT patient)>1)').fetchone()[0]
        if digest(manifest)!=mh or digest(p)!=cm['output_sha256'] or any((Path(q).stat().st_size,Path(q).stat().st_mtime_ns)!=stamp for q,stamp in stamps.items()):raise BuildError('input_changed')
        fields=['source','arm','FLO_MEAS_ID','FLO_MEAS_NAME','DISP_NAME','UNIT','window','value_shape']
        atomic_json(output/'restricted_mapping_catalog.json',dict(restricted_keep_on_cluster=True,warning='Local review only; raw labels may contain sensitive text. No measurement values exported.',
            vitals=[dict(values=dict(zip(fields,k)),rows=n,patient_keys=len(catalog_patients[k])) for k,n in sorted(catalog.items())],
            sex=[dict(SEX_C=k[0],SEX=k[1],patient_keys=n) for k,n in sorted(sexcat.items(),key=lambda x:repr(x[0]))],
            settings=[dict(source=s,arm=a,ED_YN=e,INP_YN=i,rows=n) for (s,a,e,i),n in sorted(settings.items())]))
        pq.write_table(pa.Table.from_pylist(private),output/'restricted_demographic_qc.parquet',compression='zstd')
        summary.update(status='complete_clinical_baseline_qc',counts_valid=True,denominators=dict(den),
            demographic_groups=[dict(arm=a,age_status=b,sex_status=c,patient_keys=n) for (a,b,c),n in sorted(dqc.items())],
            encounter_key_coverage=eqc,encounter_key_overlap=dict(patient_csn_in_multiple_sources=overlap,patient_csn_with_multiple_dates=conflicting,csn_with_multiple_patient_keys=multikey),
            record_qc=[dict(source=s,arm=a,flag=f,rows=n) for (s,a,f),n in sorted(scanqc.items())],
            vital_catalog_combinations=len(catalog),
            next_gate='Review restricted mapping catalog locally. Encounter key counts are not admissions/visits; source overlap is not resolved. Vital catalog counts are not BP/pulse/BMI availability until mapped.')
        db.close();db=None
        atomic_json(output/'manifest.json',dict(version=summary['version'],clinical_manifest_sha256=mh,cohort_sha256=cm['output_sha256'],script_sha256=digest(Path(__file__)),
            outputs={n:digest(output/n) for n in ('restricted_demographic_qc.parquet','restricted_mapping_catalog.json','restricted_encounter_qc.sqlite')}))
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'audit_failed_no_raw_error_export');raise
    finally:
        if db is not None:db.close()
        summary['elapsed_seconds']=round(time.monotonic()-started,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohort-report',required=True,type=Path)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--clinical-snapshot',type=Path);g.add_argument('--shared-root',type=Path)
    p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:r=run(a.cohort_report,a.clinical_snapshot or discover(a.shared_root),a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
