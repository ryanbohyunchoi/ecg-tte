#!/usr/bin/env python3
"""Check explicit BCL asset paths only; no weights, waveforms or patient rows read."""
import argparse
import csv
import os
from pathlib import Path
from build_shared_tables import atomic_json

CHECKPOINT='/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt'
FORMATS='/mnt/nfs_yale_ecg/preprocessing/formats_rerun.csv'
ROOTS=('/mnt/local_data_store/bb2238/signals/preprocessed/all_ecgs','/mnt/yale-ecg-signals/numpy_rp','/mnt/yale-ecg-signals/numpy','/mnt/raid0/bb2238/signals/preprocessed/all_ecgs')

def inspect(path,kind):
    p=Path(path);r=dict(path=str(p),kind=kind,exists=p.exists(),is_symlink=p.is_symlink())
    try:
        r.update(is_file=p.is_file(),is_directory=p.is_dir(),readable=os.access(p,os.R_OK))
        if p.is_file():r['bytes']=p.stat().st_size
        if kind=='formats' and p.is_file():
            with p.open('rb') as f:header=f.readline(65537)
            if len(header)>65536:r['header_status']='over_limit'
            else:
                columns=next(csv.reader([header.decode('utf-8-sig').rstrip('\r\n')]))
                r['required_columns_present']={c:c in columns for c in ('fileID','format_new')}
    except Exception as e:r['error_type']=type(e).__name__
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if not a.output_dir.is_absolute() or a.output_dir.is_symlink():raise SystemExit('Absolute fresh output directory required')
    os.umask(0o077);a.output_dir.mkdir(parents=True,exist_ok=False)
    result=dict(version='comet_bcl_asset_check_v1',status='path_check_complete',restricted_until_reviewed=True,ready_for_inference=False,
        upstream_commit='d359c04d1f5e6c810f76751777535918870704b7',
        interpretation='Presence/readability and formats header only; checkpoint contents, preprocessing semantics and patient waveform availability unverified.',
        assets=[inspect(CHECKPOINT,'checkpoint'),inspect(FORMATS,'formats'),inspect('/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet','ecg_metadata')]+[inspect(r,'waveform_root') for r in ROOTS])
    atomic_json(a.output_dir/'summary.json',result)
    print('Saved:',a.output_dir/'summary.json')
if __name__=='__main__':main()
