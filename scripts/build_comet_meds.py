#!/usr/bin/env python3
"""Build fresh, subject-sharded pre-index MEDS from existing OMOP gold."""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, time as clock_time
import json
import math
import os
from pathlib import Path
import sqlite3
import time
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from audit_comet_clmbr_inputs import files, signature, batches, coverage, InputError
from audit_comet_embedding_coverage import key, day
from build_shared_tables import atomic_json, digest

VERSION='comet_meds_v1'
# These are declared event-time choices, not source availability timestamps.
DOMAINS={
 'condition_occurrence':('condition_concept_id',('condition_start_datetime','condition_start_date'),None),
 'drug_exposure':('drug_concept_id',('drug_exposure_start_datetime','drug_exposure_start_date'),None),
 'procedure_occurrence':('procedure_concept_id',('procedure_datetime','procedure_date'),None),
 'measurement':('measurement_concept_id',('measurement_datetime','measurement_date'),'value_as_number'),
 'visit_occurrence':('visit_concept_id',('visit_start_datetime','visit_start_date'),None),
}
SCHEMA=pa.schema([('subject_id',pa.int64()),('time',pa.timestamp('us')),('code',pa.string()),
 ('numeric_value',pa.float32()),('unit',pa.string()),('source_domain',pa.string()),('source_concept_id',pa.int64())])
BIRTH='MEDS_BIRTH'


def event_time(v):
    if isinstance(v,datetime): return v if v.tzinfo is None else None
    if isinstance(v,date): return datetime.combine(v,clock_time())
    if day(v) is None: return None
    return datetime.fromisoformat(str(v).strip())


def numeric(v):
    if v is None: return None
    try: n=float(v)
    except (ValueError,TypeError): return None
    return n if math.isfinite(n) and abs(n)<=3.4028234e38 else None


def load_roster(source):
    s=json.loads((source/'summary.json').read_text()); m=json.loads((source/'manifest.json').read_text())
    p=source/'restricted_cleaned_baseline.parquet'
    if s.get('status')!='complete_mice_preparation' or s.get('counts_valid') is not True: raise InputError('complete_preparation_required')
    h=digest(p)
    if m['outputs'].get(p.name)!=h: raise InputError('baseline_hash_mismatch')
    rows=pq.read_table(p,columns=['patient_key','treatment_arm','index_date']).to_pylist()
    if len(rows)!=s['rows'] or dict(Counter(r['treatment_arm'] for r in rows))!=s['denominators']: raise InputError('roster_mismatch')
    return rows,h


def concept_rows(path):
    if path.suffix=='.parquet':
        yield from batches([path],['concept_id','vocabulary_id','concept_code'])
    else:
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f,delimiter='\t')
            if not {'concept_id','vocabulary_id','concept_code'}<=set(reader.fieldnames or []): raise InputError('concept_columns_missing')
            yield from reader


def write_shards(db,output,shards):
    outputs={}; counts={}
    for bucket in range(shards):
        cursor=db.execute('SELECT subject_id,t,code,value,unit,domain,cid FROM events WHERE bucket=? AND code IS NOT NULL ORDER BY subject_id,t,code,domain,cid,value,unit',(bucket,))
        writer=None; total=0; p=output/'data'/f'part-{bucket:03d}.parquet'
        try:
            while chunk:=cursor.fetchmany(32768):
                rows=[dict(subject_id=r[0],time=datetime.fromisoformat(r[1]),code=r[2],numeric_value=r[3],unit=r[4],source_domain=r[5],source_concept_id=r[6]) for r in chunk]
                if writer is None: writer=pq.ParquetWriter(p,SCHEMA,compression='zstd')
                writer.write_table(pa.Table.from_pylist(rows,schema=SCHEMA)); total+=len(rows)
        finally:
            if writer: writer.close()
        if total: outputs[str(p.relative_to(output))]=digest(p); counts[str(bucket)]=total
    return outputs,counts


