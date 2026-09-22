#!/usr/bin/env python3
"""Extract latest prior raw-scale vital candidates; not unit-validated PSM input."""
import argparse
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
import math
import os
from pathlib import Path
import re
import time
from audit_comet_beta_history import verify
from audit_comet_clinical_baseline import IDS
from build_shared_tables import BuildError, open_table, digest, atomic_json
from build_comet_candidates import records
from medication_quality import missing_kind

MAP={'5':('bp',90,'BLOOD PRESSURE','BP'), '8':('pulse',90,'PULSE','Pulse'),
     '301070':('bmi',365,'R BMI','BMI (Calculated)')}
NUM=r'[+-]?\d+(?:\.\d+)?'


def parse_candidate(raw,pair):
    if len(raw)>4096:raise BuildError('oversized_vital_value')
    if missing_kind(raw):return 'missing_value',None
    pattern=r'\s*('+NUM+r')\s*/\s*('+NUM+r')\s*' if pair else r'\s*('+NUM+r')\s*'
    match=re.fullmatch(pattern,raw)
    if match is None:return 'unparsed_value',None
    try:values=tuple(float(Decimal(v)) for v in match.groups())
    except (InvalidOperation,ValueError,OverflowError):return 'unparsed_value',None
    if not all(math.isfinite(v) for v in values):return 'nonfinite_value',None
    return 'numeric_raw_scale',values


def add_latest(state,day,observation):
    if day is None:
        state['undated']=True
        if len(state.setdefault('undated_observations',[]))>=10000:raise BuildError('undated_lineage_limit')
        state['undated_observations'].append(observation);return
    if state.get('day') is None or day>state['day']:state.update(day=day,observations=[observation])
    elif day==state['day']:
        if len(state['observations'])>=10000:raise BuildError('latest_day_lineage_limit')
        state['observations'].append(observation)


def choose(state,pair):
    if state.get('undated'):return 'unresolved_undated_record',None
    obs=state.get('observations',[])
    if not obs:return 'no_record_in_window',None
    if any(not o['labels_match'] or o['unit'].strip().upper()!='NULL' for o in obs):return 'mapping_signature_changed',None
    parsed=[parse_candidate(o['raw'],pair) for o in obs]
    if any(status!='numeric_raw_scale' for status,_ in parsed):return 'latest_value_unusable',None
    values={v for _,v in parsed}
    if len(values)!=1:return 'latest_day_disagreement',None
    return 'candidate_numeric_units_unverified',next(iter(values))



def choose_timed(state,feature):
    if state.get('undated'):return 'unresolved_undated_record',None
    obs=state.get('observations',[])
    if not obs:return 'no_record_in_window',None
    timed=[]
    for o in obs:
        raw=o.get('recorded_time','')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?',raw):return 'latest_day_time_unresolved',None
        try:stamp=datetime.fromisoformat(raw)
        except ValueError:return 'latest_day_time_unresolved',None
        if stamp.date()!=state['day']:return 'latest_day_time_unresolved',None
        timed.append((stamp,o))
    latest=max(t for t,o in timed)
    if feature=='bmi':selected=[o for t,o in timed if t==latest]
    else:
        keys={o.get('encounter_key') for t,o in timed if t==latest}
        if len(keys)!=1 or None in keys:return 'latest_encounter_unresolved',None
        key=next(iter(keys));selected=[o for t,o in timed if o.get('encounter_key')==key]
    if any(not o['labels_match'] or o['unit'].strip().upper()!='NULL' for o in selected):return 'mapping_signature_changed',None
    dedup={}
    for o in selected:
        status,value=parse_candidate(o['raw'],feature.startswith('bp'))
        if status!='numeric_raw_scale':return 'selected_value_unusable',None
        # Equal values at different times remain repeated readings; duplicate rows do not get extra weight.
        stamp=datetime.fromisoformat(o['recorded_time'])
        token=(stamp,o.get('encounter_key'),value)
        dedup[token]=value
    values=list(dedup.values())
    if feature=='bmi':
        if len(set(values))!=1:return 'latest_timestamp_disagreement',None
        return 'candidate_numeric_units_unverified',values[0]
    result=tuple(math.fsum(v[i]/len(values) for v in values) for i in range(len(values[0])))
    return 'candidate_numeric_units_unverified',result

