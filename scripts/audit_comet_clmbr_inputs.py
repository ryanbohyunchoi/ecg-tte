#!/usr/bin/env python3
"""Read-only COMET person/MEDS coverage; no tokenization, models or raw JDAT."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, time as day_time
import json
import os
from pathlib import Path
import time
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from build_shared_tables import atomic_json, digest
from audit_comet_embedding_coverage import key, day

class InputError(Exception): pass


def files(root):
    if root.is_symlink(): raise InputError('symlink_source_root')
    if not root.is_dir(): return []
    paths = sorted(root.rglob('*.parquet'))
    for p in paths:
        if any(x.is_symlink() for x in (p,*p.parents)):
            raise InputError('symlink_source_partition')
    return paths


def signature(p):
    s=p.stat(); return [s.st_size,s.st_mtime_ns]


def batches(paths,columns,subject_ids=None):
    selected=pa.array(sorted(subject_ids),type=pa.int64()) if subject_ids is not None else None
    for p in paths:
        for b in pq.ParquetFile(p).iter_batches(batch_size=65536,columns=columns):
            if selected is not None:
                b=b.filter(pc.is_in(b.column(b.schema.get_field_index("subject_id")),value_set=selected))
            yield from b.to_pylist()


def inspect_table(paths):
    schemas={}; rows=0
    for p in paths:
        f=pq.ParquetFile(p); rows+=f.metadata.num_rows
        s=tuple((x.name,str(x.type)) for x in f.schema_arrow)
        schemas[s]=schemas.get(s,0)+1
    return dict(files=len(paths),rows=rows,schemas=[dict(columns=dict(s),files=n) for s,n in schemas.items()])


def inspect_model(root):
    # Fixed metadata/weights filenames only; no pickle deserialization or downloads.
    names=('config.json','tokenizer_config.json','dictionary.msgpack','ontology.pkl',
           'pytorch_model.bin','model.safetensors','model.safetensors.index.json')
    result={}
    for name in names:
        p=root/name
        result[name]=dict(present=p.is_file(),symlink=p.is_symlink(),bytes=p.stat().st_size if p.is_file() else None)
    return dict(root_exists=root.is_dir(),files=result,identity_verified=False)


def coverage(roster,person_paths,meds_paths):
    cohort={}
    for r in roster:
        k=key(r['patient_key']); d=day(r['index_date'])
        if not k or not d or k in cohort: raise InputError('invalid_roster')
        cohort[k]=(r['treatment_arm'],datetime.combine(d,day_time()))
    if not cohort: raise InputError('empty_roster')
    links=defaultdict(set); qc=Counter()
    for r in batches(person_paths,['person_id','person_source_value']):
        k=key(r['person_source_value'])
        if k not in cohort: continue
        pid=r['person_id']
        if not isinstance(pid,int) or isinstance(pid,bool):
            raise InputError('noninteger_person_id')
        links[k].add(pid)
    selected={p for v in links.values() for p in v}
    owners=defaultdict(set)
    for r in batches(person_paths,['person_id','person_source_value']):
        if r['person_id'] in selected: owners[r['person_id']].add(key(r['person_source_value']))
    valid={}; stats=defaultdict(Counter)
    for k,(arm,cutoff) in cohort.items():
        stats[arm]['candidates']+=1
        if not links[k]: stats[arm]['no_exact_person_link']+=1
        elif len(links[k])!=1 or any(owners[p]!={k} for p in links[k]): stats[arm]['ambiguous_person_link']+=1
        else:
            pid=next(iter(links[k])); valid[pid]=(k,arm,cutoff)
            stats[arm]['unique_person_link']+=1
    seen=set(); prior=set(); code_counts=Counter()
    for r in batches(meds_paths,['subject_id','time','code'],subject_ids=valid):
        qc['linked_subject_meds_rows']+=1
        pid=r['subject_id']
        if pid not in valid: continue
        seen.add(pid); k,arm,cutoff=valid[pid]
        t=r['time']; code=key(r['code'])
        if not code: stats[arm]['missing_code_rows']+=1; continue
        if t is None: stats[arm]['undated_rows_not_used_for_prior_coverage']+=1; continue
        if not isinstance(t,datetime) or t.tzinfo is not None:
            stats[arm]['unsupported_timestamp_rows']+=1; continue
        if t>=cutoff:
            stats[arm]['same_day_or_future_rows']+=1; continue
        prior.add(pid); stats[arm]['dated_preindex_coded_rows']+=1
        prefix=code.split('/',1)[0]
        code_counts[prefix if prefix in ('SNOMED','RxNorm','LOINC','Visit','CPT4','ICD10CM','ICD9CM','MEDS_BIRTH') else 'OTHER']+=1
    for pid,(k,arm,cutoff) in valid.items():
        stats[arm]['patients_with_any_meds_rows']+=int(pid in seen)
        stats[arm]['patients_with_dated_preindex_codes']+=int(pid in prior)
        stats[arm]['linked_patients_without_dated_preindex_codes']+=int(pid not in prior)
    return dict(arms={a:dict(v) for a,v in stats.items()},qc=dict(qc),preindex_code_families=dict(code_counts)),[
        dict(patient_key=k,subject_id=pid,treatment_arm=a,index_date=cutoff.date(),has_dated_preindex_code=pid in prior)
        for pid,(k,a,cutoff) in sorted(valid.items())]


def run(source,gold,meds,model,output):
    paths=[source,gold,meds,model,output]
    if any(not p.is_absolute() for p in paths): raise InputError('absolute_paths_required')
    for p in paths[:-1]:
        if p.resolve()==output.resolve() or p.resolve() in output.resolve().parents or output.resolve() in p.resolve().parents:
            raise InputError('source_output_overlap')
    os.umask(0o077); output.mkdir(parents=True,exist_ok=False,mode=0o700)
    result=dict(version='comet_clmbr_inputs_v1',status='running',counts_valid=False,ready_for_inference=False,
        restricted_until_reviewed=True,gold_root=str(gold),meds_root=str(meds),model_root=str(model),
        interpretation='Exact identity and dated-code coverage only. Does not validate MEDS lineage, full schema, model vocabulary, birth/sex handling, numeric consumption, source availability at index or embedding readiness. Clinical event cutoff is strictly before index-date midnight; undated rows do not establish prior history.')
    atomic_json(output/'summary.json',result); start=time.monotonic()
    try:
        s=json.loads((source/'summary.json').read_text()); m=json.loads((source/'manifest.json').read_text())
        baseline=source/'restricted_cleaned_baseline.parquet'
        if s.get('status')!='complete_mice_preparation' or s.get('counts_valid') is not True: raise InputError('complete_preparation_required')
        h=digest(baseline)
        if m['outputs'].get(baseline.name)!=h: raise InputError('baseline_hash_mismatch')
        roster=pq.read_table(baseline,columns=['patient_key','treatment_arm','index_date']).to_pylist()
        if len(roster)!=s['rows'] or dict(Counter(r['treatment_arm'] for r in roster))!=s['denominators']: raise InputError('roster_mismatch')
        person=files(gold/'person'); events=files(meds/'data')
        result.update(person=inspect_table(person),meds=inspect_table(events),model=inspect_model(model),baseline_sha256=h)
        if not person or not events: raise InputError('person_or_meds_partitions_missing')
        before={str(p):signature(p) for p in person+events}
        for p,col in [(p,'person_id') for p in person]+[(p,'subject_id') for p in events]:
            f=pq.ParquetFile(p)
            if not pa.types.is_integer(f.schema_arrow.field(col).type): raise InputError('integer_subject_identity_required')
        aggregates,linked=coverage(roster,person,events)
        if any(signature(p)!=before[str(p)] for p in person+events) or files(gold/'person')!=person or files(meds/'data')!=events:
            raise InputError('source_changed')
        result.update(aggregates)
        if linked: pq.write_table(pa.Table.from_pylist(linked),output/'restricted_person_linkage.parquet')
        atomic_json(output/'restricted_source_inventory.json',before)
        result.update(status='complete_input_coverage',counts_valid=True)
    except Exception as exc:
        result.update(status='failed_input_check',counts_valid=False,error_type=type(exc).__name__,reason=str(exc) if isinstance(exc,InputError) else 'input_read_failed')
    result['elapsed_seconds']=round(time.monotonic()-start,3)
    atomic_json(output/'summary.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('source-report','gold-root','meds-root','model-root','output-dir'):p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    result=run(a.source_report,a.gold_root,a.meds_root,a.model_root,a.output_dir)
    print('Finished:',result['status'],'— review summary.json locally.')
    return 0 if result['counts_valid'] else 1
if __name__=='__main__':raise SystemExit(main())
