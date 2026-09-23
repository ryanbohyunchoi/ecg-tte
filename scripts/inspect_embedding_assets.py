#!/usr/bin/env python3
"""Bounded checks of archive-derived paths; no model loading or patient records."""
import argparse
import os
from pathlib import Path
import pyarrow.parquet as pq
from build_shared_tables import atomic_json

LEADS={
 'ecg_metadata':'/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet',
 'ecg_signals':'/mnt/raid0/bb2238/signals/preprocessed/all_ecgs',
 'ecg_biometric_checkpoint':'/mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt',
 'ecg_similarity_checkpoint':'/mnt/raid0/rbc58/cardiomap/experiments/ecg_sim_from_biometric/best.pt',
 'legacy_comet_ecg_embeddings':'/mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/embeddings/biometric',
 'clmbr_checkpoint_directory':'/mnt/raid0/eo287/clmbr',
 'clmbr_allcomers_cache':'/mnt/raid0/rbc58/mosaic/prog_clmbr_allcomers.parquet',
 'clmbr_v2_train_cache':'/mnt/raid0/rbc58/mosaic/prog_clmbr_v2_train.parquet',
 'legacy_meds_directory':'/mnt/raid0/rbc58/mosaic/meds_extract_ascvd',
}


def inspect(path):
    p=Path(path);result=dict(path=str(p))
    try:
        if not p.exists():return dict(result,status='not_found')
        if p.is_dir():return dict(result,status='directory_exists_no_listing')
        before=p.stat();result.update(status='file_exists',bytes=before.st_size)
        if p.suffix=='.parquet':
            f=pq.ParquetFile(p)
            result.update(status='footer_read',rows=f.metadata.num_rows,columns=[dict(name=x.name,type=str(x.type)) for x in f.schema_arrow])
        after=p.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):return dict(path=str(p),status='source_changed')
        return result
    except Exception as e:return dict(result,status='unavailable',error_type=type(e).__name__)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    if not a.output_dir.is_absolute():p.error('absolute output path required')
    os.umask(0o077);a.output_dir.mkdir(parents=True,exist_ok=False,mode=0o700)
    result=dict(version='embedding_asset_leads_v1',status='complete_path_checks',restricted_until_reviewed=True,
                interpretation='Archive-derived leads only. No patient linkage, coverage, checkpoint identity, training overlap or pre-index safety validated. No archive modules imported or models loaded.',
                assets={k:inspect(v) for k,v in LEADS.items()})
    atomic_json(a.output_dir/'summary.json',result)
    print('Path/footer checks complete. Review summary.json locally.')
if __name__=='__main__':main()
