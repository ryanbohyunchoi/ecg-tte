#!/usr/bin/env python3
"""Run the pinned frozen BCL smoke test; keep raw logs and vectors on H100."""
import argparse
import contextlib
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from build_shared_tables import BuildError, atomic_json, digest
from check_comet_bcl_assets import CHECKPOINT

PIN='d359c04d1f5e6c810f76751777535918870704b7'


def read_csv(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def validate_vectors(directory,ids,shard_size=32):
    import numpy as np
    config=json.loads((directory/'embedding_config.json').read_text())
    names=[f'shard_{i:05d}' for i in range((len(ids)+shard_size-1)//shard_size)]
    if {p.stem for p in directory.glob('shard_*.npy')}!=set(names):raise BuildError('missing_or_extra_shards')
    if {p.name for p in directory.glob('shard_*_index.csv')}!={n+'_index.csv' for n in names}:raise BuildError('missing_or_extra_indices')
    result=dict(rows=len(ids),dimensions=int(config['embed_dim']),load_error_rows=0,nonfinite_rows=0,zero_vector_rows=0)
    if config['num_rows']!=len(ids):raise BuildError('output_config_mismatch')
    for i,name in enumerate(names):
        a=np.load(directory/(name+'.npy'),allow_pickle=False)
        rows=read_csv(directory/(name+'_index.csv'));lo=i*shard_size;hi=min(lo+shard_size,len(ids))
        if [r['fileID'] for r in rows]!=ids[lo:hi] or [int(r['row']) for r in rows]!=list(range(lo,hi)):raise BuildError('output_identity_or_order_mismatch')
        if a.ndim!=2 or a.shape!=(hi-lo,result['dimensions']) or a.shape[1]<1 or a.dtype!=np.float32:raise BuildError('invalid_vector_shape_or_dtype')
        result['load_error_rows']+=sum(bool(r['error']) for r in rows)
        result['nonfinite_rows']+=int((~np.isfinite(a).all(axis=1)).sum())
        result['zero_vector_rows']+=int((~np.any(a!=0,axis=1)).sum())
    return result


def run(prep,upstream,out,reference_smoke=None):
    full=reference_smoke is not None
    shard_size=512 if full else 32
    for p in (prep,upstream,out):
        if not p.is_absolute() or p.is_symlink():raise BuildError('absolute_nonsymlink_paths_required')
    for p in (prep,upstream):
        if out.resolve()==p.resolve() or out.resolve() in p.resolve().parents or p.resolve() in out.resolve().parents:raise BuildError('output_overlap')
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    summary=dict(version='comet_bcl_full_v1' if full else 'comet_bcl_smoke_v1',status='running',counts_valid=False,restricted_until_reviewed=True,ready_for_matching=False)
    try:
        rev=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
        dirty=subprocess.check_output(['git','-C',str(upstream),'status','--porcelain','--untracked-files=no'],stderr=subprocess.DEVNULL,text=True)
        if rev!=PIN or dirty:raise BuildError('upstream_pin_or_cleanliness_mismatch')
        # No untracked Python modules may shadow the reviewed source.
        extra=subprocess.check_output(['git','-C',str(upstream),'ls-files','--others','--exclude-standard'],stderr=subprocess.DEVNULL,text=True)
        if any(n.endswith('.py') for n in extra.splitlines()):raise BuildError('untracked_upstream_python')
        s=json.loads((prep/'summary.json').read_text());m=json.loads((prep/'manifest.json').read_text())
        if s.get('status')!=('complete_full_inputs' if full else 'complete_smoke_inputs') or s.get('rows',0)<1 or (not full and s['rows']>32):raise BuildError('matching_input_contract_required')
        hashes={str(prep/n):digest(prep/n) for n in ('restricted_input.csv','restricted_formats.csv')}
        if any(m['outputs'].get(Path(p).name)!=h for p,h in hashes.items()):raise BuildError('smoke_input_changed')
        ids=[r['fileID'] for r in read_csv(prep/'restricted_input.csv')]
        formats=read_csv(prep/'restricted_formats.csv')
        if len(ids)!=s['rows'] or len(set(ids))!=len(ids) or [r['fileID'] for r in formats]!=ids:raise BuildError('input_catalog_mismatch')
        root=Path(m['waveform_root'])
        wave_stamps={}
        for fid in ids:
            if fid.startswith('/') or any(v in ('','.','..') for v in fid.split('/')) or '\\' in fid:raise BuildError('unsafe_relative_id')
            p=root/(fid+'.npy')
            if root.resolve() not in p.resolve().parents or any(v.is_symlink() for v in (p,*p.parents) if v==root or root in v.parents):raise BuildError('unsafe_waveform_path')
            st=p.stat();wave_stamps[p]=(st.st_size,st.st_mtime_ns)
        checkpoint=Path(CHECKPOINT);checkpoint_hash=digest(checkpoint)
        reference=None
        if full:
            reference=json.loads((reference_smoke/'summary.json').read_text())
            rm=json.loads((reference_smoke/'manifest.json').read_text())
            if reference.get('status')!='complete_smoke_requires_review' or not reference.get('counts_valid') or rm.get('checkpoint_sha256')!=checkpoint_hash or rm.get('upstream_commit')!=PIN:raise BuildError('reference_smoke_mismatch')
            old_prep=json.loads((Path(next(iter(rm['input_hashes']))).parent/'manifest.json').read_text())
            if old_prep['source_linkage_sha256']!=m['source_linkage_sha256']:raise BuildError('cohort_changed_since_smoke')
        with (out/'restricted_runtime.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            import torch
            if not torch.cuda.is_available():raise BuildError('cuda_unavailable')
            ck=torch.load(checkpoint,map_location='cpu',weights_only=False)
            cfg=ck.get('config',{})
            # Explicit advertised checkpoint contract; never override saved settings.
            if cfg.get('mode')!='BCL' or cfg.get('num_leads')!=12 or cfg.get('ecg_seconds')!=10 or cfg.get('ecg_freq')!=500 or cfg.get('signal_representation')!='lead_time_transformer':raise BuildError('checkpoint_contract_mismatch')
            summary['checkpoint_config']={k:cfg[k] for k in ('mode','num_leads','ecg_seconds','ecg_freq','signal_representation')}
            del ck
            summary['runtime']={p:importlib.metadata.version(p) for p in ('torch','numpy','scipy','pandas')}
            summary['gpu']=torch.cuda.get_device_name(0)
            if full and summary['runtime']!=reference['runtime']:raise BuildError('runtime_changed_since_smoke')
            args=[sys.executable,str(upstream/'bcl_embed_torch.py'),'--checkpoint-path',str(checkpoint),'--input-file',str(prep/'restricted_input.csv'),'--formats-csv',str(prep/'restricted_formats.csv'),'--data-roots',str(root),'--output-dir',str(out/'embeddings'),'--batch-size','8','--num-workers','2','--shard-size',str(shard_size),'--no-quality-filter','--no-deduplicate','--no-partial','--no-amp','--no-overwrite','--no-ddp-autodetect']
            result=subprocess.run(args,cwd=upstream,stdout=log,stderr=log)
            if result.returncode:raise BuildError('encoder_failed_review_restricted_log')
        summary['vectors']=validate_vectors(out/'embeddings',ids,shard_size)
        if any(summary['vectors'][k] for k in ('load_error_rows','nonfinite_rows','zero_vector_rows')):raise BuildError('invalid_or_failed_vectors')
        if full and summary['vectors']['dimensions']!=reference['vectors']['dimensions']:raise BuildError('embedding_dimension_changed')
        if digest(checkpoint)!=checkpoint_hash or any(digest(Path(p))!=h for p,h in hashes.items()):raise BuildError('inputs_changed_during_run')
        if any((p.stat().st_size,p.stat().st_mtime_ns)!=v for p,v in wave_stamps.items()):raise BuildError('waveform_changed_during_run')
        atomic_json(out/'manifest.json',dict(upstream_commit=PIN,checkpoint_sha256=checkpoint_hash,input_hashes=hashes,source_linkage_sha256=m['source_linkage_sha256'],reference_smoke=str(reference_smoke) if full else None,script_sha256=digest(Path(__file__))))
        summary.update(status='complete_full_requires_review' if full else 'complete_smoke_requires_review',counts_valid=True,interpretation='Frozen backbone before projection head; technical output checks only. No clinical preprocessing validation, matching or effects.')
    except Exception as e:
        summary.update(status='failed_full' if full else 'failed_smoke',reason=str(e) if isinstance(e,BuildError) else type(e).__name__)
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-started,3);atomic_json(out/'summary.json',summary)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('prep-report','upstream-repo','output-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--reference-smoke',type=Path)
    a=p.parse_args()
    try:s=run(a.prep_report,a.upstream_repo,a.output_dir,a.reference_smoke)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Finished:',s['status']);raise SystemExit(0 if s['counts_valid'] else 1)
