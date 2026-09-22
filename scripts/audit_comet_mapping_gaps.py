#!/usr/bin/env python3
"""Explain saved baseline technical nulls and inventory four lab-name leads; no remapping."""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import time
import pyarrow.parquet as pq
from build_shared_tables import BuildError, digest, atomic_json
from build_comet_cached_baseline import discover
from comet_cached_context import CachedContext
from build_comet_candidates import records
from build_comet_baseline_staging import DX, tokens, timing, recorded_binary
from medication_quality import missing_kind
from profile_psm_sources import numeric_kind

VERSION='comet_mapping_gaps_v1'
LEADS={'creatinine':r'\b(?:creatinine|creat)\b','potassium':r'\b(?:potassium|k)\b',
       'sodium':r'\b(?:sodium|na)\b','hemoglobin':r'\b(?:hemoglobin|haemoglobin|hgb|hb)\b'}


def lab_leads(name,base):
    text=re.sub(r'[_-]+',' ',((name or '')+' '+(base or '')).lower())
    return {f for f,pattern in LEADS.items() if re.search(pattern,text)}


def code_reason(raw):
    if missing_kind(raw):return 'missing_icd10'
    return 'parseable_icd10' if tokens(raw) is not None else 'unparsed_icd10'


def verify_parent(report):
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'manifest.json').read_text())
    if s.get('version')!='comet_cached_baseline_v1' or m.get('version')!=s['version'] or s.get('status')!='complete_cached_baseline_staging' or s.get('counts_valid') is not True:raise BuildError('completed_cached_baseline_required')
    checked={report/'summary.json':digest(report/'summary.json'),report/'manifest.json':digest(report/'manifest.json')}
    for name,h in m['artifact_checksums'].items():
        path=report/name
        if path.is_symlink() or report.resolve() not in path.resolve().parents or digest(path)!=h:raise BuildError('parent_artifact_changed')
        checked[path]=h
    # Explain exactly the existing parser/prefix contract, not an updated interpretation.
    for name in ('build_comet_baseline_staging.py','medication_quality.py'):
        if digest(Path(__file__).with_name(name))!=m['code_sha256'].get(name):raise BuildError('baseline_interpretation_code_changed')
    return s,m,checked


def checked_records(table,columns,patient_keys):
    stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in table.files}
    yield from records(table,columns,patient_keys=patient_keys)
    if any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=v for p,v in stamps.items()):raise BuildError('cached_part_changed_during_scan')


def explain_dx(context,baseline):
    anchors=context.anchors;positive=defaultdict(set);causes=defaultdict(lambda:defaultdict(set));rowcounts=Counter()
    for snapshot in (context.core,context.dx):
        for name in ('hospital_diagnoses','outpatient_diagnoses'):
            source=snapshot.parent.name+'/'+name;print('Explaining diagnosis nulls: '+source,flush=True)
            table=context.open(snapshot,name)
            for r in checked_records(table,['__patient_key','__day_DX_DATE','CURRENT_ICD10_LIST','CURRENT_ICD9_LIST'],patient_keys=anchors):
                k=r['__patient_key'];when=timing(r['__day_DX_DATE'],anchors[k]['candidate_order_day'])
                if when not in ('prior365','missing_date'):continue
                raw=r['CURRENT_ICD10_LIST'] or '';parsed=tokens(raw)
                kind=code_reason(raw);icd9='icd9_present' if not missing_kind(r['CURRENT_ICD9_LIST'] or '') else 'icd9_missing'
                rowcounts[anchors[k]['candidate_arm'],source,when,kind,icd9]+=1
                flags={f for f,prefixes in DX.items() if parsed and any(c.startswith(prefixes) for c in parsed)}
                if when=='prior365' and parsed is not None:positive[k].update(flags)
                else:
                    blocked=set(DX) if parsed is None else flags
                    reason=when+'__'+kind+'__'+icd9
                    for f in blocked:causes[k][f].add(reason)
    patient_counts=Counter();reason_counts=Counter();mismatches=0
    for k,r in anchors.items():
        for f in DX:
            value,status=recorded_binary(f in positive[k],bool(causes[k][f]))
            if baseline[k][f]!=value:mismatches+=1
            patient_counts[r['candidate_arm'],f,status]+=1
            if value is None:
                for reason in causes[k][f]:reason_counts[r['candidate_arm'],f,reason]+=1
    if mismatches:raise BuildError('diagnosis_reconstruction_differs_from_saved_baseline')
    return dict(reconstruction_matches_saved_values=True,
        reason_counts=[dict(arm=a,feature=f,reason=r,patient_keys=n) for (a,f,r),n in sorted(reason_counts.items())],
        feature_counts=[dict(arm=a,feature=f,status=s,patient_keys=n) for (a,f,s),n in sorted(patient_counts.items())],
        row_counts=[dict(arm=a,source=s,timing=t,icd10_status=c,icd9_status=i,rows=n) for (a,s,t,c,i),n in sorted(rowcounts.items())],
        interpretation='Reasons overlap within patient/feature; do not sum. Nulls reflect the existing all-or-nothing ICD10 parser/date policy. ICD9 presence is a lead for mapping, not a confirmed diagnosis. Positive prior evidence overrides technical blockers. No baseline values changed.')


