#!/usr/bin/env python3
"""Prepare private latest pre-index ECG linkage; no inference or waveform loading."""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
from audit_comet_embedding_coverage import key,day,records,stamp,ALIASES
from build_shared_tables import BuildError,atomic_json,digest
from build_comet_meds import load_roster


def safe_id(v):
    v=key(v)
    return v if v and v not in ('.','..') and not any(c in v for c in ('/','\\','\x00','\n','\r')) else None


def relative_id(v):
    """Canonical relative stem; accept one optional .npy suffix, never basename-strip."""
    v=key(v)
    if not v or v.startswith('/') or any(ord(c)<32 or ord(c)==127 for c in v) or '\\' in v:return None
    if any(part in ('','.','..') for part in v.split('/')):return None
    if v.endswith('.npy'):v=v[:-4]
    if not v or v.split('/')[-1] in ('','.','..'):return None
    return v


def waveform_ok(root,fid):
    path=root/(fid+'.npy')
    # Reject symlinked directories as well as symlinked files.
    if root.is_symlink() or any(p.is_symlink() for p in (path,*path.parents) if p==root or root in p.parents):return False
    if root.resolve() not in path.resolve().parents:return False
    return path.is_file() and path.stat().st_size>0


def select(roster,metadata,waveforms,formats,relative_npy=False):
    normalize=relative_id if relative_npy else safe_id
    people={};latest={};qc=Counter()
    for r in roster:
        k=key(r['patient_key']);d=day(r['index_date'])
        if not k or not d or k in people:raise BuildError('invalid_roster')
        people[k]=(r['treatment_arm'],d)
    # Pick the latest calendar day BEFORE checking availability; no older fallback.
    for r in records(metadata,['MRN','ECGDate',*ALIASES]):
        qc['metadata_rows']+=1;p=key(r['MRN']);d=day(r['ECGDate'])
        if p not in people:continue
        if d is None:qc['cohort_invalid_date_rows']+=1;continue
        lag=(people[p][1]-d).days
        if not 1<=lag<=365:continue
        qc['prior365_rows']+=1
        ids=tuple(normalize(r[a]) for a in ALIASES)
        if p not in latest or d>latest[p][0]:latest[p]=(d,{ids})
        elif d==latest[p][0]:latest[p][1].add(ids)
    relevant={fid for _,rows in latest.values() for ids in rows for fid in ids if fid}
    owners={};ambiguous=set()
    for r in records(metadata,['MRN','ECGDate',*ALIASES]):
        for fid in {normalize(r[a]) for a in ALIASES}&relevant:
            identity=(key(r['MRN']),day(r['ECGDate']))
            if None in identity or fid in owners and owners[fid]!=identity:ambiguous.add(fid)
            owners[fid]=identity
    exists={}
    for fid in relevant:
        p=waveforms/(fid+'.npy')
        exists[fid]=waveform_ok(waveforms,fid)
    format_labels={};format_conflicts=set()
    with formats.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not {'fileID','format_new'}<=set(reader.fieldnames or []):raise BuildError('formats_columns_missing')
        for r in reader:
            fid=normalize(r['fileID']) if relative_npy else key(r['fileID'])
            if fid not in relevant:continue
            # Exact upstream rule; empty labels do not establish sampling semantics.
            label=key(r['format_new']);flag=None if label is None else ('5_0' in label)
            if fid in format_labels and format_labels[fid]!=flag:format_conflicts.add(fid)
            format_labels[fid]=flag
    rows=[]
    for p,(arm,index) in people.items():
        result=dict(patient_key=p,treatment_arm=arm,index_date=index.isoformat(),status='no_prior365_ecg',fileID='',ecg_date='',lag_days='',metadata_alias='',format_250hz='',waveform_bytes='',waveform_mtime_ns='')
        if p in latest:
            d,idsrows=latest[p];result.update(ecg_date=d.isoformat(),lag_days=(index-d).days)
            candidates={};unresolved=False
            for ids in idsrows:
                usable=[(alias,fid) for alias,fid in zip(ALIASES,ids) if fid and exists[fid]]
                fids={fid for _,fid in usable}
                if len(fids)>1:unresolved=True
                for alias,fid in usable:candidates.setdefault(fid,set()).add(alias)
            if unresolved:result['status']='multiple_waveform_aliases_unresolved'
            elif any(fid in ambiguous for fid in candidates):result['status']='ambiguous_latest_day_identity'
            elif not candidates:result['status']='no_latest_day_waveform'
            else:
                # Multiple ECGs on that same latest day: lexical resolved fileID.
                fid=sorted(candidates)[0];result.update(fileID=fid,metadata_alias='+'.join(sorted(candidates[fid])))
                if fid in format_conflicts:result['status']='conflicting_sampling_formats'
                elif fid not in format_labels or format_labels[fid] is None:result['status']='sampling_format_unresolved'
                else:
                    path=waveforms/(fid+'.npy');size,mtime=stamp(path)
                    result.update(status='selected_for_smoke',format_250hz=format_labels[fid],waveform_bytes=size,waveform_mtime_ns=mtime)
        rows.append(result)
    selected=[r for r in rows if r['status']=='selected_for_smoke']
    if len({r['fileID'] for r in selected})!=len(selected):raise BuildError('selected_waveform_reused')
    return rows,dict(qc)


