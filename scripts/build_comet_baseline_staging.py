#!/usr/bin/env python3
"""Assemble declared COMET baseline columns with explicit candidate/blocked status."""
import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import math
import os
from pathlib import Path
import re
import time
import pyarrow as pa
import pyarrow.parquet as pq
from audit_comet_beta_history import verify, NAMES
from audit_comet_clinical_baseline import IDS, age_state
from audit_comet_eligibility import ACE
from build_comet_candidates import records
from build_shared_tables import BuildError, open_table, digest, atomic_json
from hf_joint_evidence import evidence
from medication_quality import missing_kind

# Explicit discovery vocabulary, not validated clinical phenotypes or complete drug maps.
DX={
 'ischemic_heart_disease_or_mi':('I20','I21','I22','I23','I24','I25'),
 'atrial_fibrillation':('I48',), 'hypertension':('I10','I11','I12','I13','I15'),
 'diabetes':('E08','E09','E10','E11','E13'), 'ckd':('N18',),
 'stroke_history':('I60','I61','I62','I63','I64','I69'),
 'copd_or_asthma':('J44','J45','J46'), 'peripheral_arterial_disease':('I702','I739'),
 'valve_disease':('I05','I06','I07','I08','I34','I35','I36','I37')}
DRUG={
 'ace_inhibitor_order':ACE,
 'arb_order':set('losartan valsartan candesartan irbesartan olmesartan telmisartan eprosartan azilsartan'.split()),
 'mra_order':{'spironolactone','eplerenone','finerenone'},
 'loop_diuretic_order':{'furosemide','bumetanide','torsemide','torasemide','ethacrynic'},
 'sglt2_inhibitor_order':{'dapagliflozin','empagliflozin','canagliflozin','ertugliflozin','bexagliflozin','sotagliflozin'},
 'digoxin_order':{'digoxin'}, 'amiodarone_order':{'amiodarone'}}
LABS={'creatinine','potassium','sodium','hemoglobin'}


def tokens(cell):
    if len(cell)>4096:raise BuildError('oversized_code_cell')
    if missing_kind(cell):return None
    parts=[x.strip().upper() for x in re.split('[,;|]',cell)]
    if not all(re.fullmatch(r'[A-Z][0-9][A-Z0-9](?:\.?[A-Z0-9]{1,4})?',x) for x in parts):return None
    return {x.replace('.','') for x in parts}


def drug_flags(names):
    if any(len(x)>4096 for x in names):raise BuildError('oversized_drug_name')
    words=set(re.findall('[a-z]+',' '.join(names).lower()))
    found={k for k,v in DRUG.items() if words&v}
    if {'sacubitril','valsartan'}<=words:
        found.add('arni_order');found.discard('arb_order')
    return found


def discover_vitals(root):
    candidates=[]
    for p in Path(root).glob('*/report/summary.json'):
        if not p.parent.parent.name.startswith('comet-vital'):continue
        s=json.loads(p.read_text())
        if s.get('version')=='comet_vital_candidates_v2' and s.get('status')=='complete_candidate_extraction' and s.get('counts_valid') is True:candidates.append(p.parent)
    if len(candidates)!=1:raise BuildError('need_one_v2_vital_run_or_explicit_path')
    return candidates[0]