def review_labs(report,context,output):
    people=defaultdict(set);anylab=defaultdict(set);groups={};labrows=0
    lm=json.loads((report/'labs'/'manifest.json').read_text())
    for entry in lm['tables']:
        path=report/'labs'/entry['file']
        if path.is_symlink() or (report/'labs').resolve() not in path.resolve().parents or digest(path)!=entry['sha256']:raise BuildError('lab_extract_changed')
        source=entry['table'];print('Reviewing small lab extract: '+source,flush=True)
        with pq.ParquetFile(path) as pf:
            if pf.metadata.num_rows!=entry['rows']:raise BuildError('lab_row_count_changed')
            fields=['__patient_key','__day_RESULT_DATE','COMPONENT_ID','COMPONENT_NAME','BASE_NAME','ORD_VALUE']
            optional=[f for f in ('SPECIMEN_TYPE','SPECIMEN_SOURCE','UNIT','UNITS','RESULT_UNIT','RESULT_UNITS','REFERENCE_UNIT') if f in pf.schema_arrow.names]
            for batch in pf.iter_batches(columns=fields+optional,batch_size=65536):
                for r in batch.to_pylist():
                    k=r['__patient_key'];d=r['__day_RESULT_DATE']
                    if k not in context.anchors or d is None or not 1<=(context.anchors[k]['candidate_order_day']-d).days<=90:raise BuildError('lab_extract_outside_baseline_window')
                    arm=context.anchors[k]['candidate_arm'];anylab[arm].add(k);labrows+=1
                    for target in lab_leads(r['COMPONENT_NAME'],r['BASE_NAME']):
                        people[arm,target].add(k)
                        labels=tuple(r.get(f) for f in ('COMPONENT_ID','COMPONENT_NAME','BASE_NAME','SPECIMEN_TYPE','SPECIMEN_SOURCE'))
                        units=tuple((f,r[f]) for f in optional if 'UNIT' in f)
                        token=(source,target,labels,units)
                        if token not in groups:
                            if len(groups)>=10000:raise BuildError('target_catalog_limit')
                            groups[token]=dict(rows=0,people=set(),formats=Counter())
                        g=groups[token];g['rows']+=1;g['people'].add(k);g['formats'][numeric_kind(r['ORD_VALUE'] or '')]+=1
    rows=[]
    for (source,target,labels,units),g in sorted(groups.items(),key=lambda x:str(x[0])):
        rows.append(dict(source=source,target_name_lead=target,component_id=labels[0],component_name=labels[1],base_name=labels[2],specimen_type=labels[3],specimen_source=labels[4],units=dict(units),rows=g['rows'],patient_keys=len(g['people']),raw_value_formats=dict(g['formats'])))
    atomic_json(output/'restricted_target_lab_catalog.json',dict(restricted_keep_on_cluster=True,
        warning='Lexical discovery only. May include urine, ratios, HbA1c, calculated or other non-target tests. Not approved analytes or units. Patient counts overlap across groups.',groups=rows))
    return dict(rows_reviewed=labrows,target_catalog_groups=len(rows),
        any_lab_union=[dict(arm=a,patient_keys=len(v)) for a,v in sorted(anylab.items())],
        name_lead_union=[dict(arm=a,target=f,patient_keys=len(people[a,f])) for a in sorted(context.summary['by_arm']) for f in LEADS],
        interpretation='Exact patient union across saved sources; all labs versus broad target-name leads separately. Name leads are NOT usable numeric analyte coverage. No unit inference, conversion, imputation or baseline overwrite.')


