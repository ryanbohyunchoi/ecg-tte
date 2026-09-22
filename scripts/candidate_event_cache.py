#!/usr/bin/env python3
"""Reusable exact-patient event cache. All source dates/values retained; no phenotype change."""
import argparse
import json
import os
from pathlib import Path
import time
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest, open_table
from check_comet_runs import check

VERSION='candidate_event_cache_v1'


def filtered_batches(table,keys,columns=None):
    if '__patient_key' not in table.schema.names:raise BuildError('patient_key_absent')
    predicate=ds.field('__patient_key').isin(pa.array(sorted(keys),type=pa.string()))
    return table.scanner(columns=columns,filter=predicate,batch_size=65536,use_threads=False).to_batches()


def open_cached(snapshot,name,cache,required_keys):
    snapshot,cache=Path(snapshot),Path(cache)
    if required_keys is None:raise BuildError('cache_population_required')
    if any(not p.is_absolute() or p.is_symlink() for p in (snapshot,cache)):raise BuildError('absolute_nonsymlink_paths_required')
    m=json.loads((cache/'manifest.json').read_text())
    if m.get('version')!=VERSION or m.get('status')!='complete':raise BuildError('cache_not_complete')
    identity=digest(snapshot/'manifest.json')
    entries=[e for e in m['tables'] if e['source_manifest_sha256']==identity and e['table']==name]
    if len(entries)!=1:raise BuildError('cache_source_not_found_or_changed')
    kp=cache/'restricted_patient_keys.parquet'
    if digest(kp)!=m['patient_keys_sha256']:raise BuildError('cache_keys_changed')
    keys=set(pq.read_table(kp,columns=['patient_key'])['patient_key'].to_pylist())
    if required_keys is not None and not set(required_keys)<=keys:raise BuildError('cache_population_not_superset')
    entry=entries[0];paths=[];rows=0
    for part in entry['parts']:
        path=cache/part['file']
        if path.is_symlink() or cache.resolve() not in path.resolve().parents or digest(path)!=part['sha256']:raise BuildError('cache_part_changed')
        with pq.ParquetFile(path) as f:
            if f.metadata.num_rows!=part['rows']:raise BuildError('cache_rows_changed')
            if [(x.name,str(x.type)) for x in f.schema_arrow]!=[tuple(x) for x in entry['schema']]:raise BuildError('cache_schema_changed')
            rows+=f.metadata.num_rows
        paths.append(str(path))
    if rows!=entry['rows']:raise BuildError('cache_row_total_changed')
    return ds.dataset(paths,format='parquet')


