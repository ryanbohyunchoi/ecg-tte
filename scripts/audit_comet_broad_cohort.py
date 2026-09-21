#!/usr/bin/env python3
"""Materialize selected broad exploratory candidates and audit prescribing history."""
from collections import Counter
import argparse
import json
import math
import os
from pathlib import Path
import time

from build_shared_tables import BuildError, atomic_json, digest, open_table
from build_comet_candidates import records
from count_comet_hf_variants import discover, echo_state
from check_comet_runs import check

ARMS={'carvedilol_candidate','metoprolol_tartrate_candidate'}


def history_group(prior,undated):
    if prior<0 or undated<0:raise BuildError('invalid_history_count')
    return ('prior_365d_found' if prior else 'no_prior_365d_found')+('_and_undated' if undated else '_no_undated')


def selected(row,state):
    return row['candidate_arm'] in ARMS and (row['DX_DATE_prior_hf_evidence'] or state=='gt1_lt40')


def run(candidate_report,output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    candidate_report,output=Path(candidate_report),Path(output)
    if not candidate_report.is_absolute() or not output.is_absolute() or output.is_symlink():raise BuildError('absolute_paths_required')
    if check(candidate_report.parent).get('check')!='complete_candidate_artifact_verified':raise BuildError('candidate_not_verified')
    m=json.loads((candidate_report/'restricted_manifest.json').read_text());core=Path(m['core_snapshot'])
    if digest(core/'manifest.json')!=m['core_manifest_sha256']:raise BuildError('core_manifest_changed')
    for source in (core.resolve(),candidate_report.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    started=time.monotonic();os.umask(0o077);output.mkdir(parents=True,mode=0o700,exist_ok=False)
    report=dict(version='comet_broad_exploratory_v1',status='building',counts_valid=False,
        restricted_until_reviewed=True,final_eligible_patients=None,
        definition='DX_DATE prior general I50 evidence OR latest strictly prior numeric EF >1 and <40 within365 days. No diastolic/HFpEF exclusions; arm ties excluded.',
        interpretation='User-selected first exploratory population; not validated HFrEF or new users. No clinical protocol freeze, PSM, imputation or effects.',
        history='Prior365-day lexical carvedilol/metoprolol family orders only, not all beta-blockers. Undated records may overlap. No history exclusion applied.',
        candidate_report=str(candidate_report),core_snapshot=str(core))
    atomic_json(output/'summary.json',report)
    try:
        input_path=candidate_report/'restricted_candidates.parquet'
        with pq.ParquetFile(input_path) as pf:
            if pf.metadata.num_rows>1000000:raise BuildError('candidate_limit')
            original=pf.read()
        rows=original.to_pylist();anchors={r['patient_key']:r for r in rows}
        if len(anchors)!=len(rows):raise BuildError('duplicate_candidate_keys')
        table=open_table(core,'echo_studies');stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in table.files}
        echoes={}
        for r in records(table,['__patient_key','__day_EchoDate','EF']):
            key=r['__patient_key'];day=r['__day_EchoDate']
            if key not in anchors or day is None or day>=anchors[key]['candidate_order_day']:continue
            value=r['EF']
            value=('missing' if value is None else 'invalid' if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 1<value<=100 else value)
            old=echoes.get(key)
            if old is None or day>old['day']:echoes[key]=dict(day=day,values={value})
            elif day==old['day']:old['values'].add(value)
        kept=[];by_arm=Counter();history=Counter();calendar=Counter();evidence=Counter()
        for row in rows:
            state=echo_state(echoes.get(row['patient_key']),row['candidate_order_day'])
            if not selected(row,state):continue
            row=dict(row);row['broad_ef_state']=state
            row['broad_history_group']=history_group(row['prior_365d_family_order_records'],row['undated_family_order_records'])
            kept.append(row);arm=row['candidate_arm'];by_arm[arm]+=1
            history[arm,row['broad_history_group']]+=1
            calendar[arm,row['candidate_order_day'].year,row['broad_history_group']]+=1
            basis='both' if row['DX_DATE_prior_hf_evidence'] and state=='gt1_lt40' else 'code_only' if row['DX_DATE_prior_hf_evidence'] else 'ef_only'
            evidence[arm,basis]+=1
        if not kept:raise BuildError('no_broad_candidates')
        schema=original.schema.append(pa.field('broad_ef_state',pa.string())).append(pa.field('broad_history_group',pa.string()))
        pending=output/'restricted_broad_candidates.partial.parquet'
        pq.write_table(pa.Table.from_pylist(kept,schema=schema),pending,compression='zstd')
        if digest(input_path)!=m['candidate_sha256'] or digest(core/'manifest.json')!=m['core_manifest_sha256'] or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=s for p,s in stamps.items()):raise BuildError('input_changed')
        with pq.ParquetFile(pending) as pf:
            if pf.metadata.num_rows!=len(kept):raise BuildError('output_rows_mismatch')
        final=output/'restricted_broad_candidates.parquet';pending.rename(final)
        atomic_json(output/'restricted_manifest.json',dict(version=report['version'],candidate_sha256=m['candidate_sha256'],
            core_manifest_sha256=m['core_manifest_sha256'],output_sha256=digest(final),rows=len(kept),
            script_sha256=digest(Path(__file__)),definition=report['definition'],clinically_validated=False))
        report.update(status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=len(kept),by_arm=dict(by_arm),
            history_groups=[dict(arm=a,group=g,patient_keys=n) for (a,g),n in sorted(history.items())],
            calendar_history_groups=[dict(arm=a,anchor_year=y,group=g,patient_keys=n) for (a,y,g),n in sorted(calendar.items())],
            evidence_groups=[dict(arm=a,basis=b,patient_keys=n) for (a,b),n in sorted(evidence.items())])
    except Exception as exc:
        report.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'audit_failed_no_raw_error_export')
        raise
    finally:
        report['elapsed_seconds']=round(time.monotonic()-started,3);atomic_json(output/'summary.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--candidate-report',type=Path);g.add_argument('--audit-root',type=Path)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:r=run(a.candidate_report or discover(a.audit_root),a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary.json; patient table stays on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