def review_age(context):
    states=defaultdict(set)
    name=next(n for n in context.source_manifests[context.clinical]['stages'] if n.endswith('_patients'))
    for r in checked_records(context.open(context.clinical,name),['__patient_key','__day_BIRTH_DATE'],patient_keys=context.anchors):states[r['__patient_key']].add(r['__day_BIRTH_DATE'])
    counts=Counter()
    for k,row in context.anchors.items():
        births=states[k]
        if not births:kind='no_demographic_match'
        elif len(births)!=1:kind='conflicting_birth_dates'
        elif None in births:kind='unusable_birth_date'
        else:
            b=next(iter(births));i=row['candidate_order_day'];age=i.year-b.year-((i.month,i.day)<(b.month,b.day))
            kind='negative_age' if age<0 else 'over120' if age>120 else 'under18' if age<18 else 'adult_review_range'
        counts[row['candidate_arm'],kind]+=1
    return [dict(arm=a,status=s,patient_keys=n) for (a,s),n in sorted(counts.items())]


def run(report,output):
    report,output=map(Path,(report,output))
    if any(not p.is_absolute() or p.is_symlink() for p in (report,output)):raise BuildError('absolute_nonsymlink_paths_required')
    parent,manifest,checks=verify_parent(report)
    context=CachedContext(parent['cohort_report'],parent['candidate_cache'])
    if manifest['cohort_sha256']!=context.manifest['output_sha256']:raise BuildError('baseline_cohort_mismatch')
    for src in (report,context.cache,context.report,*context.source_manifests):
        a,b=output.resolve(),src.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    rows=pq.read_table(report/'baseline'/'restricted_baseline_staging.parquet').to_pylist();baseline={r['patient_key']:r for r in rows}
    if len(rows)!=len(baseline) or set(baseline)!=set(context.anchors) or any(baseline[k]['index_date']!=r['candidate_order_day'] or baseline[k]['treatment_arm']!=r['candidate_arm'] for k,r in context.anchors.items()):raise BuildError('baseline_anchor_mismatch')
    os.umask(0o077);output.mkdir(parents=True,mode=0o700,exist_ok=False);start=time.monotonic()
    summary=dict(version=VERSION,status='running',counts_valid=False,ready_for_mice=False,restricted_until_reviewed=True,baseline_report=str(report),denominators=context.summary['by_arm'])
    atomic_json(output/'summary.json',summary)
    try:
        summary['laboratory']=review_labs(report,context,output)
        summary['diagnosis']=explain_dx(context,baseline)
        summary['age_review']=review_age(context)
        context.check_inputs()
        if any(digest(p)!=h for p,h in checks.items()):raise BuildError('parent_changed')
        atomic_json(output/'manifest.json',dict(version=VERSION,parent_checksums={str(p):h for p,h in checks.items()},context_checksums={str(p):h for p,h in context.fingerprints.items()},script_sha256=digest(Path(__file__)),target_catalog_sha256=digest(output/'restricted_target_lab_catalog.json')))
        summary.update(status='complete_mapping_gap_audit',counts_valid=True,baseline_changed=False,
            next_step='Review narrowed target lab catalog locally; decide component/specimen/unit mappings. Resolve observed diagnosis blocker causes before any new missingness policy or imputation. No source rebuild needed.')
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else type(exc).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-report',type=Path);p.add_argument('--project-root',type=Path,default=Path('/mnt/raid0/rbc58/ecg-tte'));p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:
        report=a.baseline_report or discover(a.project_root,'audits/comet-cached-baseline-*/report/summary.json','comet_cached_baseline_v1','complete_cached_baseline_staging')
        run(report,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Mapping gap audit complete. Review summary.json and restricted_target_lab_catalog.json locally.');return 0

if __name__=='__main__':raise SystemExit(main())
