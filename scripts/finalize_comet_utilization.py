#!/usr/bin/env python3
"""Version the completed v3 staging table with recorded utilization zeros; no raw scan."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import time
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest

FIELDS={'hospital_admissions','ed_encounters','outpatient_visits'}
POLICY='Counts of qualifying dated recorded encounters in days1-365 before index; zero means none recorded, not complete observation. Undated encounters do not enter this dated count. Technical encounter-key/setting conflicts remain null. No MICE on recorded zeros.'


def run(source,output):
    source,output=Path(source),Path(output)
    if not source.is_absolute() or not output.is_absolute() or source.is_symlink() or output.is_symlink():raise BuildError('absolute_nonsymlink_paths_required')
    a,b=source.resolve(),output.resolve()
    if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    start=time.monotonic()
    names=('summary.json','manifest.json','restricted_baseline_staging.parquet','restricted_feature_status.parquet')
    before={n:digest(source/n) for n in names}
    summary=json.loads((source/'summary.json').read_text());manifest=json.loads((source/'manifest.json').read_text())
    if summary.get('version')!='comet_baseline_staging_v3' or summary.get('status')!='complete_baseline_staging' or summary.get('counts_valid') is not True or manifest.get('version')!='comet_baseline_staging_v3':raise BuildError('completed_v3_required')
    for n in names[2:]:
        if manifest.get('outputs',{}).get(n)!=before[n]:raise BuildError('input_checksum_mismatch')
    spec=Path(__file__).resolve().parents[1]/'docs/COMET_PSM_TABLE_V2.json'
    if manifest.get('feature_spec_sha256')!=digest(spec):raise BuildError('feature_spec_mismatch')
    features=[r['name'] for r in json.loads(spec.read_text())['covariates']]
    table=pq.read_table(source/names[2]);st=pq.read_table(source/names[3]);rows=table.to_pylist();states=st.to_pylist()
    if table.column_names!=['patient_key','treatment_arm','index_date',*features] or len(features)!=32 or summary.get('covariates')!=32:raise BuildError('schema_mismatch')
    bykey={r['patient_key']:r for r in rows}
    if len(bykey)!=len(rows) or len(rows)!=summary.get('rows') or not rows:raise BuildError('roster_mismatch')
    seen=set();counts=Counter();old_counts=Counter();changed=Counter()
    for r in states:
        key=(r['patient_key'],r['feature']);f=r['feature']
        if key in seen or key[0] not in bykey or f not in features:raise BuildError('invalid_status_keys')
        seen.add(key);patient=bykey[key[0]];arm=patient['treatment_arm']
        old_counts[arm,f,r['status'],patient[f] is not None]+=1
        if r['status']=='zero_coverage_unvalidated':
            if f not in FIELDS or patient[f] is not None:raise BuildError('invalid_zero_state')
            patient[f]=0.;r['status']='no_qualifying_record';changed[arm,f]+=1
        counts[arm,f,r['status'],patient[f] is not None]+=1
    if len(seen)!=len(rows)*32:raise BuildError('incomplete_status_table')
    expected=Counter({(r['arm'],r['feature'],r['status'],r['has_candidate_value']):r['patient_keys'] for r in summary['feature_status_counts']})
    if old_counts!=expected:raise BuildError('summary_status_mismatch')
    if any(digest(source/n)!=v for n,v in before.items()):raise BuildError('input_changed')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    result=dict(summary,version='comet_baseline_staging_v4',status='building',counts_valid=False,
                source_report=str(source),utilization_policy=POLICY,ready_for_mice=False)
    atomic_json(output/'summary.json',result)
    try:
        pq.write_table(pa.Table.from_pylist(rows,schema=table.schema),output/names[2],compression='zstd')
        pq.write_table(pa.Table.from_pylist(states,schema=st.schema),output/names[3],compression='zstd')
        outmanifest=dict(manifest,version=result['version'],source_report=str(source),parent_checksums=before,
            script_sha256=digest(Path(__file__)),utilization_policy=POLICY,
            outputs={n:digest(output/n) for n in names[2:]})
        # Diagnostic remains in the immutable parent report; do not advertise an absent copy.
        atomic_json(output/'manifest.json',outmanifest)
        result.update(status='complete_baseline_staging',counts_valid=True,
            not_found_policy='Diagnosis/order recorded-evidence policy unchanged. '+POLICY,
            feature_status_counts=[dict(arm=a,feature=f,status=s,has_candidate_value=v,patient_keys=n) for (a,f,s,v),n in sorted(counts.items())],
            recorded_zero_conversions=[dict(arm=a,feature=f,patient_keys=n) for (a,f),n in sorted(changed.items())])
    except Exception:
        result.update(status='failed_counts_invalid',counts_valid=False);raise
    finally:
        result['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-report',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:s=run(a.source_report,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Completed recorded utilization zeros; no imputation or PSM.');print(json.dumps(s['recorded_zero_conversions'],indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
