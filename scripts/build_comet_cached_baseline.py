#!/usr/bin/env python3
"""One cache-backed run: expanded-cohort vitals, baseline staging and pre-index labs."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import time
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest
from candidate_event_cache import filtered_batches
from comet_cached_context import CachedContext, LAB_IDS
import extract_comet_vital_candidates as V
import build_comet_baseline_staging as B
from profile_psm_sources import numeric_kind

VERSION='comet_cached_baseline_v1'
LAB_COLUMNS=['__patient_key','__source_row','__day_RESULT_DATE','RESULT_DATE','RESULT_TIME',
    'COMPONENT_ID','COMPONENT_NAME','BASE_NAME','ORD_VALUE','ORD_NUM_VALUE']
LAB_OPTIONAL=['PAT_ENC_CSN_ID','ORDER_PROC_ID','RESULT_LINE','SPECIMEN_TYPE','SPECIMEN_SOURCE',
    'SPECIMN_TAKEN_DATE','SPECIMN_TAKEN_TIME','RESULT_FLAG','UNIT','UNITS','RESULT_UNIT','RESULT_UNITS','REFERENCE_UNIT']


def baseline_lab_batches(table,anchors,columns):
    """Keep only calendar days 1–90 prior, before Python conversion; never index day."""
    keys=pa.array(list(anchors),type=pa.string())
    index=pa.array([r['candidate_order_day'] for r in anchors.values()],type=pa.date32()).cast(pa.int32())
    for batch in filtered_batches(table,anchors,columns):
        positions=pc.index_in(batch.column('__patient_key'),value_set=keys)
        days=batch.column('__day_RESULT_DATE').cast(pa.int32())
        lag=pc.subtract(pc.take(index,positions),days)
        mask=pc.and_(pc.greater_equal(lag,1),pc.less_equal(lag,90))
        yield batch.filter(mask)


def extract_labs(context,output):
    output.mkdir(mode=0o700)
    catalog=Counter();coverage=Counter();tables=[]
    sources=[(context.outpatient_labs,'outpatient_labs')]+[(context.hospital_labs,n) for n in sorted(LAB_IDS)]
    for source,name in sources:
        print('Extracting pre-index labs: '+name,flush=True)
        table=context.open(source,name)
        if not set(LAB_COLUMNS)<=set(table.schema.names):raise BuildError('required_lab_columns_absent')
        columns=LAB_COLUMNS+[c for c in LAB_OPTIONAL if c in table.schema.names]
        schema=pa.schema([table.schema.field(c) for c in columns])
        path=output/(name+'.parquet');count=0;seen=set();start=time.monotonic()
        with pq.ParquetWriter(path,schema,compression='zstd') as writer:
            for batch in baseline_lab_batches(table,context.anchors,columns):
                if not batch.num_rows:continue
                writer.write_batch(batch);count+=batch.num_rows
                # No raw values leave the restricted Parquet extract. Catalog is labels/QC only.
                for r in batch.to_pylist():
                    k=r['__patient_key'];arm=context.anchors[k]['candidate_arm'];seen.add(k)
                    unit=tuple((c,r.get(c)) for c in LAB_OPTIONAL if 'UNIT' in c and c in columns)
                    token=(name,r['COMPONENT_ID'],r['COMPONENT_NAME'],r['BASE_NAME'],r.get('SPECIMEN_TYPE'),r.get('SPECIMEN_SOURCE'),unit,numeric_kind(r['ORD_VALUE'] or ''))
                    if any(len(str(v))>1024 for v in token):raise BuildError('oversized_lab_catalog_label')
                    if token not in catalog and len(catalog)>=20000:raise BuildError('lab_catalog_limit_no_silent_omission')
                    catalog[token]+=1
        for k in seen:coverage[context.anchors[k]['candidate_arm'],name]+=1
        tables.append(dict(source_snapshot=str(source),table=name,rows=count,patient_keys=len(seen),
            file=path.name,sha256=digest(path),output_bytes=path.stat().st_size,elapsed_seconds=round(time.monotonic()-start,3),unit_fields=[c for c in columns if 'UNIT' in c]))
        print(f'{name}: {count:,} pre-index rows saved',flush=True)
    groups=[dict(source=t[0],component_id=t[1],component_name=t[2],base_name=t[3],specimen_type=t[4],specimen_source=t[5],units=dict(t[6]),raw_value_format=t[7],rows=n) for t,n in sorted(catalog.items(),key=lambda x:str(x[0]))]
    atomic_json(output/'restricted_lab_catalog.json',dict(restricted_keep_on_cluster=True,groups=groups))
    result=dict(tables=tables,patients_with_any_preindex_lab=[dict(arm=a,source=n,patient_keys=c) for (a,n),c in sorted(coverage.items())],
        catalog_combinations=len(catalog),catalog_sha256=digest(output/'restricted_lab_catalog.json'),
        interpretation='All components, RESULT_DATE calendar days1-90 before index; no numeric sentinel interpretation, clinical mapping, unit conversion or deduplication across sources. Undated, index-day and future results excluded. Raw values restricted to Parquet. Unit absence is not canonical unit confirmation.')
    atomic_json(output/'manifest.json',result)
    return result


def run(report,cache,output):
    report,cache,output=map(Path,(report,cache,output))
    if not output.is_absolute() or output.is_symlink():raise BuildError('absolute_nonsymlink_output_required')
    context=CachedContext(report,cache)
    for src in (report,cache,*context.source_manifests):
        a,b=output.resolve(),src.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    os.umask(0o077);output.mkdir(parents=True,mode=0o700,exist_ok=False);start=time.monotonic()
    summary=dict(version=VERSION,status='building',counts_valid=False,ready_for_mice=False,restricted_until_reviewed=True,
        cohort_report=str(report),candidate_cache=str(cache),rows=len(context.roster),denominators=context.summary['by_arm'],
        interpretation='Fixed expanded exploratory cohort. Candidate clinical values and recorded evidence, not frozen eligibility or validated model input. No MICE, matching or effect estimation.',
        timing='Strict prior days: diagnoses/encounters/EF365; orders/BP/pulse/labs90; BMI365. Original medication-order index unchanged.',
        lab_mapping='Lab target columns remain null until component/specimen/unit mapping. Restricted pre-index extracts allow mapping without full-source rescan.',
        source_limitations='Hospital labs only 2025 shards1/2; damaged shard3 excluded. Medication snapshot unchanged. Vital unit signatures unverified.')
    atomic_json(output/'summary.json',summary)
    try:
        # Verify every selected cache part once up front and reuse opened tables.
        for entry in context.cache_manifest['tables']:context.open(Path(entry['source_snapshot']),entry['table'])
        print('Cache integrity verified; starting baseline extraction',flush=True)
        stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for t in context.tables.values() for p in t.files}
        V.run(report,context.clinical,output/'vitals',context=context)
        bs=B.run(report,context.clinical,output/'vitals',output/'baseline',context=context)
        labs=extract_labs(context,output/'labs')
        context.check_inputs()
        if any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=s for p,s in stamps.items()):raise BuildError('cached_parts_changed')
        code=['build_comet_cached_baseline.py','comet_cached_context.py','build_comet_baseline_staging.py','extract_comet_vital_candidates.py','candidate_event_cache.py','build_comet_candidates.py','profile_psm_sources.py','medication_quality.py','audit_comet_clinical_baseline.py','audit_comet_eligibility.py']
        atomic_json(output/'manifest.json',dict(version=VERSION,cohort_sha256=context.manifest['output_sha256'],
            input_checksums={str(p):h for p,h in context.fingerprints.items()},
            code_sha256={n:digest(Path(__file__).with_name(n)) for n in code},
            artifact_checksums={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='summary.json'}))
        summary.update(status='complete_cached_baseline_staging',counts_valid=True,covariates=32,
            feature_status_counts=bs['feature_status_counts'],lab_extract=labs,
            next_step='Review lab component/specimen/unit catalog and updated missingness; map the small saved pre-index extracts. Final eligibility, clinical mapping and outcome contract remain separate requirements before MICE/PSM.')
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else type(exc).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def discover(root,pattern,version,status):
    candidates=[]
    for p in Path(root).glob(pattern):
        s=json.loads(p.read_text())
        if s.get('version')==version and s.get('status')==status:candidates.append(p.parent)
    if len(candidates)!=1:raise BuildError('need_exactly_one_compatible_saved_run_or_explicit_path')
    return candidates[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('/mnt/raid0/rbc58/ecg-tte'))
    p.add_argument('--cohort-report',type=Path);p.add_argument('--candidate-cache',type=Path);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:
        cohort=a.cohort_report or discover(a.project_root,'audits/comet-expanded-dx-*/report/summary.json','comet_expanded_dx_reassessment_v1','complete_expanded_dx_reassessment')
        cache=a.candidate_cache or discover(a.project_root,'shared/comet-event-cache-*/cache/summary.json','candidate_event_cache_v1','complete')
        run(cohort,cache,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Completed cached baseline staging. Review summary.json; all patient data remain on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
