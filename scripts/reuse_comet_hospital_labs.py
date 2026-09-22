#!/usr/bin/env python3
"""Copy and verify two completed lab stages into an explicitly limited new snapshot."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import pyarrow as pa
from build_shared_tables import BuildError, VERSION, atomic_json, build, digest, implementation_hash, verify_stage
IDS=('Data_2025_04_03_hosp_enc_labs_1','Data_2025_04_03_hosp_enc_labs_2')


def run(source,output):
    source,output=Path(source),Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (source,output)):raise BuildError('absolute_nonsymlink_paths_required')
    a,b=source.resolve(),output.resolve()
    if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    original_hash=digest(source/'manifest.json');old=json.loads((source/'manifest.json').read_text())
    if old.get('version')!=VERSION or old.get('status')!='failed':raise BuildError('expected_failed_parent_snapshot')
    specs=[];stages={}
    for name in IDS:
        directory=source/name
        if directory.is_symlink():raise BuildError('symlink_stage')
        stage=verify_stage(directory,verify_hashes=True)
        if old.get('stages',{}).get(name)!=stage:raise BuildError('parent_stage_mismatch')
        spec=stage['source_spec'];expected='CarDS_2435227_Hosp_Enc_Labs_'+name[-1]+'.txt'
        if spec['id']!=name or Path(spec['path']).name!=expected or Path(spec['path']).parent.name!='Data-2025-04-03':raise BuildError('unexpected_lab_source')
        stages[name]=stage;specs.append(spec)
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    contract=dict(version=VERSION,implementation_sha256=implementation_hash(),pyarrow=pa.__version__,python=platform.python_version(),batch_rows=65536,sources=specs)
    atomic_json(output/'manifest.json',dict(version=VERSION,status='building',contract=contract,stages={}))
    try:
        for name,stage in stages.items():
            dest=output/name;dest.mkdir(mode=0o700)
            for part in stage['parts']:shutil.copyfile(source/name/part['file'],dest/part['file'])
            atomic_json(dest/'manifest.json',stage)
        if digest(source/'manifest.json')!=original_hash:raise BuildError('parent_changed')
        # Existing engine rechecks copied hashes/schema/row counts AND raw file hashes.
        result=build(specs,output,resume=True)
        if digest(source/'manifest.json')!=original_hash:raise BuildError('parent_changed')
        provenance=dict(version='limited_hospital_labs_v1',parent_manifest_sha256=original_hash,parent_snapshot=str(source),
            selected_stages=list(IDS),excluded='Hospital shard3 and all other sources. Complete means selected two shards only, not complete lab capture.',
            method='Independent copies; output and raw source checksums verified. Parent unchanged.',script_sha256=digest(Path(__file__)))
        result['limited_reuse']=provenance;atomic_json(output/'manifest.json',result)
        summary=json.loads((output/'summary.json').read_text());summary['limited_reuse']=provenance;atomic_json(output/'summary.json',summary)
        return result
    except Exception:
        state=json.loads((output/'manifest.json').read_text());state['status']='failed';atomic_json(output/'manifest.json',state)
        atomic_json(output/'summary.json',dict(version=VERSION,status='failed',reason='limited_reuse_failed',counts_valid=False));raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-snapshot',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    try:run(a.source_snapshot,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Verified limited two-shard lab snapshot complete. No clinical extraction or imputation.');return 0

if __name__=='__main__':raise SystemExit(main())