def build_cache(candidate_report,snapshots,output):
    candidate_report,output=Path(candidate_report),Path(output);snapshots=list(map(Path,snapshots))
    if any(not p.is_absolute() or p.is_symlink() for p in (candidate_report,output,*snapshots)):raise BuildError('absolute_nonsymlink_paths_required')
    if not snapshots:raise BuildError('source_snapshots_required')
    if len(set(snapshots))!=len(snapshots):raise BuildError('duplicate_snapshot')
    for source in (candidate_report,*snapshots):
        a,b=output.resolve(),source.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    if check(candidate_report.parent).get('check')!='complete_candidate_artifact_verified':raise BuildError('candidate_not_verified')
    cp=candidate_report/'restricted_candidates.parquet';candidate_hash=digest(cp)
    rawkeys=pq.read_table(cp,columns=['patient_key'])['patient_key'].to_pylist();keys=set(rawkeys)
    if not keys or len(keys)!=len(rawkeys) or any(not isinstance(k,str) or not k for k in keys):raise BuildError('invalid_candidate_keys')
    sources=[]
    for p in snapshots:
        m=json.loads((p/'manifest.json').read_text())
        if m.get('status')!='complete' or m.get('version')!='shared_sources_v1':raise BuildError('source_snapshot_incomplete')
        sources.append((p,digest(p/'manifest.json'),m))
    if len({h for p,h,m in sources})!=len(sources):raise BuildError('duplicate_source_manifest')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700);started=time.monotonic()
    state=dict(version=VERSION,status='building',restricted_until_reviewed=True,candidate_sha256=candidate_hash,
        candidate_report=str(candidate_report),candidate_patient_keys=len(keys),script_sha256=digest(Path(__file__)),tables=[],
        scope='Exact broader-candidate patient filter only. All dates and source columns retained. Warehouse cache, NOT baseline features or outcomes. Clinical windows remain downstream. Source snapshots unchanged.')
    def save():
        state['elapsed_seconds']=round(time.monotonic()-started,3)
        atomic_json(output/'manifest.json',state)
        summary={k:v for k,v in state.items() if k not in ('patient_keys_sha256','tables')}
        summary['tables']=[{k:v for k,v in e.items() if k not in ('parts','schema')} | {'parts':len(e['parts']),'output_bytes':sum(p['bytes'] for p in e['parts'])} for e in state['tables']]
        atomic_json(output/'summary.json',summary)
    pq.write_table(pa.table({'patient_key':sorted(keys)}),output/'restricted_patient_keys.parquet',compression='zstd')
    state['patient_keys_sha256']=digest(output/'restricted_patient_keys.parquet');save()
    try:
        for snapshot,identity,manifest in sources:
            for name,stage in manifest['stages'].items():
                if Path(name).name!=name or name in ('.','..'):raise BuildError('unsafe_table_name')
                print('Filtering '+snapshot.parent.name+'/'+name,flush=True);t0=time.monotonic()
                table=open_table(snapshot,name)
                stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in table.files}
                directory=output/identity/name;directory.mkdir(parents=True,exist_ok=False)
                entry=dict(source_snapshot=str(snapshot),source_manifest_sha256=identity,table=name,
                    source_rows=stage['rows'],rows=0,parts=[],schema=[(f.name,str(f.type)) for f in table.schema])
                writer=None;part_rows=0;part=None;last=time.monotonic()
                def close_part():
                    nonlocal writer,part_rows
                    if writer is None:return
                    writer.close();writer=None
                    entry['parts'].append(dict(file=str(part.relative_to(output)),rows=part_rows,bytes=part.stat().st_size,sha256=digest(part)));part_rows=0
                try:
                    for batch in filtered_batches(table,keys):
                        if batch.num_rows==0:continue
                        if writer is None:
                            part=directory/f"part-{len(entry['parts']):05d}.parquet"
                            writer=pq.ParquetWriter(part,table.schema,compression='zstd')
                        writer.write_batch(batch);part_rows+=batch.num_rows;entry['rows']+=batch.num_rows
                        if part_rows>=524288:close_part()
                        if time.monotonic()-last>=15:
                            print(f"{name}: retained {entry['rows']:,} rows; {time.monotonic()-t0:.0f}s",flush=True);last=time.monotonic()
                    if entry['rows']==0:
                        part=directory/'part-00000.parquet';writer=pq.ParquetWriter(part,table.schema,compression='zstd')
                    close_part()
                finally:
                    if writer is not None:writer.close()
                if any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=v for p,v in stamps.items()):raise BuildError('source_parts_changed')
                entry['elapsed_seconds']=round(time.monotonic()-t0,3);state['tables'].append(entry);save()
                print(f"{name}: {entry['rows']:,} retained / {entry['source_rows']:,} source rows",flush=True)
        if digest(cp)!=candidate_hash or any(digest(p/'manifest.json')!=h for p,h,m in sources):raise BuildError('input_changed')
        state['status']='complete';save()
    except Exception:
        state['status']='failed';save();raise
    return state


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate-report',required=True,type=Path)
    p.add_argument('--source-snapshot',required=True,type=Path,action='append');p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:build_cache(a.candidate_report,a.source_snapshot,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Candidate event cache complete; review summary. No clinical definitions changed.');return 0

if __name__=='__main__':raise SystemExit(main())
