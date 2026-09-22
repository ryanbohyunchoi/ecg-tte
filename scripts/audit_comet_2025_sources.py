#!/usr/bin/env python3
"""Fixed-cohort 2025 source feasibility, never cohort mutation or lab normalization."""
import argparse
from collections import Counter,defaultdict
import os
from pathlib import Path
import pyarrow.parquet as pq
from audit_comet_beta_history import verify
from build_shared_tables import open_table, digest, atomic_json, BuildError
from build_comet_candidates import records
from count_comet_hf_variants import dx_flags
from medication_quality import missing_kind


def run(cohort,dx,lab,clinical,output):
    cohort,dx,lab,clinical,output=map(Path,(cohort,dx,lab,clinical,output))
    if any(not p.is_absolute() or p.is_symlink() for p in (cohort,dx,lab,clinical,output)):raise BuildError('explicit_paths_required')
    for src in (cohort,dx,lab,clinical):
        a,b=output.resolve(),src.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    _,cm=verify(cohort);cp=cohort/'restricted_broad_candidates.parquet'
    roster=pq.read_table(cp,columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
    anchors={r['patient_key']:r for r in roster}
    if len(anchors)!=len(roster):raise BuildError('duplicate_roster_key')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    s=dict(version='comet_2025_source_audit_v1',status='running',counts_valid=False,restricted_until_reviewed=True,
        interpretation='Fixed-cohort source feasibility. Lab source limited to2025outpatient; no clinical lab mapping, imputation, cohort exclusions or HF predictor reinstatement.')
    atomic_json(output/'summary.json',s)
    try:
        hashes={str(p/'manifest.json'):digest(p/'manifest.json') for p in (dx,lab,clinical)};stamps={}
        def scan(snapshot,name,cols):
            t=open_table(snapshot,name)
            for f in t.files:stamps[str(f)]=(Path(f).stat().st_size,Path(f).stat().st_mtime_ns)
            return records(t,cols,patient_keys=anchors)
        def prior(k,d,w):return k in anchors and d is not None and 1<=(anchors[k]['candidate_order_day']-d).days<=w
        enc=defaultdict(set);owners=defaultdict(set)
        for r in scan(clinical,'Data_2025_04_03_hosp_enc',['__patient_key','PAT_ENC_CSN_ID','__day_HOSP_ADMSN_DATE','INP_YN','ED_YN']):
            k=r['__patient_key'];d=r['__day_HOSP_ADMSN_DATE'];csn=r['PAT_ENC_CSN_ID'] or ''
            if prior(k,d,365) and not missing_kind(csn):enc[k,csn.strip()].add((d,r['INP_YN'],r['ED_YN']));owners[csn.strip()].add(k)
        valid={key for key,v in enc.items() if len(v)==1 and len(owners[key[1]])==1 and next(iter(v))[1]=='1' and next(iter(v))[2] in ('0','1')}
        people=defaultdict(set);linked=defaultdict(set);denom=Counter(r['candidate_arm'] for r in roster)
        def mark(k,source,flag):people[anchors[k]['candidate_arm'],source,flag].add(k)
        for name in ('hospital_diagnoses','outpatient_diagnoses'):
            for r in scan(dx,name,['__patient_key','PAT_ENC_CSN_ID','__day_DX_DATE','CURRENT_ICD10_LIST','DX_NAME']):
                k=r['__patient_key']
                if k not in anchors:continue
                csn=r['PAT_ENC_CSN_ID'] or '';key=(k,csn.strip())
                if key in valid:linked[anchors[k]['candidate_arm'],name].add(key)
                d=r['__day_DX_DATE']
                if d is None:mark(k,name,'any_undated_diagnosis')
                if d is None or d>=anchors[k]['candidate_order_day']:continue
                flags=dx_flags(r['CURRENT_ICD10_LIST'] or '',r['DX_NAME'] or '')
                if flags & {'isolated_diastolic','combined','hfpef_mention','diastolic_mention'}:mark(k,'diagnoses_union','any_prior_exclusion_signal')
                if not prior(k,d,365):continue
                mark(k,name,'any_prior365_diagnosis')
                for f in flags:mark(k,name,'prior365_'+f)
                if flags & {'isolated_diastolic','combined','hfpef_mention','diastolic_mention'}:mark(k,'diagnoses_union','prior365_exclusion_signal')
        catalog=Counter();omitted=0
        for r in scan(lab,'outpatient_labs',['__patient_key','__day_RESULT_DATE','COMPONENT_ID','COMPONENT_NAME','BASE_NAME']):
            k=r['__patient_key'];d=r['__day_RESULT_DATE']
            if k not in anchors:continue
            if d is None:mark(k,'outpatient_labs','any_missing_result_date')
            if not prior(k,d,90):continue
            mark(k,'outpatient_labs','any_prior90_result_dated_record')
            values=tuple(r[n] or '' for n in ('COMPONENT_ID','COMPONENT_NAME','BASE_NAME'))
            if any(len(v)>256 for v in values) or (values not in catalog and len(catalog)>=2000):omitted+=1
            else:catalog[values]+=1
        if digest(cp)!=cm['output_sha256'] or any(digest(Path(p))!=h for p,h in hashes.items()) or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=v for p,v in stamps.items()):raise BuildError('source_changed')
        s.update(status='complete_fixed_cohort_feasibility',counts_valid=True,denominators=denom,
            patients=[dict(arm=a,source=src,flag=f,patient_keys=len(v)) for (a,src,f),v in sorted(people.items())],
            inpatient_linkage=[dict(arm=a,diagnosis_source=src,inpatient_keys=sum(anchors[k]['candidate_arm']==a for k,c in valid),keys_matching_any_diagnosis=len(linked[a,src])) for a in sorted(denom) for src in ('hospital_diagnoses','outpatient_diagnoses')],
            lab_catalog_combinations=len(catalog),lab_catalog_omitted_records=omitted,
            timing='DX_DATEprior365; labs RESULT_DATEprior90; calendar days only. Lab clinical/availability semantics unverified. Absent aggregate flags mean zero; flags/sources overlap.',
            cohort_sha256=cm['output_sha256'],source_manifest_sha256=hashes,script_sha256=digest(Path(__file__)))
        atomic_json(output/'restricted_lab_catalog.json',dict(restricted_keep_on_cluster=True,fields=['COMPONENT_ID','COMPONENT_NAME','BASE_NAME'],groups=[dict(values=list(v),records=n) for v,n in sorted(catalog.items())]))
    except Exception:
        s.update(status='failed_counts_invalid',counts_valid=False);raise
    finally:atomic_json(output/'summary.json',s)
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('cohort-report','dx-snapshot','lab-snapshot','clinical-snapshot','output-dir'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:run(a.cohort_report,a.dx_snapshot,a.lab_snapshot,a.clinical_snapshot,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Fixed-cohort feasibility complete; review summary locally.');return 0

if __name__=='__main__':raise SystemExit(main())
