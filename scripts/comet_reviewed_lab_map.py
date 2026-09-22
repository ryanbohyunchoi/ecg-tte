"""Reviewed component identities; raw-scale candidate extraction, never unit inference."""
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest
from medication_quality import missing_kind

VERSION='comet_lab_identity_map_v1'
# Exact reviewed triples in the 2025 outpatient and hospital1/2 catalog.
MAP={
 '795':('creatinine','BKR CREATININE','CREATININE'),
 '1526296':('creatinine','CREATININE','CREATININE'),
 '894':('potassium','BKR POTASSIUM','K'),
 '1534081':('potassium','POTASSIUM','K'),
 '893':('sodium','BKR SODIUM','NA'),
 '1534098':('sodium','SODIUM','NA'),
 '1256':('hemoglobin','BKR HEMOGLOBIN','HGB'),
 '17187':('hemoglobin','BKR WAM HEMOGLOBIN','HGB'),
 '1534435':('hemoglobin','HEMOGLOBIN','HGB'),
 '812':('hemoglobin','HEMOGLOBIN','HGB'),
 '24868':('hemoglobin','BKR HEMOGLOBIN (MC)','HGB')}
SOURCES={'outpatient_labs','Data_2025_04_03_hosp_enc_labs_1','Data_2025_04_03_hosp_enc_labs_2'}
TARGETS=('creatinine','potassium','sodium','hemoglobin')


def number(raw):
    if len(raw)>4096:raise BuildError('oversized_lab_value')
    if missing_kind(raw) or not re.fullmatch(r'\s*[+-]?\d+(?:\.\d+)?\s*',raw):return None
    try:v=float(Decimal(raw.strip()))
    except (InvalidOperation,ValueError,OverflowError):return None
    return v if math.isfinite(v) else None


def select_latest(obs):
    """No older fallback, no averaging of conflicting same-time labs."""
    if not obs:return None,'no_mapped_component_in_window',[]
    latest_day=max(o['day'] for o in obs);latest=[o for o in obs if o['day']==latest_day]
    for o in latest:
        raw=o['RESULT_TIME'] or ''
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?',raw):return None,'latest_day_time_unresolved',latest
        try:stamp=datetime.fromisoformat(raw)
        except ValueError:return None,'latest_day_time_unresolved',latest
        if stamp.date()!=latest_day:return None,'latest_day_time_date_conflict',latest
    stamp=max(datetime.fromisoformat(o['RESULT_TIME']) for o in latest)
    chosen=[o for o in latest if datetime.fromisoformat(o['RESULT_TIME'])==stamp]
    if any((o['COMPONENT_NAME'],o['BASE_NAME'])!=MAP[o['COMPONENT_ID']][1:] for o in chosen):return None,'component_signature_changed',chosen
    if any(o.get('SPECIMEN_TYPE')!='Blood' for o in chosen):return None,'specimen_not_confirmed_blood',chosen
    if any(re.search(r'URINE|FOLEY|CATHETER, URINE|CSF|STOOL|SWAB',o.get('SPECIMEN_SOURCE') or '',re.I) for o in chosen):return None,'specimen_source_conflict',chosen
    if any(o.get('explicit_units') for o in chosen):return None,'unit_signature_changed_requires_review',chosen
    values={number(o['ORD_VALUE'] or '') for o in chosen}
    if None in values:return None,'latest_value_non_numeric_or_missing',chosen
    if len(values)!=1:return None,'latest_timestamp_disagreement',chosen
    return next(iter(values)),'mapped_numeric_units_unverified',chosen


