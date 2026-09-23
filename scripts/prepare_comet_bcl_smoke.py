#!/usr/bin/env python3
"""Prepare deterministic private BCL smoke inputs from validated v2 selection."""
import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
from build_shared_tables import BuildError, atomic_json, digest
from prepare_comet_bcl_input import relative_id, waveform_ok, stamp


def choose(rows,full=False):
    selected=[r for r in rows if r['status']=='selected_for_smoke']
    groups={}
    for r in selected:
        if r['format_250hz'] not in ('True','False'):raise BuildError('invalid_sampling_flag')
        if relative_id(r['fileID'])!=r['fileID']:raise BuildError('noncanonical_id')
        groups.setdefault((r['treatment_arm'],r['format_250hz']),[]).append(r)
    # Eight from each arm/sampling stratum: up to32, diagnostic not representative.
    return [r for k in sorted(groups) for r in sorted(groups[k],key=lambda r:r['fileID'])[:None if full else 8]]


def run(report,out,full=False):
    if any(not p.is_absolute() or p.is_symlink() for p in (report,out)):raise BuildError('absolute_nonsymlink_paths_required')
    if report.resolve()==out.resolve() or report.resolve() in out.resolve().parents or out.resolve() in report.resolve().parents:raise BuildError('output_overlap')
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'manifest.json').read_text())
    if s.get('version')!='comet_bcl_input_v2_relative_npy' or not s.get('counts_valid') or s.get('status')!='complete_ecg_selection_requires_review':raise BuildError('completed_v2_selection_required')
    linkage=report/'restricted_ecg_linkage.csv';before=digest(linkage)
    if before!=m['outputs'].get(linkage.name):raise BuildError('linkage_changed')
    with linkage.open(newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=s['rows'] or sum(r['status']=='selected_for_smoke' for r in rows)!=s['selected']:raise BuildError('selection_count_mismatch')
    sample=choose(rows,full)
    if not sample or len({r['fileID'] for r in sample})!=len(sample):raise BuildError('empty_or_duplicate_smoke')
    root=Path(m['waveform_root'])
    for r in sample:
        if not waveform_ok(root,r['fileID']) or list(stamp(root/(r['fileID']+'.npy')))!=[int(r['waveform_bytes']),int(r['waveform_mtime_ns'])]:raise BuildError('selected_waveform_changed')
    if digest(linkage)!=before:raise BuildError('linkage_changed')
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False)
    with (out/'restricted_input.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['fileID']);w.writerows([[r['fileID']] for r in sample])
    with (out/'restricted_formats.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['fileID','format_new'])
        # Derived adapter flags reproduce the already selected upstream Boolean rule.
        # These are not original clinical labels or independently validated frequencies.
        w.writerows([[r['fileID'],'5_0' if r['format_250hz']=='True' else 'adapter_non250'] for r in sample])
    atomic_json(out/'manifest.json',dict(source_linkage_sha256=before,source_report=str(report),waveform_root=str(root),outputs={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    summary=dict(version='comet_bcl_full_inputs_v1' if full else 'comet_bcl_smoke_inputs_v1',status='complete_full_inputs' if full else 'complete_smoke_inputs',ready_for_inference=False,restricted_until_reviewed=True,rows=len(sample),groups=[dict(arm=a,format_250hz=b,rows=n) for (a,b),n in sorted(Counter((r['treatment_arm'],r['format_250hz']) for r in sample).items())],interpretation=('All selected ECGs.' if full else 'Up to8 per arm/sampling stratum.')+'  Derived catalog reproduces selection flags using canonical relative stems. No waveform contents or checkpoint loaded; checkpoint/runtime review remains pending.')
    atomic_json(out/'summary.json',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--full',action='store_true');a=p.parse_args()
    try:run(a.report,a.output_dir,a.full)
    except Exception as e:print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Saved:',a.output_dir/'summary.json')
