#!/usr/bin/env python3
"""Lossless-value, trial-independent source tables. Run with patient data on H100 only."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import uuid
import fcntl

from inspect_jdat_headers import inspect
from audit_medication_dates import parse
from medication_quality import missing_kind

VERSION = 'shared_sources_v1'
MED_HASH = '61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8'
DX_HASH = 'eee6c9922b68b8f5c95022eff2a9c7b827478195d07167c62343060cb7e75cb4'
MAX_LINE = 1048576
MAX_BATCH_BYTES = 32*1024*1024
ECHO_SCHEMA = [('EchoDate','string'),('ProcedureType','string'),('MRN','string'),
 ('AccessionNumber','string'),('DateOfBirth_echodata','string'),('Age_echodata','double'),
 ('AVStenosis','string'),('AVRegurg','string'),('MVStenosis','string'),
 ('MVRegurgitation','string'),('TVRegurgitation','string'),('TVStenosis','string'),
 ('PVStenosis','string'),('PVRegurgitation','string'),('EF','double')]


class BuildError(Exception):
    """Only static, non-patient diagnostics are used here."""


def atomic_json(path, value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    temp.replace(path)


def fingerprint(path):
    s=path.stat()
    if not path.is_file(): raise BuildError('source_not_regular_file')
    return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,device=s.st_dev,inode=s.st_ino)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()


def default_sources(root, echo):
    return [dict(id='medication_orders',path=str(root/'CarDS_2435227_Meds.txt'),format='literal_tabs',
                 schema_hash=MED_HASH,expected_rows=30929792,key='PAT_MRN_ID',terminal_empty=False,
                 dates=['ORDER_INST','START_DATE','END_DATE','DISCONTINUE_TIME']),
            *[dict(id=source_id,path=str(root/name),format='literal_tabs',schema_hash=DX_HASH,
                 expected_rows=rows,key='PAT_MRN_ID',terminal_empty=True,
                 dates=['CALC_DX_DATE','DX_DTTM','DX_DATE']) for source_id,name,rows in [
                     ('hospital_diagnoses','CarDS_2435227_Hosp_Enc_DX.txt',42763152),
                     ('outpatient_diagnoses','CarDS_2435227_Outpatient_Enc_DX.txt',9633590)]],
            dict(id='echo_studies',path=str(echo),format='parquet',schema_fields=ECHO_SCHEMA,
                 expected_rows=661062,key='MRN',terminal_empty=False,dates=['EchoDate'])]


@lru_cache(maxsize=32768)
def cached_date(value): return parse(value)


def enriched(raw, spec, start, pa, qc):
    # Preserve all source columns, including literal markers and free text.
    data=dict(raw)
    count=len(raw[spec['key']])
    data['__source_id']=[spec['id']]*count
    data['__source_row'] = list(range(start,start+count))
    keys=[]; statuses=[]
    for value in raw[spec['key']]:
        text='' if value is None else value.strip()
        status=missing_kind(text)
        keys.append(None if status else text)
        statuses.append(status or 'nonempty_unvalidated')
        qc['patient_key'][status or 'nonempty_unvalidated']+=1
    data['__patient_key']=keys
    data['__patient_key_status']=statuses
    for field in spec['dates']:
        values=[];formats=[]
        for value in raw[field]:
            text='' if value is None else value
            fmt,day=cached_date(text) if len(text)<=128 else parse(text)
            values.append(day);formats.append(fmt);qc['dates'][field][fmt]+=1
        data['__day_'+field]=pa.array(values,type=pa.date32())
        data['__date_status_'+field]=formats
    return data


def output_schema(raw_schema,spec,pa):
    if any(f.name.startswith('__') for f in raw_schema): raise BuildError('reserved_source_column')
    if len(set(raw_schema.names))!=len(raw_schema): raise BuildError('duplicate_source_columns')
    fields=list(raw_schema)
    fields += [pa.field('__source_id',pa.string()),pa.field('__source_row',pa.int64()),
               pa.field('__patient_key',pa.string()),pa.field('__patient_key_status',pa.string())]
    for name in spec['dates']:
        fields += [pa.field('__day_'+name,pa.date32()),pa.field('__date_status_'+name,pa.string())]
    return pa.schema(fields)


def build_stage(spec, target, batch_rows):
    import pyarrow as pa
    import pyarrow.parquet as pq
    source=Path(spec['path']); before=fingerprint(source); start=time.monotonic()
    target.mkdir(mode=0o700)
    state=dict(source_id=spec['id'],status='building',rows=0,physical_lines=0,terminal_empty_lines=0,
               source_fingerprint=before,parts=[])
    qc={'patient_key':Counter(),'dates':{f:Counter() for f in spec['dates']}}
    writer=None; part_rows=0; writer_path=None
    raw_hash=hashlib.sha256()
    def close_part():
        nonlocal writer,part_rows
        if writer is None:return
        writer.close();writer=None
        with pq.ParquetFile(writer_path) as check:
            if check.metadata.num_rows!=part_rows:raise BuildError('written_row_count_mismatch')
        state['parts'].append(dict(file=writer_path.name,rows=part_rows,bytes=writer_path.stat().st_size,sha256=digest(writer_path)))
        part_rows=0
    def write(raw, schema):
        nonlocal writer,part_rows,writer_path
        n=len(raw[spec['key']])
        if not n:return
        table=pa.Table.from_pydict(enriched(raw,spec,state['rows']+1,pa,qc),schema=schema)
        if writer is None:
            writer_path=target/f"part-{len(state['parts']):05d}.parquet"
            writer=pq.ParquetWriter(writer_path,schema,compression='zstd',use_dictionary=True)
        writer.write_table(table,row_group_size=batch_rows)
        state['rows']+=n;part_rows+=n
        if part_rows>=batch_rows*8:close_part()
        if state['rows']//100000 != (state['rows']-n)//100000:
            elapsed=max(time.monotonic()-start,.001)
            print(f"{spec['id']}: {state['rows']:,} rows; {elapsed/60:.1f} min; {state['rows']/elapsed:,.0f} rows/s",flush=True)
    try:
        if spec['format']=='literal_tabs':
            h=inspect(source.parent,source.name)
            if h.get('status')!='header_candidate' or h.get('delimiter')!='tab':raise BuildError('invalid_header')
            if h['schema_sha256']!=spec['schema_hash']:raise BuildError('schema_mismatch')
            columns=h['columns'];raw_schema=pa.schema([(c,pa.string()) for c in columns])
            schema=output_schema(raw_schema,spec,pa);data={c:[] for c in columns};buffer_bytes=0
            with source.open('rb') as f:
                header=f.readline(65537);raw_hash.update(header)
                for raw in iter(lambda:f.readline(MAX_LINE+1),b''):
                    raw_hash.update(raw);state['physical_lines']+=1
                    if len(raw)>MAX_LINE:raise BuildError('line_exceeds_limit')
                    if b'\x00' in raw:raise BuildError('nul_byte')
                    if raw in (b'\n',b'\r\n') and spec['terminal_empty']:
                        if f.read(1):raise BuildError('nonterminal_empty_line')
                        state['terminal_empty_lines']=1
                        break
                    payload=raw[:-2] if raw.endswith(b'\r\n') else raw[:-1] if raw.endswith(b'\n') else raw
                    cells=payload.decode('utf-8',errors='strict').split('\t')
                    if len(cells)!=len(columns):raise BuildError('row_width_mismatch')
                    for c,v in zip(columns,cells):data[c].append(v)
                    buffer_bytes+=len(raw)
                    if len(data[spec['key']])>=batch_rows or buffer_bytes>=MAX_BATCH_BYTES:
                        write(data,schema);data={c:[] for c in columns};buffer_bytes=0
                write(data,schema)
            state['source_sha256']=raw_hash.hexdigest()
        elif spec['format']=='parquet':
            with pq.ParquetFile(source) as pf:
                raw_schema=pf.schema_arrow
                if [(f.name,str(f.type)) for f in raw_schema]!=[tuple(x) for x in spec['schema_fields']]:raise BuildError('schema_mismatch')
                schema=output_schema(raw_schema,spec,pa)
                for batch in pf.iter_batches(batch_size=batch_rows):write(batch.to_pydict(),schema)
                if state['rows']!=pf.metadata.num_rows:raise BuildError('source_footer_mismatch')
            state['source_sha256']=digest(source)
        else:raise BuildError('unsupported_format')
        close_part()
        if state['rows']!=spec['expected_rows']:raise BuildError('expected_rows_mismatch')
        if fingerprint(source)!=before:raise BuildError('source_changed')
        if sum(p['rows'] for p in state['parts'])!=state['rows']:raise BuildError('parts_count_mismatch')
        state.update(status='complete',qc=qc,elapsed_seconds=round(time.monotonic()-start,3),
                     output_schema=[(f.name,str(f.type)) for f in schema],source_spec=spec)
        atomic_json(target/'manifest.json',state)
        return state
    finally:
        if writer is not None:writer.close()
        cached_date.cache_clear()


def implementation_hash():
    h=hashlib.sha256()
    for name in ('build_shared_tables.py','inspect_jdat_headers.py','audit_medication_dates.py',
                 'medication_quality.py','count_medication_evidence.py','profile_jdat_mapping.py'):
        h.update(name.encode());h.update(Path(__file__).with_name(name).read_bytes())
    return h.hexdigest()


def verify_stage(directory, expected_spec=None, verify_hashes=True):
    import pyarrow.parquet as pq
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('status')!='complete':raise BuildError('stage_incomplete')
    if expected_spec is not None and manifest['source_spec']!=json.loads(json.dumps(expected_spec)):raise BuildError('stage_spec_mismatch')
    total=0;names=[]
    for part in manifest['parts']:
        name=part['file']
        if Path(name).name!=name or not name.endswith('.parquet'):raise BuildError('unsafe_part_path')
        path=directory/name
        if path.is_symlink() or path.stat().st_size!=part['bytes']:raise BuildError('part_changed')
        if verify_hashes and digest(path)!=part['sha256']:raise BuildError('part_hash_mismatch')
        with pq.ParquetFile(path) as pf:
            if pf.metadata.num_rows!=part['rows']:raise BuildError('part_rows_mismatch')
            if [(f.name,str(f.type)) for f in pf.schema_arrow]!=[tuple(x) for x in manifest['output_schema']]:raise BuildError('part_schema_mismatch')
        total+=part['rows'];names.append(name)
    if total!=manifest['rows'] or len(set(names))!=len(names):raise BuildError('stage_rows_mismatch')
    if set(names)!={p.name for p in directory.glob('*.parquet')}:raise BuildError('unexpected_parts')
    return manifest


def summary(output,state,elapsed):
    value=dict(version=VERSION,status=state['status'],restricted_until_reviewed=True,
        elapsed_seconds=round(elapsed,3),clinical_semantics_validated=False,
        tables={k:dict(rows=v['rows'],parts=len(v['parts']),
            physical_lines=v['physical_lines'],terminal_empty_lines=v['terminal_empty_lines'],
            source_sha256=v['source_sha256'],output_bytes=sum(p['bytes'] for p in v['parts']),
            build_elapsed_seconds=v['elapsed_seconds'],qc=v['qc']) for k,v in state['stages'].items()})
    for key in ('failure_stage','error_type','reason'):
        if key in state:value[key]=state[key]
    atomic_json(output/'summary.json',value)


def build(specs, output, resume=False, batch_rows=65536):
    import pyarrow as pa
    started=time.monotonic()
    if batch_rows<1 or batch_rows>65536:raise BuildError('invalid_batch_rows')
    output=Path(output)
    if not output.is_absolute() or output.is_symlink():raise BuildError('absolute_nonsymlink_output_required')
    output=output.resolve()
    ids=[s['id'] for s in specs]
    if len(ids)!=len(set(ids)) or not ids:raise BuildError('invalid_source_ids')
    for s in specs:
        if not s['id'].replace('_','').isalnum():raise BuildError('invalid_source_id')
        path=Path(s['path'])
        if not path.is_absolute() or path.is_symlink():raise BuildError('absolute_nonsymlink_source_required')
        path=path.resolve()
        if output==path.parent or path.parent in output.parents or output in path.parents:raise BuildError('output_source_overlap')
    os.umask(0o077)
    if resume:
        if not output.is_dir():raise BuildError('resume_directory_missing')
    else:output.mkdir(parents=True,mode=0o700,exist_ok=False)
    contract=json.loads(json.dumps(dict(version=VERSION,implementation_sha256=implementation_hash(),
        pyarrow=pa.__version__,python=platform.python_version(),batch_rows=batch_rows,sources=specs)))
    with (output/'.build.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise BuildError('build_already_running')
        manifest_path=output/'manifest.json'
        if resume:
            old=json.loads(manifest_path.read_text())
            if old['contract']!=contract:raise BuildError('incompatible_resume_contract')
        state=dict(version=VERSION,status='building',restricted=True,contract=contract,stages={},
            interpretation='Trial-independent source records; clinical source semantics and identity linkage unvalidated. No cohort filtering or deduplication.')
        atomic_json(manifest_path,state)
        summary(output,state,time.monotonic()-started)
        stage_id='source_preflight'
        try:
            initial={s['id']:fingerprint(Path(s['path'])) for s in specs}
            for spec in specs:
                stage_id=spec['id'];final=output/stage_id;pending=output/('.building-'+stage_id)
                if final.exists():
                    if final.is_symlink():raise BuildError('symlink_stage')
                    print(stage_id+': validating completed stage for reuse',flush=True)
                    stage=verify_stage(final,spec)
                    if stage['source_fingerprint']!=initial[stage_id] or digest(Path(spec['path']))!=stage['source_sha256']:raise BuildError('source_changed_resume')
                    state['stages'][stage_id]=stage
                else:
                    if pending.exists():pending.rename(output/('.incomplete-'+stage_id+'-'+uuid.uuid4().hex))
                    stage=build_stage(spec,pending,batch_rows)
                    pending.rename(final)
                    state['stages'][stage_id]=stage
                atomic_json(manifest_path,state)
                summary(output,state,time.monotonic()-started)
            if any(fingerprint(Path(s['path']))!=initial[s['id']] for s in specs):raise BuildError('source_changed')
            state['status']='complete';atomic_json(manifest_path,state)
            summary(output,state,time.monotonic()-started)
        except Exception as exc:
            state.update(status='failed',failure_stage=stage_id,error_type=type(exc).__name__,
                         reason=str(exc) if isinstance(exc,BuildError) else 'build_failed_no_raw_error_export')
            atomic_json(manifest_path,state)
            summary(output,state,time.monotonic()-started)
            raise
    return state


def open_table(snapshot, source_id, verify_hashes=False):
    """Validated manifest reader for downstream tools; no raw-source scan needed."""
    import pyarrow.dataset as ds
    root=Path(snapshot);m=json.loads((root/'manifest.json').read_text())
    if m.get('status')!='complete' or m.get('version')!=VERSION:raise BuildError('snapshot_not_complete_or_incompatible')
    if source_id not in m['stages']:raise BuildError('unknown_source')
    directory=root/source_id
    if directory.is_symlink():raise BuildError('symlink_stage')
    stage=verify_stage(directory,verify_hashes=verify_hashes)
    if stage!=m['stages'][source_id]:raise BuildError('stage_manifest_mismatch')
    paths=[str(directory/p['file']) for p in stage['parts']]
    if not paths:raise BuildError('empty_table_no_parts')
    return ds.dataset(paths,format='parquet')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--echo',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    try:
        r=build(default_sources(args.root,args.echo),args.output_dir,args.resume)
    except Exception as exc:
        print('Build stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__),flush=True)
        return 1
    print('Shared snapshot complete. Keep all tables and manifests on H100.',flush=True)
    for k,v in r['stages'].items():print(k+': '+str(v['rows'])+' rows',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