def extract(parent,anchors,output):
    lm=json.loads((parent/'labs'/'manifest.json').read_text())
    if {e['table'] for e in lm['tables']}!=SOURCES or len(lm['tables'])!=3:raise BuildError('reviewed_lab_sources_required')
    states={};rowqc=Counter();patients={};before={}
    for entry in lm['tables']:
        src=entry['table'];path=parent/'labs'/entry['file']
        if path.is_symlink() or (parent/'labs').resolve() not in path.resolve().parents or digest(path)!=entry['sha256']:raise BuildError('lab_extract_changed')
        before[path]=entry['sha256'];print('Mapping reviewed lab identities: '+src,flush=True)
        with pq.ParquetFile(path) as f:
            needed=['__patient_key','__source_row','__day_RESULT_DATE','RESULT_TIME','COMPONENT_ID','COMPONENT_NAME','BASE_NAME','ORD_VALUE','ORD_NUM_VALUE','SPECIMEN_TYPE']
            if not set(needed)<=set(f.schema_arrow.names):raise BuildError('lab_mapping_columns_missing')
            optional=[n for n in ('SPECIMEN_SOURCE','UNIT','UNITS','REFERENCE_UNIT','RESULT_UNIT','RESULT_UNITS') if n in f.schema_arrow.names]
            for batch in f.iter_batches(columns=needed+optional,batch_size=65536):
                for r in batch.to_pylist():
                    k=r['__patient_key'];component=r['COMPONENT_ID']
                    if k not in anchors or component not in MAP:continue
                    target=MAP[component][0];day=r['__day_RESULT_DATE'];index=anchors[k]['candidate_order_day']
                    if day is None or not 1<=(index-day).days<=90:raise BuildError('mapped_lab_outside_baseline_window')
                    rowqc[src,target,'mapped_id_rows']+=1
                    raw=number(r['ORD_VALUE'] or '');numeric=number(r['ORD_NUM_VALUE'] or '')
                    if raw is not None and numeric is not None and raw!=numeric:rowqc[src,target,'numeric_companion_disagrees_not_used']+=1
                    if r['SPECIMEN_TYPE']!='Blood':rowqc[src,target,'specimen_not_blood_rows']+=1
                    r.update(source=src,day=day,explicit_units={n:r[n] for n in optional if 'UNIT' in n and not missing_kind(r[n] or '')})
                    key=(k,target);old=states.get(key)
                    if old is None or day>old[0]:states[key]=(day,[r])
                    elif day==old[0]:
                        if len(old[1])>=10000:raise BuildError('lab_latest_day_limit')
                        old[1].append(r)
    values={};statuses={};counts=Counter();lineage=[]
    for k,a in anchors.items():
        for target in TARGETS:
            value,status,chosen=select_latest(states.get((k,target),(None,[]))[1])
            values[k,target]=value;statuses[k,target]=status;counts[a['candidate_arm'],target,status]+=1
            for o in chosen:
                lineage.append(dict(patient_key=k,target=target,source=o['source'],source_row=o['__source_row'],result_day=o['day'],result_time=o['RESULT_TIME'],component_id=o['COMPONENT_ID'],specimen_type=o['SPECIMEN_TYPE'],raw_value=o['ORD_VALUE'],status=status))
    if any(digest(p)!=h for p,h in before.items()):raise BuildError('lab_extract_changed_during_mapping')
    schema=pa.schema([('patient_key',pa.string()),('target',pa.string()),('source',pa.string()),('source_row',pa.int64()),('result_day',pa.date32()),('result_time',pa.string()),('component_id',pa.string()),('specimen_type',pa.string()),('raw_value',pa.string()),('status',pa.string())])
    pq.write_table(pa.Table.from_pylist(lineage,schema=schema),output/'restricted_lab_selected_lineage.parquet',compression='zstd')
    report=dict(version=VERSION,identity_basis='Reviewed user-supplied component/name/base-name catalog, 2025 selected sources only. Routine-name blood candidates; no POC, blood gas, fractions, free hemoglobin, HbA1c, urine, ratios or eGFR substituted.',
        component_map={k:dict(target=v[0],component_name=v[1],base_name=v[2]) for k,v in MAP.items()},
        unit_policy='No source unit metadata. Raw ORD_VALUE numeric candidates only; no canonical unit assignment or conversions. ORD_NUM_VALUE is QC only, never a fallback.',
        selection='Latest day then latest valid RESULT_TIME within days1-90; exact numeric ties coalesce, conflicting ties null, no older fallback. All mapped-ID latest-day records considered before specimen/label checks.',
        feature_status_counts=[dict(arm=a,target=t,status=s,patient_keys=n) for (a,t,s),n in sorted(counts.items())],
        record_qc=[dict(source=s,target=t,flag=f,rows=n) for (s,t,f),n in sorted(rowqc.items())],script_sha256=digest(Path(__file__)))
    atomic_json(output/'lab_mapping_report.json',report)
    return values,statuses,report
