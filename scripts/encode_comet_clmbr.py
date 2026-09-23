#!/usr/bin/env python3
"""Frozen local CLMBR-T inference from the versioned COMET MEDS artifact."""
import argparse
from collections import Counter
from datetime import datetime, time as clock_time, timezone
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import time
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import atomic_json, digest
from build_comet_meds import VERSION as MEDS_VERSION, BIRTH
from audit_comet_clmbr_inputs import InputError, signature

VERSION='comet_clmbr_embeddings_v1'


CONFIG_FIELDS=('hidden_size','n_layers','n_heads','vocab_size','attention_width','is_hierarchical')


def resolved_config_report(raw,config):
    """Use the pinned loader's defaults, never invent dimensions from absent JSON."""
    raw_transformer=raw.get('transformer_config',{})
    if raw_transformer is None:raw_transformer={}
    if not isinstance(raw_transformer,dict):raise InputError('invalid_transformer_config')
    resolved={k:getattr(config.transformer_config,k,None) for k in CONFIG_FIELDS}
    return dict(raw_model_config={k:raw_transformer.get(k) for k in CONFIG_FIELDS},
                model_config=resolved,
                model_config_defaulted_fields=[k for k in CONFIG_FIELDS if k not in raw_transformer])


def verify_inputs(root):
    s=json.loads((root/'summary.json').read_text());m=json.loads((root/'manifest.json').read_text())
    if s.get('version')!=MEDS_VERSION or s.get('status')!='complete_cohort_meds' or s.get('counts_valid') is not True or m.get('version')!=MEDS_VERSION:raise InputError('complete_meds_required')
    for n,h in m['outputs'].items():
        p=root/n
        if p.is_symlink() or root.resolve() not in p.resolve().parents or digest(p)!=h:raise InputError('meds_artifact_changed')
    actual={str(p.relative_to(root)) for p in (root/'data').glob('*.parquet')}
    if actual!={n for n in m['outputs'] if n.startswith('data/')}:raise InputError('meds_partition_set_changed')
    roster=pq.read_table(root/'restricted_cohort.parquet').to_pylist()
    if len({r['subject_id'] for r in roster})!=len(roster):raise InputError('duplicate_subject')
    return roster,m


def patient_events(rows,index_date,birth_code,numeric_mode):
    cutoff=datetime.combine(index_date,clock_time());events=[]
    for timestamp,group in itertools.groupby(rows,key=lambda r:r['time']):
        if timestamp is None or timestamp.tzinfo is not None or timestamp>=cutoff:raise InputError('non_preindex_event')
        measurements=[]
        for r in group:
            code=birth_code if r['code']==BIRTH else r['code']
            m={'code':code}
            if numeric_mode=='native' and r['numeric_value'] is not None:
                if not np.isfinite(r['numeric_value']):raise InputError('nonfinite_numeric_input')
                m['numeric_value']=r['numeric_value']
                if r.get('unit'):m['metadata']={'unit':r['unit']}
            measurements.append(m)
        events.append({'time':timestamp,'measurements':measurements})
    if any(a['time']>b['time'] for a,b in zip(events,events[1:])):raise InputError('unsorted_events')
    return events


def select_vector(reps,timestamps,patient_ids,subject_id,index_date,expected_dim):
    reps=np.asarray(reps);timestamps=np.asarray(timestamps);patient_ids=np.asarray(patient_ids)
    cutoff=datetime.combine(index_date,clock_time(),tzinfo=timezone.utc).timestamp()
    if reps.ndim!=2 or reps.shape[1]!=expected_dim or len(reps)!=len(timestamps) or len(reps)!=len(patient_ids) or not len(reps):raise InputError('representation_shape_invalid')
    if not np.all(patient_ids==subject_id) or not np.all(timestamps<cutoff) or np.any(np.diff(timestamps)<0):raise InputError('representation_identity_or_cutoff_invalid')
    vector=reps[-1].astype(np.float32)
    if not np.all(np.isfinite(vector)) or np.linalg.norm(vector)==0:raise InputError('invalid_vector')
    return vector


def stream_people(path):
    def rows():
        for b in pq.ParquetFile(path).iter_batches(batch_size=32768):yield from b.to_pylist()
    for pid,group in itertools.groupby(rows(),key=lambda r:r['subject_id']):yield pid,list(group)


