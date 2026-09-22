#!/usr/bin/env python3
"""Bounded source metadata and saved-run inventory; no patient rows or raw lab scans."""
import argparse
import json
import os
from pathlib import Path
import time
from inspect_jdat_headers import inspect

DELIVERIES=('Data-2025-04-03','Data-2026-04-15')
LABS={DELIVERIES[0]:['Hosp_Enc_Labs_1','Hosp_Enc_Labs_2','Hosp_Enc_Labs_3','Outpatient_Enc_Labs'],
      DELIVERIES[1]:['Hosp_Enc_Labs_1','Hosp_Enc_Labs_2','Hosp_Enc_Labs_3','Hosp_Enc_Labs_4','Outpatient_Enc_Labs_1','Outpatient_Enc_Labs_2','Outpatient_Enc_Labs_3']}


def metadata(path):
    if path.is_symlink():return dict(status='symlink_not_followed')
    try:
        st=path.stat()
        if not path.is_file():return dict(status='not_regular_file')
        return dict(status='present_metadata_only',bytes=st.st_size,mtime_ns=st.st_mtime_ns)
    except FileNotFoundError:return dict(status='missing')
    except OSError:return dict(status='unreadable')


def bounded_json(path):
    if path.is_symlink():raise ValueError('symlink')
    with path.open('rb') as f:data=f.read(1048577)
    if len(data)>1048576:raise ValueError('report_limit')
    return json.loads(data)


def run(root,shared,audits,output):
    root,shared,audits,output=map(Path,(root,shared,audits,output))
    if any(not p.is_absolute() or p.is_symlink() for p in (root,shared,audits,output)):raise ValueError('absolute_nonsymlink_paths_required')
    if not root.is_dir():raise ValueError('source_root_unavailable')
    if output.exists():raise FileExistsError('fresh_output_required')
    if output.resolve()==root.resolve() or root.resolve() in output.resolve().parents or output.resolve() in root.resolve().parents:raise ValueError('output_source_overlap')
    start=time.monotonic();result=dict(version='comet_source_dependencies_v1',status='metadata_check_complete',restricted_until_reviewed=True,
        interpretation='File metadata and diagnosis headers only. Lab integrity, source coverage, key compatibility and clinical units are NOT established. No source substitution, build, patient rows or cohort changes.',
        diagnoses=[],labs=[],metadata_file_candidates=[],saved_lab_stages=[],saved_measurement_catalogs=[],warnings=[])
    for delivery in DELIVERIES:
        base=root/delivery
        if base.is_symlink():
            result['warnings'].append(delivery+':symlink_not_followed');continue
        for domain in ('Hosp_Enc_DX','Outpatient_Enc_DX'):
            relative=delivery+'/CarDS_2435227_'+domain+'.txt'
            h=inspect(root,relative)
            result['diagnoses'].append(dict(relative_path=relative,**{k:h[k] for k in ('status','schema_sha256','columns','file_bytes','reason') if k in h}))
        for domain in LABS[delivery]:
            relative=delivery+'/CarDS_2435227_'+domain+'.txt'
            result['labs'].append(dict(relative_path=relative,known_damaged_source=(delivery==DELIVERIES[0] and domain=='Hosp_Enc_Labs_3'),**metadata(root/relative)))
    # Filenames only, no recursive traversal or dictionary contents.
    for base in (root,*(root/d for d in DELIVERIES)):
        if base.is_symlink() or not base.is_dir():continue
        with os.scandir(base) as entries:
            for i,e in enumerate(entries):
                if i>=10000:result['warnings'].append('filename_inventory_limit');break
                if e.is_file(follow_symlinks=False) and any(t in e.name.lower() for t in ('dictionary','data_dict','lookup','readme','codebook','mapping')):
                    result['metadata_file_candidates'].append(str(Path(e.path)))
    for base,target in ((shared,'snapshot/summary.json'),(audits,'report/restricted_measurement_catalog.json')):
        if not base.is_dir():result['warnings'].append('saved_run_root_unavailable');continue
        with os.scandir(base) as entries:
            for i,e in enumerate(entries):
                if i>=10000:result['warnings'].append('saved_run_inventory_limit');break
                if not e.is_dir(follow_symlinks=False):continue
                p=Path(e.path)/target
                if p.parent.is_symlink() or not p.is_file() or p.is_symlink():continue
                if base==audits:
                    result['saved_measurement_catalogs'].append(str(p));continue
                try:s=bounded_json(p)
                except (OSError,ValueError):result['warnings'].append('saved_summary_unreadable_or_oversized');continue
                for name,table in s.get('tables',{}).items():
                    if 'lab' in name.lower():
                        result['saved_lab_stages'].append(dict(summary=str(p),snapshot_status=s.get('status'),table=name,
                            rows=table.get('rows'),parts=table.get('parts'),source_sha256=table.get('source_sha256')))
    result['elapsed_seconds']=round(time.monotonic()-start,3)
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','shared-root','audit-root','output-dir'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:run(a.root,a.shared_root,a.audit_root,a.output_dir)
    except Exception as e:print('Stopped: '+type(e).__name__);return 1
    print('Metadata check complete. Review summary.json locally; no lab integrity or unit validation implied.');return 0

if __name__=='__main__':raise SystemExit(main())