def build(source,gold,concept,output,shards=32):
    if not 1<=shards<=128: raise InputError('invalid_shard_count')
    for p in (source,gold,concept,output):
        if not p.is_absolute() or p.is_symlink(): raise InputError('absolute_nonsymlink_paths_required')
    for p in (source,gold,concept):
        if output.resolve()==p.resolve() or output.resolve() in p.resolve().parents or p.resolve() in output.resolve().parents: raise InputError('source_output_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    (output/'data').mkdir();(output/'metadata').mkdir()
    start=time.monotonic(); db=None
    result=dict(version=VERSION,status='building',counts_valid=False,ready_for_inference=False,restricted_until_reviewed=True,
      gold_root=str(gold),concept_source=str(concept),source_report=str(source),shards=shards,
      timing='All available history strictly before index midnight; missing/offset event times excluded; no availability-at-index claim.',
      numeric_policy='Observed numeric values retained as float32 with raw unit label; no unit conversion or imputation. Invalid/overflow values become null and are counted.',
      schema_contract='MEDS flat-event adapter v1: subject_id int64, time timestamp[us], code string, numeric_value float32; extra unit/provenance. No claim of universal MEDS-version compatibility.',
      birth_policy='Exact consistent birth_datetime only; no synthetic January 1 birthdays. MEDS_BIRTH event; missing birth retained in roster but unavailable for inference.',
      domains=list(DOMAINS),omissions=['No outcomes or post-index events','No inferred drug adherence/dose','No static sex/race tokens in v1; demographics retained in restricted roster','No observation table in this declared five-domain v1'])
    atomic_json(output/'summary.json',result)
    try:
        roster,baseline_hash=load_roster(source)
        person=files(gold/'person'); domain_files={d:files(gold/d) for d in DOMAINS}
        if not person or any(not f for f in domain_files.values()): raise InputError('required_gold_domain_missing')
        source_paths=[*person,*(p for ps in domain_files.values() for p in ps),concept]
        before={str(p):signature(p) for p in source_paths}
        link_qc,linked=coverage(roster,person,[])
        if len(linked)!=len(roster): raise InputError('all_candidate_identity_links_required')
        cuts={r['subject_id']:datetime.combine(r['index_date'],clock_time()) for r in linked}
        arms={r['subject_id']:r['treatment_arm'] for r in linked}
        birthdays={p:set() for p in cuts}
        sexes={p:set() for p in cuts}
        for r in batches(person,['person_id','birth_datetime','gender_concept_id']):
            pid=r['person_id']
            if pid in cuts:
                birthdays[pid].add(event_time(r['birth_datetime']))
                sexes[pid].add(r['gender_concept_id'])
        births={p:next(iter(v)) for p,v in birthdays.items() if len(v)==1 and None not in v and next(iter(v))<cuts[p]}
        for r in linked:
            pid=r['subject_id'];r['birth_datetime']=births.get(pid)
            r['gender_concept_id']=next(iter(sexes[pid])) if len(sexes[pid])==1 else None
            r.pop('has_dated_preindex_code',None)
        db=sqlite3.connect(output/'restricted_staging.sqlite')
        db.execute('PRAGMA temp_store=MEMORY')
        db.execute('CREATE TABLE events(subject_id INTEGER,t TEXT,cid INTEGER,value REAL,unit TEXT,domain TEXT,bucket INTEGER,code TEXT)')
        db.executemany('INSERT INTO events VALUES(?,?,?,?,?,?,?,?)',[(p,b.isoformat(),None,None,None,'birth',p%shards,BIRTH) for p,b in births.items()])
        needed=set();qc={};chosen={};selected=pa.array(sorted(cuts),type=pa.int64())
        for domain,(cid_col,date_options,val_col) in DOMAINS.items():
            counter=Counter();chosen[domain]={}
            for path in domain_files[domain]:
                pf=pq.ParquetFile(path); names=set(pf.schema_arrow.names)
                dates=[c for c in date_options if c in names]
                if not dates or cid_col not in names or 'person_id' not in names: raise InputError('required_event_columns_missing_'+domain)
                if not pa.types.is_integer(pf.schema_arrow.field('person_id').type) or not pa.types.is_integer(pf.schema_arrow.field(cid_col).type): raise InputError('integer_event_identity_required_'+domain)
                if val_col and val_col not in names: raise InputError('numeric_column_missing_'+domain)
                unit_col='unit_source_value' if 'unit_source_value' in names and val_col else None
                cols=['person_id',cid_col,*dates]+([val_col] if val_col else [])+([unit_col] if unit_col else [])
                chosen[domain][str(path)]=cols
                for batch in pf.iter_batches(batch_size=65536,columns=cols):
                    counter['source_rows']+=len(batch)
                    batch=batch.filter(pc.is_in(batch.column(batch.schema.get_field_index('person_id')),value_set=selected))
                    inserts=[]
                    for r in batch.to_pylist():
                        counter['cohort_rows']+=1;pid=r['person_id']
                        # Fallback to a date column only when preferred timestamp is absent/null.
                        raw=next((r[c] for c in dates if key(r[c]) is not None),None)
                        t=event_time(raw)
                        if t is None: counter['invalid_or_missing_time']+=1;continue
                        if t>=cuts[pid]:counter['same_day_or_future']+=1;continue
                        if pid in births and t<births[pid]:counter['before_birth']+=1;continue
                        cid=r[cid_col]
                        if cid is None or cid<=0:counter['no_standard_concept']+=1;continue
                        v=numeric(r[val_col]) if val_col else None
                        if val_col and r[val_col] is not None and v is None: counter['invalid_numeric_value']+=1
                        if v is not None and (not unit_col or key(r[unit_col]) is None):counter['numeric_without_unit_label']+=1
                        needed.add(cid);counter['preindex_candidate_rows']+=1
                        inserts.append((pid,t.isoformat(),cid,v,key(r[unit_col]) if unit_col else None,domain,pid%shards,None))
                    db.executemany('INSERT INTO events VALUES(?,?,?,?,?,?,?,?)',inserts)
                db.commit()
            qc[domain]=dict(counter)
            print('Staged domain:',domain,'cohort pre-index candidate rows:',counter['preindex_candidate_rows'],flush=True)
        mapping={}
        for r in concept_rows(concept):
            try: cid=int(r['concept_id'])
            except (TypeError,ValueError):continue
            if cid not in needed:continue
            v,c=key(r['vocabulary_id']),key(r['concept_code'])
            if not v or not c:continue
            code=v+'/'+c
            if cid in mapping and mapping[cid]!=code:raise InputError('conflicting_concept_mapping')
            mapping[cid]=code
        # Explicit model vocabulary bridge, not arbitrary source label matching.
        mapping.update({cid:code for cid,code in {9201:'Visit/IP',9202:'Visit/OP',9203:'Visit/ER'}.items() if cid in needed})
        db.execute('CREATE TABLE concepts(cid INTEGER PRIMARY KEY,code TEXT)')
        db.executemany('INSERT INTO concepts VALUES(?,?)',mapping.items())
        db.execute('UPDATE events SET code=(SELECT concepts.code FROM concepts WHERE concepts.cid=events.cid) WHERE domain != "birth"')
        db.execute('CREATE INDEX shard_sort ON events(bucket,subject_id,t)');db.commit()
        for domain in DOMAINS:
            qc[domain]['unmapped_preindex_rows']=db.execute('SELECT COUNT(*) FROM events WHERE domain=? AND code IS NULL',(domain,)).fetchone()[0]
        clinical={p:n for p,n in db.execute('SELECT subject_id,COUNT(*) FROM events WHERE code IS NOT NULL AND domain != "birth" GROUP BY subject_id')}
        for r in linked:r['clinical_meds_rows']=clinical.get(r['subject_id'],0)
        arm_counts={}
        for arm in sorted(set(arms.values())):
            ids=[p for p,a in arms.items() if a==arm]
            arm_counts[arm]=dict(candidates=len(ids),with_clinical_events=sum(p in clinical for p in ids),with_exact_birth=sum(p in births for p in ids),with_birth_and_clinical_events=sum(p in births and p in clinical for p in ids))
        outputs,part_counts=write_shards(db,output,shards)
        pq.write_table(pa.Table.from_pylist(linked),output/'restricted_cohort.parquet')
        outputs['restricted_cohort.parquet']=digest(output/'restricted_cohort.parquet')
        atomic_json(output/'metadata'/'dataset.json',dict(version=VERSION,cohort_specific=True,birth_code=BIRTH,subject_sharding='subject_id modulo '+str(shards),numeric_policy=result['numeric_policy']))
        outputs['metadata/dataset.json']=digest(output/'metadata'/'dataset.json')
        if any(signature(p)!=before[str(p)] for p in source_paths) or files(gold/'person')!=person or any(files(gold/d)!=ps for d,ps in domain_files.items()):raise InputError('source_changed')
        atomic_json(output/'restricted_source_inventory.json',dict(files=before,selected_columns=chosen,concept_sha256=digest(concept)))
        outputs['restricted_source_inventory.json']=digest(output/'restricted_source_inventory.json')
        if digest(source/'restricted_cleaned_baseline.parquet')!=baseline_hash:raise InputError('baseline_changed')
        result.update(status='complete_cohort_meds',counts_valid=True,baseline_sha256=baseline_hash,rows=sum(part_counts.values()),arm_coverage=arm_counts,domain_qc=qc,clinical_mapping_concepts=len(mapping))
        atomic_json(output/'manifest.json',dict(version=VERSION,baseline_sha256=baseline_hash,outputs=outputs))
    except Exception as exc:
        result.update(status='failed_cohort_meds',counts_valid=False,error_type=type(exc).__name__,reason=str(exc) if isinstance(exc,InputError) else 'build_failed_no_raw_error_emitted')
    finally:
        if db:db.close()
    result['elapsed_seconds']=round(time.monotonic()-start,3)
    atomic_json(output/'summary.json',result)
    # Retain failed staging for diagnosis; successful shard hashes supersede temporary staging.
    if result['counts_valid']:(output/'restricted_staging.sqlite').unlink()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('source-report','gold-root','concept','output-dir'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--shards',type=int,default=32);a=p.parse_args()
    s=build(a.source_report,a.gold_root,a.concept,a.output_dir,a.shards)
    print('Finished:',s['status'],'— review summary.json locally.')
    return 0 if s['counts_valid'] else 1
if __name__=='__main__':raise SystemExit(main())