def encode(root,model_root,output,numeric_mode,max_tokens=4096,limit=32):
    if max_tokens<2 or limit<0:raise InputError('invalid_limits')
    for p in (root,model_root,output):
        if not p.is_absolute() or p.is_symlink():raise InputError('absolute_nonsymlink_paths_required')
    for p in (root,model_root):
        if p.resolve()==output.resolve() or p.resolve() in output.resolve().parents or output.resolve() in p.resolve().parents:raise InputError('source_output_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    start=time.monotonic();s=dict(version=VERSION,status='running',counts_valid=False,ready_for_matching=False,restricted_until_reviewed=True,
        numeric_mode=numeric_mode,max_tokens=max_tokens,limit=limit,
        policy='Frozen local model; latest retained token representation; last max_tokens after FEMR tokenization; no ECG restriction or outcome tuning. Same-day/future events forbidden. Raw vectors, no matching normalization.',
        numeric_interpretation='native passes observed values/raw units to pinned tokenizer without conversion; code-only omits numeric values only at model input. Neither validates clinical units.')
    atomic_json(output/'summary.json',s)
    try:
        roster,manifest=verify_inputs(root)
        meds_manifest_hash=digest(root/'manifest.json')
        source_stamps={n:signature(root/n) for n in manifest['outputs']}
        by_id={r['subject_id']:r for r in roster}
        # Deterministic arm-balanced smoke selection, not a representativeness claim.
        if limit:
            arms=sorted({r['treatment_arm'] for r in roster});selected=[]
            ordered={a:iter(sorted(r['subject_id'] for r in roster if r['treatment_arm']==a)) for a in arms}
            while len(selected)<min(limit,len(roster)):
                for a in arms:
                    pid=next(ordered[a],None)
                    if pid is not None and len(selected)<limit:selected.append(pid)
            targets=set(selected)
        else:targets=set(by_id)
        versions={p:importlib.metadata.version(p) for p in ('femr','meds','torch','transformers','xformers','numpy','pyarrow')}
        s['runtime']=versions
        atomic_json(output/'summary.json',s)
        if versions['femr']!='0.2.3' or versions['meds']!='0.1.3':raise InputError('requires_femr_0_2_3_and_meds_0_1_3')
        import torch
        import meds
        from femr.models.tokenizer import FEMRTokenizer
        from femr.models.processor import FEMRBatchProcessor
        from femr.models.transformer import FEMRModel
        from femr.models.config import FEMRModelConfig
        if not torch.cuda.is_available():raise InputError('cuda_required')
        os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
        model_files=[model_root/n for n in ('config.json','dictionary.msgpack','model.safetensors')]
        if any(not p.is_file() for p in model_files):raise InputError('required_model_files_missing')
        hashes={p.name:digest(p) for p in model_files}
        config=json.loads((model_root/'config.json').read_text())
        resolved=FEMRModelConfig.from_pretrained(str(model_root),local_files_only=True)
        s.update(resolved_config_report(config,resolved))
        expected_dim=s['model_config']['hidden_size']
        if expected_dim!=768:raise InputError('expected_clmbr_t_768_dimensions')
        tokenizer=FEMRTokenizer.from_pretrained(str(model_root))
        if tokenizer.is_hierarchical:raise InputError('hierarchical_tokenizer_requires_explicit_ontology_contract')
        processor=FEMRBatchProcessor(tokenizer)
        torch.manual_seed(20260923)
        model,loading=FEMRModel.from_pretrained(str(model_root),config=resolved,local_files_only=True,use_safetensors=True,output_loading_info=True)
        if any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):raise InputError('checkpoint_state_incompatible')
        model=model.eval().to('cuda')
        for parameter in model.parameters():parameter.requires_grad_(False)
        def move(x):
            if isinstance(x,dict):return {k:move(v) for k,v in x.items()}
            if isinstance(x,(list,tuple)):return type(x)(move(v) for v in x)
            return x.to('cuda') if torch.is_tensor(x) else x
        statuses=[];outputs={};seen=set();totals=Counter()
        for path in sorted((root/'data').glob('*.parquet')):
            vectors=[]
            for pid,rows in stream_people(path):
                if pid not in targets:continue
                if pid in seen:raise InputError('subject_in_multiple_shards')
                seen.add(pid);r=by_id[pid]
                record=dict(subject_id=pid,patient_key=r['patient_key'],treatment_arm=r['treatment_arm'],index_date=r['index_date'])
                if r['birth_datetime'] is None:
                    statuses.append(dict(record,status='missing_exact_birth'));continue
                if r['clinical_meds_rows']==0:
                    statuses.append(dict(record,status='no_clinical_events'));continue
                events=patient_events(rows,r['index_date'],meds.birth_code,numeric_mode)
                if sum(m['code']==meds.birth_code for e in events for m in e['measurements'])<1:raise InputError('birth_event_missing')
                clinical_hits=0;accepted=0;attempted=0;tokenizer.start_patient()
                for e in events:
                    for m in e['measurements']:
                        if m['code']==meds.birth_code:continue
                        attempted+=1
                        if tokenizer.get_feature_codes(e['time'],m)[0]:accepted+=1;clinical_hits+=1
                totals['clinical_measurements']+=attempted;totals['accepted_clinical_measurements']+=accepted
                if not clinical_hits:
                    statuses.append(dict(record,status='no_tokenizer_supported_clinical_events',attempted=attempted,accepted=accepted));continue
                patient={'patient_id':pid,'events':events}
                preliminary=processor.convert_patient(patient)
                n=int(preliminary['transformer']['valid_tokens'].sum())
                if n<1:raise InputError('no_tokens_despite_accepted_codes')
                raw=processor.convert_patient(patient,offset=max(0,n-max_tokens),max_length=max_tokens,tensor_type='pt')
                with torch.inference_mode():_,result=model(**move(processor.collate([raw])))
                v=select_vector(result['representations'].detach().cpu().numpy(),result['timestamps'].detach().cpu().numpy(),result['patient_ids'].detach().cpu().numpy(),pid,r['index_date'],expected_dim)
                vectors.append(dict(record,embedding=v.tolist()))
                statuses.append(dict(record,status='encoded',tokens_available=n,tokens_retained=min(n,max_tokens),attempted=attempted,accepted=accepted))
                totals['encoded']+=1;totals['truncated_patients']+=int(n>max_tokens)
                if totals['encoded']%100==0:print('Encoded patients:',totals['encoded'],flush=True)
            if vectors:
                dest=output/('restricted_embeddings_'+path.stem+'.parquet')
                pq.write_table(pa.Table.from_pylist(vectors),dest,compression='zstd');outputs[dest.name]=digest(dest)
            # Progress is recoverable as an auditable partial run, not automatically reusable cache.
            atomic_json(output/'progress.json',dict(encoded=totals['encoded'],target_patients=len(targets),completed_partitions=len(outputs)))
        for pid in sorted(targets-seen):
            r=by_id[pid];statuses.append(dict(subject_id=pid,patient_key=r['patient_key'],treatment_arm=r['treatment_arm'],index_date=r['index_date'],status='no_meds_rows'))
        pq.write_table(pa.Table.from_pylist(statuses),output/'restricted_patient_status.parquet')
        outputs['restricted_patient_status.parquet']=digest(output/'restricted_patient_status.parquet')
        if hashes!={p.name:digest(p) for p in model_files}:raise InputError('model_changed')
        if digest(root/'manifest.json')!=meds_manifest_hash or any(signature(root/n)!=stamp for n,stamp in source_stamps.items()):raise InputError('meds_changed')
        atomic_json(output/'manifest.json',dict(version=VERSION,meds_manifest_sha256=digest(root/'manifest.json'),model_sha256=hashes,runtime=versions,outputs=outputs,numeric_mode=numeric_mode,max_tokens=max_tokens))
        s['tokenizer_coverage_by_arm']={a:dict(attempted=sum(r.get('attempted',0) for r in statuses if r['treatment_arm']==a),accepted=sum(r.get('accepted',0) for r in statuses if r['treatment_arm']==a)) for a in sorted({r['treatment_arm'] for r in roster})}
        s.update(status='complete_smoke_requires_review' if limit else 'complete_embeddings_requires_review',counts_valid=True,target_patients=len(targets),embedding_dimension=expected_dim,totals=dict(totals),status_by_arm={a:dict(Counter(r['status'] for r in statuses if r['treatment_arm']==a)) for a in sorted({r['treatment_arm'] for r in roster})},model_sha256=hashes)
    except importlib.metadata.PackageNotFoundError as exc:
        s.update(status='failed_encoding',counts_valid=False,error_type=type(exc).__name__,reason='required_runtime_package_missing',package=exc.name)
    except Exception as exc:
        s.update(status='failed_encoding',counts_valid=False,error_type=type(exc).__name__,reason=str(exc) if isinstance(exc,InputError) else 'runtime_failure_no_raw_error_emitted')
    s['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',s)
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('meds-root','model-root','output-dir'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--numeric-mode',choices=['native','code-only'],required=True)
    p.add_argument('--max-tokens',type=int,default=4096);p.add_argument('--limit',type=int,default=32,help='0 for full cohort; default 32 is smoke only')
    a=p.parse_args();s=encode(a.meds_root,a.model_root,a.output_dir,a.numeric_mode,a.max_tokens,a.limit)
    print('Finished:',s['status'],'— review summary.json locally.')
    return 0 if s['counts_valid'] else 1
if __name__=='__main__':raise SystemExit(main())