def run(cohort_report,clinical,vital_report,output):
    cohort_report,clinical,vital_report,output=map(Path,(cohort_report,clinical,vital_report,output))
    if not all(p.is_absolute() for p in (cohort_report,clinical,vital_report,output)) or any(p.is_symlink() for p in (clinical,vital_report,output)):raise BuildError('absolute_nonsymlink_paths_required')
    cs,cm=verify(cohort_report);core=Path(cs['core_snapshot']);clinical_hash=digest(clinical/'manifest.json')
    cmanifest=json.loads((clinical/'manifest.json').read_text())
    if cmanifest.get('status')!='complete' or set(cmanifest.get('stages',{}))!=IDS:raise BuildError('clinical_snapshot_not_complete')
    vm=json.loads((vital_report/'manifest.json').read_text());vs=json.loads((vital_report/'summary.json').read_text());vp=vital_report/'restricted_vital_candidates.parquet'
    if vm.get('version')!='comet_vital_candidates_v2' or vs.get('status')!='complete_candidate_extraction' or vs.get('counts_valid') is not True or vm.get('cohort_sha256')!=cm['output_sha256'] or vm.get('clinical_manifest_sha256')!=clinical_hash or digest(vp)!=vm.get('output_sha256'):raise BuildError('incompatible_vital_artifact')
    for src in (cohort_report,core,clinical,vital_report):
        a,b=output.resolve(),src.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    cp=cohort_report/'restricted_broad_candidates.parquet'
    with pq.ParquetFile(cp) as f:
        if not 0<f.metadata.num_rows<=1000000:raise BuildError('cohort_limit')
        cohort=f.read(columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
    anchors={r['patient_key']:r for r in cohort}
    if len(anchors)!=len(cohort) or any(not r['patient_key'] or not isinstance(r['candidate_order_day'],date) for r in cohort):raise BuildError('invalid_cohort')
    vr=pq.read_table(vp).to_pylist();vitals={r['patient_key']:r for r in vr}
    if len(vitals)!=len(vr) or set(vitals)!=set(anchors) or any(vitals[k]['index_date']!=r['candidate_order_day'] or vitals[k]['arm']!=r['candidate_arm'] for k,r in anchors.items()):raise BuildError('vital_cohort_alignment_failed')
    definition=Path(__file__).resolve().parents[1]/'docs/COMET_PSM_TABLE_V1.json';spec=json.loads(definition.read_text());features=[r['name'] for r in spec['covariates']]
    if len(features)!=33 or len(set(features))!=33:raise BuildError('feature_contract_changed')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700);start=time.monotonic()
    summary=dict(version='comet_baseline_staging_v1',status='building',counts_valid=False,ready_for_mice=False,restricted_until_reviewed=True,
        interpretation='33-column fixed-roster candidate staging, not validated clinical baseline. Code/name leads and encounter-flag counts are provisional. No cohort exclusions, imputation or PSM.',
        blocker='Lab source unavailable; units/availability/identity and clinical mappings unresolved; eligibility/index not frozen.',
        clinical_snapshot=str(clinical),cohort_report=str(cohort_report),vital_report=str(vital_report))
    atomic_json(output/'summary.json',summary)
    try:
        stamps={};births=defaultdict(set);sexes=defaultdict(set);echoes={};dx=defaultdict(set);rx=defaultdict(set);bad_dx=Counter();undated=Counter();enc={};hfkeys=set();linked=set()
        def scan(snapshot,name,cols):
            t=open_table(snapshot,name);stamps.update({p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in t.files})
            return records(t,cols)
        def in_window(key,day,w):return key in anchors and day is not None and 1<=(anchors[key]['candidate_order_day']-day).days<=w
        patients=next(n for n in IDS if n.endswith('_patients'))
        print('Extracting demographics',flush=True)
        for r in scan(clinical,patients,['__patient_key','__day_BIRTH_DATE','SEX_C','SEX']):
            k=r['__patient_key']
            if k not in anchors:continue
            linked.add(k);births[k].add(r['__day_BIRTH_DATE']);sexes[k].add((r['SEX_C'],r['SEX']))
        print('Extracting echo candidates',flush=True)
        for r in scan(core,'echo_studies',['__patient_key','__day_EchoDate','EF']):
            k=r['__patient_key'];d=r['__day_EchoDate']
            if not in_window(k,d,365):continue
            v=r['EF'];v=v if not isinstance(v,bool) and isinstance(v,(float,int)) and math.isfinite(v) and 1<v<=100 else None
            if k not in echoes or d>echoes[k][0]:echoes[k]=(d,{v})
            elif d==echoes[k][0]:echoes[k][1].add(v)
        for name in ('hospital_diagnoses','outpatient_diagnoses'):
            print('Extracting recorded diagnosis leads: '+name,flush=True)
            for r in scan(core,name,['__patient_key','__day_DX_DATE','CURRENT_ICD10_LIST','PAT_ENC_CSN_ID']):
                k=r['__patient_key'];d=r['__day_DX_DATE']
                if not in_window(k,d,365):continue
                codes=tokens(r['CURRENT_ICD10_LIST'] or '')
                if codes is None:bad_dx[k]+=1;continue
                dx[k].update(f for f,prefixes in DX.items() if any(c.startswith(prefixes) for c in codes))
                csn=r['PAT_ENC_CSN_ID'] or ''
                if not missing_kind(csn) and evidence(r['CURRENT_ICD10_LIST'] or '')[0]:hfkeys.add((k,csn.strip()))
        print('Extracting prior medication-name leads',flush=True)
        for r in scan(core,'medication_orders',['__patient_key','__day_ORDER_INST',*NAMES]):
            k=r['__patient_key'];d=r['__day_ORDER_INST']
            if k not in anchors:continue
            if d is None:undated[k]+=1;continue
            if in_window(k,d,90):rx[k].update(drug_flags(tuple(r[n] or '' for n in NAMES)))
        bad_enc=Counter()
        for name in sorted(n for n in IDS if n.endswith('_hosp_enc') or n.endswith('_outpatient_enc')):
            hospital=name.endswith('_hosp_enc');field='__day_HOSP_ADMSN_DATE' if hospital else '__day_CONTACT_DATE'
            print('Extracting encounter-key candidates: '+name,flush=True)
            for r in scan(clinical,name,['__patient_key','PAT_ENC_CSN_ID',field]+(['ED_YN','INP_YN'] if hospital else [])):
                k=r['__patient_key'];d=r[field]
                if not in_window(k,d,365):continue
                csn=r['PAT_ENC_CSN_ID'] or ''
                if missing_kind(csn):bad_enc[k]+=1;continue
                token=(k,csn.strip())
                if len(enc)>=2000000 and token not in enc:raise BuildError('encounter_key_limit')
                enc.setdefault(token,set()).add((d,'hospital_source' if hospital else 'outpatient_source',r.get('ED_YN'),r.get('INP_YN')))
        utilization=defaultdict(Counter);key_patients=defaultdict(set)
        for (k,csn),values in enc.items():key_patients[csn].add(k)
        for (k,csn),values in enc.items():
            if len(values)!=1 or len(key_patients[csn])!=1:bad_enc[k]+=1;continue
            _,kind,ed,inp=next(iter(values))
            if kind=='outpatient_source':utilization[k]['outpatient_visits']+=1
            elif ed in ('0','1') and inp in ('0','1'):
                utilization[k]['ed_encounters']+=ed=='1';utilization[k]['hospital_admissions']+=inp=='1'
                utilization[k]['hf_hospital_admissions']+=inp=='1' and (k,csn) in hfkeys
            else:bad_enc[k]+=1
        output_rows=[];states=[];counts=Counter()
        for k,r in anchors.items():
            values={f:None for f in features};status={f:'not_extracted' for f in features}
            def put(f,v,st):values[f]=v;status[f]=st
            st,age=age_state(births[k],r['candidate_order_day']);put('age_at_index',age,'candidate_demographic' if age is not None else st)
            pair=next(iter(sexes[k])) if len(sexes[k])==1 else None
            sex={'1':'Female','2':'Male'}.get(pair[0]) if pair else None
            put('recorded_sex',sex if pair and pair[1]==sex else None,'candidate_demographic' if sex and pair[1]==sex else 'sex_missing_or_conflict')
            put('index_year',r['candidate_order_day'].year,'derived_from_provisional_index')
            e=echoes.get(k);ev=next(iter(e[1])) if e and len(e[1])==1 else None
            put('lvef',ev,'candidate_units_availability_unverified' if ev is not None else 'no_usable_latest_echo')
            for field,feature,valuefield in [('sbp','bp','bp_first_candidate'),('dbp','bp','bp_second_candidate'),('heart_rate','pulse','pulse_candidate'),('bmi','bmi','bmi_candidate')]:
                # Names are declared target slots; interpretation remains blocked in companion status.
                put(field,vitals[k][valuefield],vitals[k][feature+'_status'])
            for f in LABS:put(f,None,'blocked_lab_source')
            for f in DX:put(f,1 if f in dx[k] else None,'candidate_positive_code_lead' if f in dx[k] else 'negative_ascertainment_unvalidated')
            for f in (*DRUG,'arni_order'):put(f,1 if f in rx[k] else None,'candidate_positive_name_lead' if f in rx[k] else 'negative_ascertainment_unvalidated')
            for f in ('outpatient_visits','ed_encounters','hospital_admissions','hf_hospital_admissions'):
                n=utilization[k][f];put(f,None if bad_enc[k] or n==0 else n,'encounter_key_conflict' if bad_enc[k] else 'candidate_setting_count' if n else 'zero_coverage_unvalidated')
            output_rows.append(dict(patient_key=k,treatment_arm=r['candidate_arm'],index_date=r['candidate_order_day'],**values))
            for f in features:
                counts[r['candidate_arm'],f,status[f],values[f] is not None]+=1
                states.append(dict(patient_key=k,feature=f,status=status[f]))
        if digest(cp)!=cm['output_sha256'] or digest(core/'manifest.json')!=cm['core_manifest_sha256'] or digest(clinical/'manifest.json')!=clinical_hash or digest(vp)!=vm['output_sha256'] or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=v for p,v in stamps.items()):raise BuildError('input_changed')
        schema=pa.schema([('patient_key',pa.string()),('treatment_arm',pa.string()),('index_date',pa.date32())]+[(f,pa.string() if f=='recorded_sex' else pa.float64()) for f in features])
        pq.write_table(pa.Table.from_pylist(output_rows,schema=schema),output/'restricted_baseline_staging.parquet',compression='zstd')
        pq.write_table(pa.Table.from_pylist(states),output/'restricted_feature_status.parquet',compression='zstd')
        atomic_json(output/'manifest.json',dict(version=summary['version'],ready_for_mice=False,cohort_sha256=cm['output_sha256'],core_manifest_sha256=cm['core_manifest_sha256'],clinical_manifest_sha256=clinical_hash,
            vital_output_sha256=vm['output_sha256'],feature_spec_sha256=digest(definition),script_sha256=digest(Path(__file__)),
            candidate_dx_prefixes=DX,candidate_drug_names={k:sorted(v) for k,v in DRUG.items()},
            outputs={n:digest(output/n) for n in ('restricted_baseline_staging.parquet','restricted_feature_status.parquet')}))
        summary.update(status='complete_baseline_staging',counts_valid=True,rows=len(cohort),covariates=33,
            feature_status_counts=[dict(arm=a,feature=f,status=s,has_candidate_value=v,patient_keys=n) for (a,f,s,v),n in sorted(counts.items())],
            qc=dict(patients_with_unparsed_prior_dx=len(bad_dx),patients_with_undated_orders=len(undated),patients_with_encounter_key_problems=len(bad_enc)),
            not_found_policy='Absent code/name leads and zero-utilization evidence remain null with blocking states; not ordinary MICE missingness. No assumption of complete observation.',
            vital_policy='sbp/dbp are provisional first/second BP target slots, not a claim of verified orientation or units. All vital values remain blocked for MICE.')
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'build_failed_no_raw_error_export');raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('cohort-report','clinical-snapshot','output-dir'):p.add_argument('--'+n,required=True,type=Path)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--vital-report',type=Path);g.add_argument('--audit-root',type=Path);a=p.parse_args()
    try:r=run(a.cohort_report,a.clinical_snapshot,a.vital_report or discover_vitals(a.audit_root),a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary; staging is not MICE-ready.');return 0

if __name__=='__main__':raise SystemExit(main())