def run(report,snapshot,output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    report,snapshot,output=map(Path,(report,snapshot,output))
    if not all(p.is_absolute() for p in (report,snapshot,output)) or any(p.is_symlink() for p in (snapshot,output)):raise BuildError('absolute_nonsymlink_paths_required')
    _,cm=verify(report);mp=snapshot/'manifest.json';mh=digest(mp);m=json.loads(mp.read_text())
    if m.get('status')!='complete' or set(m.get('stages',{}))!=IDS:raise BuildError('complete_clinical_snapshot_required')
    for source in (snapshot.resolve(),report.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    cp=report/'restricted_broad_candidates.parquet'
    with pq.ParquetFile(cp) as f:
        if not 0<f.metadata.num_rows<=1000000:raise BuildError('cohort_limit')
        cohort=f.read(columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
    anchors={r['patient_key']:r for r in cohort}
    if len(anchors)!=len(cohort) or any(not r['patient_key'] or not isinstance(r['candidate_order_day'],date) for r in cohort):raise BuildError('invalid_anchors')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700);start=time.monotonic()
    s=dict(version='comet_vital_candidates_v2',status='building',counts_valid=False,restricted_until_reviewed=True,
        ready_for_mice=False,clinical_snapshot=str(snapshot),cohort_report=str(report),
        interpretation='One row per fixed candidate; raw-scale numeric candidates only. No canonical units, BP orientation approval, availability-time validation or clinical ranges. No cohort exclusions or MICE.',
        timing='Latest strictly prior day: average BP/pulse within latest timestamp-identified encounter on that day; latest timestamp BMI. Primary BP/pulse90days, BMI365days; older BP/pulse days91-365 are separate auxiliaries. No older fallback. Undated matched components block primary and auxiliary.',
        unit_policy='Reviewed observed signature has literal NULL units; any changed labels/units on selected day blocks selection.')
    atomic_json(output/'summary.json',s)
    try:
        states={(k,f):{} for k in anchors for f in ('bp','pulse','bmi','bp_older','pulse_older')};stamps={}
        for source in sorted(x for x in IDS if x.endswith('_vitals')):
            print('Extracting candidate vitals: '+source,flush=True)
            t=open_table(snapshot,source);stamps.update({p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in t.files})
            for r in records(t,['__patient_key','__source_row','__day_RECORDED_TIME','RECORDED_TIME','PAT_ENC_CSN_ID','FLO_MEAS_ID','FLO_MEAS_NAME','DISP_NAME','MEAS_VALUE','UNIT']):
                key=r['__patient_key'];component=(r['FLO_MEAS_ID'] or '').strip()
                if key not in anchors or component not in MAP:continue
                feature,window,name,display=MAP[component];day=r['__day_RECORDED_TIME'];index=anchors[key]['candidate_order_day']
                if day is not None and not 1<=(index-day).days<=365:continue
                target=feature+'_older' if day is not None and feature!='bmi' and (index-day).days>90 else feature
                raw=r['MEAS_VALUE'] or '';unit=r['UNIT'] or ''
                if len(raw)>4096 or len(unit)>256:raise BuildError('oversized_vital_field')
                observation=dict(source=source,source_row=r['__source_row'],component=component,raw=raw,unit=unit,
                    labels_match=r['FLO_MEAS_NAME']==name and r['DISP_NAME']==display,recorded_time=r['RECORDED_TIME'] or '',
                    encounter_key=None if missing_kind(r['PAT_ENC_CSN_ID'] or '') else r['PAT_ENC_CSN_ID'].strip())
                if len(observation['recorded_time'])>128 or len(observation['encounter_key'] or '')>256:raise BuildError('oversized_time_or_encounter_key')
                add_latest(states[key,target],day,observation)
                if day is None and feature!='bmi':add_latest(states[key,feature+'_older'],day,observation)
        qc=Counter();joint=Counter();yearqc=Counter();olderqc=Counter();rows=[];lineage=[]
        for r in cohort:
            key=r['patient_key'];out=dict(patient_key=key,arm=r['candidate_arm'],index_date=r['candidate_order_day']);statuses=[]
            for feature in ('bp','pulse','bmi','bp_older','pulse_older'):
                state=states[key,feature];status,values=choose_timed(state,feature);statuses.append(status)
                qc[r['candidate_arm'],feature,status]+=1;out[feature+'_status']=status
                if feature.startswith('bp'):
                    out[feature+'_first_candidate']=None if values is None else values[0]
                    out[feature+'_second_candidate']=None if values is None else values[1]
                else:out[feature+'_candidate']=None if values is None else values[0]
                out[feature+'_observation_day']=state.get('day')
                for obs in state.get('observations',[]):lineage.append(dict(patient_key=key,feature=feature,observation_day=state['day'].isoformat(),**obs))
                for obs in state.get('undated_observations',[]):lineage.append(dict(patient_key=key,feature=feature,observation_day=None,**obs))
            joint[(r['candidate_arm'],*statuses[:3])]+=1
            for feature in ('bp','pulse','bmi'):
                yearqc[r['candidate_arm'],r['candidate_order_day'].year,feature,out[feature+'_status']]+=1
            for feature in ('bp','pulse'):
                olderqc[r['candidate_arm'],feature,out[feature+'_status'],out[feature+'_older_status']]+=1
            rows.append(out)
        if digest(cp)!=cm['output_sha256'] or digest(mp)!=mh or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=stamp for p,stamp in stamps.items()):raise BuildError('input_changed')
        fields=[('patient_key',pa.string()),('arm',pa.string()),('index_date',pa.date32()),('bp_first_candidate',pa.float64()),('bp_second_candidate',pa.float64()),('pulse_candidate',pa.float64()),('bmi_candidate',pa.float64())]
        fields.extend([('bp_older_first_candidate',pa.float64()),('bp_older_second_candidate',pa.float64()),('pulse_older_candidate',pa.float64())])
        for f in ('bp','pulse','bmi','bp_older','pulse_older'):fields.extend([(f+'_status',pa.string()),(f+'_observation_day',pa.date32())])
        path=output/'restricted_vital_candidates.parquet';pq.write_table(pa.Table.from_pylist(rows,schema=pa.schema(fields)),path,compression='zstd')
        atomic_json(output/'restricted_lineage.json',dict(restricted_keep_on_cluster=True,contains_raw_values=True,records=lineage))
        den=Counter(r['candidate_arm'] for r in cohort)
        s.update(status='complete_candidate_extraction',counts_valid=True,denominators=dict(den),
            feature_status_counts=[dict(arm=a,feature=f,status=t,patient_keys=n) for (a,f,t),n in sorted(qc.items())],
            arm_year_status_counts=[dict(arm=a,index_year=y,feature=f,status=t,patient_keys=n) for (a,y,f,t),n in sorted(yearqc.items())],
            older_auxiliary_counts=[dict(arm=a,feature=f,primary_status=p,older_status=o,patient_keys=n) for (a,f,p,o),n in sorted(olderqc.items())],
            joint_status_counts=[dict(arm=a,bp_status=b,pulse_status=p,bmi_status=m,patient_keys=n) for (a,b,p,m),n in sorted(joint.items())])
        atomic_json(output/'manifest.json',dict(version=s['version'],ready_for_mice=False,cohort_sha256=cm['output_sha256'],clinical_manifest_sha256=mh,
            output_sha256=digest(path),lineage_sha256=digest(output/'restricted_lineage.json'),script_sha256=digest(Path(__file__)),mapping=MAP))
    except Exception as exc:
        s.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'extraction_failed_no_raw_error_export');raise
    finally:
        s['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',s)
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('cohort-report','clinical-snapshot','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:r=run(a.cohort_report,a.clinical_snapshot,a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary only; raw values stay on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
