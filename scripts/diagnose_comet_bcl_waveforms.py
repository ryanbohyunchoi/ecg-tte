#!/usr/bin/env python3
"""Bounded path diagnostics only; no waveform contents, IDs or filenames emitted."""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
from audit_comet_embedding_coverage import key,day,records,stamp,ALIASES
from prepare_comet_bcl_input import safe_id
from check_comet_bcl_assets import ROOTS,FORMATS
from build_shared_tables import BuildError,atomic_json,digest


def probe(root,ids):
    info=dict(root=str(root),exists=root.exists(),is_directory=root.is_dir(),is_symlink=root.is_symlink())
    counts=Counter();tested=Counter()
    try:
        if root.is_dir():
            with os.scandir(root) as entries:
                for i,entry in enumerate(entries):
                    if i==500:info['listing_bounded']=True;break
                    counts['entries']+=1
                    if entry.is_symlink():counts['symlinks']+=1
                    if entry.is_dir(follow_symlinks=False):counts['directories']+=1
                    elif entry.is_file(follow_symlinks=False):
                        suffix=Path(entry.name).suffix.lower()
                        counts['regular_'+(suffix if suffix in ('.npy','.npz','.csv','.parquet') else 'other')]+=1
                else:info['listing_bounded']=False
        for alias,values in ids.items():
            for fid in values:
                for mode,name in (('append_npy',fid+'.npy'),('as_given',fid),('append_npz',fid+'.npz')):
                    p=root/name;prefix=alias+':'+mode+':'
                    tested[prefix+'tested']+=1
                    try:
                        if p.is_symlink():tested[prefix+'symlink']+=1
                        if p.is_file():
                            tested[prefix+'file_exists']+=1
                            if p.stat().st_size>0:
                                tested[prefix+'nonempty_file']+=1
                                if not p.is_symlink():tested[prefix+'nonempty_nonsymlink_file']+=1
                        elif p.is_symlink():tested[prefix+'broken_or_nonfile_symlink']+=1
                    except OSError:tested[prefix+'stat_error']+=1
    except OSError:info['listing_error']='OSError'
    info.update(directory_sample=dict(counts),candidate_path_counts=dict(tested))
    return info


def run(report,metadata,out):
    if any(not p.is_absolute() or p.is_symlink() for p in (report,metadata,out)):raise BuildError('absolute_nonsymlink_paths_required')
    if out.resolve()==report.resolve() or report.resolve() in out.resolve().parents or out.resolve() in report.resolve().parents:raise BuildError('output_overlap')
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'manifest.json').read_text())
    if s.get('status')!='complete_ecg_selection_requires_review' or not s.get('counts_valid'):raise BuildError('complete_selection_required')
    linkage=report/'restricted_ecg_linkage.csv'
    checks={str(p):digest(p) for p in (report/'summary.json',report/'manifest.json',linkage)}
    if m['outputs'].get(linkage.name)!=checks[str(linkage)]:raise BuildError('linkage_changed')
    before=stamp(metadata)
    if m['source_stamps'].get(str(metadata))!=before:raise BuildError('metadata_changed_since_selection')
    wanted={};perarm=Counter()
    with linkage.open() as f:
        for r in csv.DictReader(f):
            if r['status']!='no_latest_day_waveform' or perarm[r['treatment_arm']]>=64:continue
            wanted[key(r['patient_key'])]=day(r['ecg_date']);perarm[r['treatment_arm']]+=1
    ids={a:set() for a in ALIASES};shapes=Counter()
    for r in records(metadata,['MRN','ECGDate',*ALIASES]):
        p=key(r['MRN'])
        if p not in wanted or day(r['ECGDate'])!=wanted[p]:continue
        for a in ALIASES:
            fid=safe_id(r[a])
            if not fid:shapes[a+':unsafe_or_empty']+=1;continue
            shapes[a+(':ends_npy' if fid.lower().endswith('.npy') else ':no_npy_suffix')]+=1
            if len(ids[a])<256:ids[a].add(fid)
            else:shapes[a+':id_cap_reached_rows']+=1
    result=dict(version='comet_bcl_waveform_diagnostic_v1',status='diagnostic_complete',restricted_until_reviewed=True,ready_for_inference=False,
        interpretation='First64 missing-waveform patients per arm; up to256 IDs per alias; first500 directory entries. Nonrepresentative diagnostics, no full coverage N or preprocessing change. No waveform contents read.',sampled_by_arm=dict(perarm),id_shape_counts=dict(shapes),sampled_ids_by_alias={a:len(v) for a,v in ids.items()},roots=[probe(Path(r),ids) for r in ROOTS])
    formats=Path(FORMATS);fs=stamp(formats);matched={a:set() for a in ALIASES}
    with formats.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if 'fileID' not in (reader.fieldnames or []):raise BuildError('formats_fileid_missing')
        for r in reader:
            fid=key(r['fileID'])
            for a in ALIASES:
                if fid in ids[a]:matched[a].add(fid)
    result['sampled_ids_in_formats']={a:len(v) for a,v in matched.items()}
    if stamp(metadata)!=before or stamp(formats)!=fs or any(digest(Path(p))!=h for p,h in checks.items()):raise BuildError('source_changed')
    atomic_json(out/'summary.json',result)
    atomic_json(out/'manifest.json',dict(input_checksums=checks,metadata_stamp=before,formats_stamp=fs,script_sha256=digest(Path(__file__))))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:run(a.report,a.metadata,a.output_dir)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Diagnostic saved:',a.output_dir/'summary.json')
