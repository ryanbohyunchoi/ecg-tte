#!/usr/bin/env python3
"""Link validated BCL vectors to the unchanged baseline; no matching or outcomes."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import BuildError,atomic_json,digest
from run_comet_bcl_smoke import read_csv,validate_vectors,PIN
from audit_comet_embedding_coverage import day


def link_vectors(linkage,ids,vectors,baseline):
    lookup={r['patient_key']:r for r in baseline}
    chosen=[r for r in linkage if r['status']=='selected_for_smoke']
    byfile={r['fileID']:r for r in chosen}
    if len(lookup)!=len(baseline) or len(byfile)!=len(chosen) or len(ids)!=len(set(ids)) or set(ids)!=set(byfile):raise BuildError('duplicate_or_incomplete_linkage')
    if len(linkage)!=len(baseline) or {r['patient_key'] for r in linkage}!=set(lookup):raise BuildError('baseline_roster_mismatch')
    result=[]
    for fid,vector in zip(ids,vectors):
        r=byfile[fid];b=lookup[r['patient_key']]
        if r['treatment_arm']!=b['treatment_arm'] or day(r['index_date'])!=day(b['index_date']):raise BuildError('baseline_identity_mismatch')
        d=day(r['ecg_date']);idx=day(b['index_date'])
        if d is None or idx is None or not 1<=(idx-d).days<=365:raise BuildError('preindex_cutoff_mismatch')
        result.append(dict(patient_key=b['patient_key'],treatment_arm=b['treatment_arm'],index_date=b['index_date'],embedding=vector.tolist()))
    if len(result)!=len(ids) or len({r['patient_key'] for r in result})!=len(result):raise BuildError('duplicate_patient_or_vector_count')
    return result


def run(full,out):
    if any(not p.is_absolute() or p.is_symlink() for p in (full,out)):raise BuildError('absolute_nonsymlink_paths_required')
    if full.resolve()==out.resolve() or full.resolve() in out.resolve().parents or out.resolve() in full.resolve().parents:raise BuildError('output_overlap')
    s=json.loads((full/'summary.json').read_text());m=json.loads((full/'manifest.json').read_text())
    if s.get('status')!='complete_full_requires_review' or not s.get('counts_valid') or s['vectors']['dimensions']!=256 or m['upstream_commit']!=PIN:raise BuildError('completed_bcl_full_required')
    checks={full/n:digest(full/n) for n in ('summary.json','manifest.json')}
    for p,h in m['input_hashes'].items():
        if digest(Path(p))!=h:raise BuildError('full_input_changed')
        checks[Path(p)]=h
    prep=Path(next(iter(m['input_hashes']))).parent
    pm=json.loads((prep/'manifest.json').read_text());checks[prep/'manifest.json']=digest(prep/'manifest.json')
    source=Path(pm['source_report']);sm=json.loads((source/'manifest.json').read_text())
    linkage=source/'restricted_ecg_linkage.csv';lh=digest(linkage)
    if lh!=pm['source_linkage_sha256'] or lh!=m['source_linkage_sha256'] or lh!=sm['outputs'][linkage.name]:raise BuildError('linkage_changed')
    checks[linkage]=lh;checks[source/'manifest.json']=digest(source/'manifest.json')
    baseline_paths=[Path(p) for p in sm['source_stamps'] if Path(p).name=='restricted_cleaned_baseline.parquet']
    if len(baseline_paths)!=1:raise BuildError('baseline_path_unresolved')
    baseline=baseline_paths[0];bh=digest(baseline)
    if bh!=sm['baseline_sha256']:raise BuildError('baseline_changed')
    checks[baseline]=bh
    ids=[r['fileID'] for r in read_csv(prep/'restricted_input.csv')]
    directory=full/'embeddings'
    for p in directory.iterdir():
        if p.is_file():checks[p]=digest(p)
    qc=validate_vectors(directory,ids,512)
    if qc!=s['vectors'] or any(qc[k] for k in ('load_error_rows','nonfinite_rows','zero_vector_rows')):raise BuildError('full_vector_qc_mismatch')
    vectors=np.concatenate([np.load(p,allow_pickle=False) for p in sorted(directory.glob('shard_*.npy'))])
    original=pq.read_table(baseline).to_pylist()
    rows=link_vectors(read_csv(linkage),ids,vectors,original);encoded={r['patient_key'] for r in rows}
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    pq.write_table(pa.Table.from_pylist(rows),out/'restricted_embeddings_part-00000.parquet')
    pq.write_table(pa.Table.from_pylist([dict(patient_key=r['patient_key'],status='encoded' if r['patient_key'] in encoded else 'no_selected_bcl') for r in original]),out/'restricted_patient_status.parquet')
    if any(digest(p)!=h for p,h in checks.items()):raise BuildError('source_changed')
    atomic_json(out/'summary.json',dict(version='comet_bcl_linked_embeddings_v1',status='complete_bcl_linkage_requires_review',counts_valid=True,ready_for_effects=False,restricted_until_reviewed=True,totals=dict(encoded=len(rows)),dimensions=256,interpretation='Exact selected fileID to baseline linkage; prior1-365day check. No new cohort selection or matching. Original full-run vectors had no saved content digests; hashes recorded now with repeated structural/value validation.'))
    atomic_json(out/'manifest.json',dict(representation='BCL_backbone_before_projection',checkpoint_sha256=m['checkpoint_sha256'],upstream_commit=PIN,baseline_sha256=bh,input_checksums={str(p):h for p,h in checks.items()},outputs={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='summary.json'}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--full-report',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:run(a.full_report,a.output_dir)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('BCL linkage complete; private outputs saved.')
