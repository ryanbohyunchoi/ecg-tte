#!/usr/bin/env python3
"""Separate 2025 diagnosis and outpatient-lab snapshots; no damaged lab shard access."""
import argparse
from pathlib import Path
from build_shared_tables import BuildError, build, digest, DX_HASH
from inspect_jdat_headers import inspect
from profile_psm_sources import SCHEMAS, DATES

SELECTION={'diagnoses': [('hospital_diagnoses','Hosp_Enc_DX'),('outpatient_diagnoses','Outpatient_Enc_DX')],
           'outpatient-labs':[('outpatient_labs','Outpatient_Enc_Labs')]}


def specs(root,domain,terminal=False):
    root=Path(root)
    if not root.is_absolute():raise BuildError('absolute_source_root_required')
    result=[]
    for name,suffix in SELECTION[domain]:
        relative='Data-2025-04-03/CarDS_2435227_'+suffix+'.txt';h=inspect(root,relative)
        expected=DX_HASH if domain=='diagnoses' else SCHEMAS['labs_2025']
        if h.get('status')!='header_candidate' or h.get('delimiter')!='tab' or h.get('schema_sha256')!=expected:raise BuildError('source_header_mismatch')
        result.append(dict(id=name,path=str(root/relative),format='literal_tabs',schema_hash=expected,
            expected_rows=None,row_count_policy='discover_at_eof',key='PAT_MRN_ID',terminal_empty=terminal,
            dates=[c for c in h['columns'] if c in (DATES|{'CALC_DX_DATE','DX_DTTM','DX_DATE'})],
            delivery='Data-2025-04-03',domain=domain,extension_contract='comet_2025_sources_v1',
            selection_driver_sha256=digest(Path(__file__)),
            interpretation='Source-preserving limited selection; not all-delivery coverage. No cohort change, source union or clinical normalization.'))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--domain',choices=SELECTION,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--resume',action='store_true')
    p.add_argument('--allow-terminal-empty-line',action='store_true');a=p.parse_args()
    try:build(specs(a.root,a.domain,a.allow_terminal_empty_line),a.output_dir,resume=a.resume)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Selected source snapshot complete; no cohort or clinical eligibility changes.');return 0

if __name__=='__main__':raise SystemExit(main())
