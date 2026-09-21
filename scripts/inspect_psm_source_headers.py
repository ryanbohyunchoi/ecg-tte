#!/usr/bin/env python3
"""Header-only inventory of candidate RBC PSM domains; no source rows scanned."""
import argparse
import json
import os
from pathlib import Path
from inspect_jdat_headers import run

SELECTION = {
    'Data-2025-04-03': ['Patients', 'Hosp_Enc', 'Outpatient_Enc', 'Outpatient_Enc_Flo_Vitals',
        'Hosp_Enc_Labs_1', 'Hosp_Enc_Labs_2', 'Hosp_Enc_Labs_3', 'Outpatient_Enc_Labs'],
    'Data-2026-04-15': ['Patients', 'Hosp_Enc', 'Outpatient_Enc', 'Hosp_Enc_Flo_Vitals',
        'Outpatient_Enc_Flo_Vitals', 'Hosp_Enc_Labs_1', 'Hosp_Enc_Labs_2',
        'Hosp_Enc_Labs_3', 'Hosp_Enc_Labs_4', 'Outpatient_Enc_Labs_1',
        'Outpatient_Enc_Labs_2', 'Outpatient_Enc_Labs_3'],
}
FILES = [f'{delivery}/CarDS_2435227_{name}.txt' for delivery,names in SELECTION.items() for name in names]


def compact(summary):
    groups={};unavailable=[]
    for f in summary['files']:
        if f.get('status')!='header_candidate':
            unavailable.append({k:f.get(k) for k in ('relative_path','status','reason')})
            continue
        group=groups.setdefault(f['schema_sha256'],dict(schema_sha256=f['schema_sha256'],
            delimiter=f['delimiter'],columns=f['columns'],files=[]))
        group['files'].append(dict(relative_path=f['relative_path'],file_bytes=f['file_bytes']))
    return dict(version=1,status=summary['status'],root_check=summary['root_check'],
        restricted_until_reviewed=True,data_rows_parsed=False,
        selection='Explicit candidate paths; 2026 Patients is an unverified newer-delivery probe.',
        interpretation='Matching headers do not establish overlapping/disjoint deliveries, units, date meaning or clinical coverage. No source union or extension built.',
        schema_groups=list(groups.values()),unavailable=unavailable)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();os.umask(0o077)
    try:
        result=run(a.root,FILES,a.output_dir,'utf-8-sig','auto',65536)
        (a.output_dir/'schema_groups.json').write_text(json.dumps(compact(result),indent=2)+'\n')
    except Exception as exc:
        print('Header check failed: '+type(exc).__name__)
        return 1
    print('Review schema_groups.json locally. Missing candidates are not silently substituted.')
    return 0 if result['status']=='complete' else 2


if __name__=='__main__':raise SystemExit(main())
