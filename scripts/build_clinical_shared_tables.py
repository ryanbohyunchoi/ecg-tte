#!/usr/bin/env python3
"""Independent demographics/encounters/vitals snapshot; no lab sources opened."""
import argparse
from pathlib import Path

from build_shared_tables import BuildError, build, digest
from inspect_jdat_headers import inspect
from profile_psm_sources import DATES, sources

DOMAINS={'patients','hospital_encounters','outpatient_encounters','vitals'}
EXPECTED={
 'Data-2025-04-03/CarDS_2435227_Patients.txt',
 'Data-2025-04-03/CarDS_2435227_Hosp_Enc.txt',
 'Data-2025-04-03/CarDS_2435227_Outpatient_Enc.txt',
 'Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Flo_Vitals.txt',
 'Data-2026-04-15/CarDS_2435227_Hosp_Enc.txt',
 'Data-2026-04-15/CarDS_2435227_Outpatient_Enc.txt',
 'Data-2026-04-15/CarDS_2435227_Hosp_Enc_Flo_Vitals.txt',
 'Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Flo_Vitals.txt',
}


def clinical_sources(root,allow_terminal_empty=False):
    root=Path(root)
    if not root.is_absolute():raise BuildError('absolute_source_root_required')
    selected=[s for s in sources() if s[1] in DOMAINS]
    if len(selected)!=len(EXPECTED) or {s[0] for s in selected}!=EXPECTED:raise BuildError('clinical_source_inventory_changed')
    specs=[]
    for relative,domain,schema in selected:
        h=inspect(root,relative)
        if h.get('status')!='header_candidate' or h.get('delimiter')!='tab':raise BuildError('clinical_header_unavailable')
        if h['schema_sha256']!=schema:raise BuildError('clinical_schema_mismatch')
        if 'PAT_MRN_ID' not in h['columns']:raise BuildError('clinical_patient_key_absent')
        delivery,filename=relative.split('/')
        specs.append(dict(id=delivery.replace('-','_')+'_'+filename.removeprefix('CarDS_2435227_').removesuffix('.txt').lower(),
            path=str(root/relative),format='literal_tabs',schema_hash=schema,expected_rows=None,
            row_count_policy='discover_at_eof',key='PAT_MRN_ID',terminal_empty=allow_terminal_empty,
            dates=[c for c in h['columns'] if c in DATES],delivery=delivery,domain=domain,relative_path=relative,
            extension_contract='clinical_raw_sources_v1',selection_driver_sha256=digest(Path(__file__)),
            interpretation='Separate raw-preserving delivery tables. No union, deduplication, clinical mappings or cohort filtering; no labs in this snapshot.'))
    return specs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--allow-terminal-empty-line',action='store_true')
    p.add_argument('--resume',action='store_true',help='Resume only this exact clinical snapshot contract, never the failed PSM snapshot.')
    a=p.parse_args()
    try:r=build(clinical_sources(a.root,a.allow_terminal_empty_line),a.output_dir,resume=a.resume)
    except Exception as exc:
        print('Clinical snapshot stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__),flush=True);return 1
    print('Clinical snapshot complete. Keep tables and manifests on H100.',flush=True)
    for name,stage in r['stages'].items():print(name+': '+str(stage['rows'])+' rows',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