def run(source,metadata,waveforms,formats,out,relative_npy=False):
    paths=(source,metadata,waveforms,formats,out)
    if any(not p.is_absolute() or p.is_symlink() for p in paths):raise BuildError('absolute_nonsymlink_paths_required')
    if any(out.resolve()==p.resolve() or out.resolve() in p.resolve().parents or p.resolve() in out.resolve().parents for p in paths[:-1]):raise BuildError('output_overlap')
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    summary=dict(version='comet_bcl_input_v2_relative_npy' if relative_npy else 'comet_bcl_input_v1',status='running',counts_valid=False,restricted_until_reviewed=True,ready_for_inference=False)
    try:
        before={str(p):stamp(p) for p in (metadata,formats,source/'restricted_cleaned_baseline.parquet')}
        roster,baseline_hash=load_roster(source)
        formats_hash=digest(formats)
        rows,qc=select(roster,metadata,waveforms,formats,relative_npy)
        if any(stamp(Path(p))!=s for p,s in before.items()):raise BuildError('source_changed')
        if digest(source/'restricted_cleaned_baseline.parquet')!=baseline_hash:raise BuildError('baseline_changed')
        with (out/'restricted_ecg_linkage.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        selected=[r for r in rows if r['status']=='selected_for_smoke']
        with (out/'restricted_bcl_input.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['fileID']);w.writerows([[r['fileID']] for r in selected])
        summary.update(path_contract='relative_stem_optional_npy_suffix_no_symlinks' if relative_npy else 'flat_id_append_npy',status='complete_ecg_selection_requires_review',counts_valid=True,rows=len(roster),selected=len(selected),qc=qc,
            status_by_arm={a:dict(Counter(r['status'] for r in rows if r['treatment_arm']==a)) for a in sorted({r['treatment_arm'] for r in rows})},
            alias_counts=dict(Counter(r['metadata_alias'] for r in selected)),format_250hz_selected=sum(r['format_250hz'] for r in selected),
            policy='Latest strictly prior calendar day1–365, then lexical resolved fileID; no older fallback. Both aliases matching different waveforms excluded. Global patient/date collisions excluded. Sampling label must be present and unambiguous. File presence is not waveform or checkpoint validation.')
        atomic_json(out/'manifest.json',dict(baseline_sha256=baseline_hash,formats_sha256=formats_hash,source_stamps=before,waveform_root=str(waveforms),script_sha256=digest(Path(__file__)),outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    except Exception as e:
        summary.update(status='failed_ecg_selection',reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:atomic_json(out/'summary.json',summary)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source-report','metadata','waveform-root','formats','output-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--relative-npy',action='store_true')
    a=p.parse_args()
    try:run(a.source_report,a.metadata,a.waveform_root,a.formats,a.output_dir,a.relative_npy)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Selection saved; review summary before inference.')
