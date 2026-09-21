#!/usr/bin/env python3
"""Constant-memory physical-line diagnostics; never export source cell contents."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time

from inspect_jdat_headers import inspect


class DiagnosticError(ValueError):
    pass


def scan(stream, expected_columns, record_limit=1048576, chunk_bytes=4194304):
    """Scan bytes after the header; retain counters, never complete long records."""
    if min(expected_columns, record_limit, chunk_bytes) < 1:
        raise DiagnosticError('invalid_scan_contract')
    counts=Counter(); samples=[]; raw_length=0; tabs=0; last_byte=None; ordinal=0
    max_bytes=0; max_payload=0; last=None; nul=False
    hashed=hashlib.sha256()
    def finish(terminated):
        nonlocal raw_length,tabs,last_byte,ordinal,max_bytes,max_payload,last,nul
        ordinal+=1
        # Segments exclude LF but retain a possible preceding CR.
        payload=raw_length-int(terminated)-int(terminated and last_byte==13)
        columns=tabs+1
        exact_empty=payload==0
        too_long=raw_length>record_limit
        counts['physical_lines']+=1
        counts['matching_width' if columns==expected_columns else 'too_few_columns' if columns<expected_columns else 'too_many_columns']+=1
        counts['over_record_limit']+=int(too_long)
        counts['exact_empty_lines']+=int(exact_empty)
        counts['lines_with_nul']+=int(nul)
        counts['unterminated_lines']+=int(not terminated)
        max_bytes=max(max_bytes,raw_length);max_payload=max(max_payload,payload)
        last=dict(data_physical_line_1based=ordinal,raw_record_bytes=raw_length,
                  payload_bytes=payload,columns=columns,terminated_with_newline=terminated,
                  exact_empty_line=exact_empty,contains_nul=nul)
        if too_long or columns!=expected_columns or nul:
            if len(samples)<20: samples.append(dict(last))
            else: counts['anomaly_samples_omitted']+=1
        raw_length=0;tabs=0;last_byte=None;nul=False
    while True:
        block=stream.read(chunk_bytes)
        if not block: break
        hashed.update(block)
        pieces=block.split(b'\n')
        for i,piece in enumerate(pieces):
            raw_length+=len(piece);tabs+=piece.count(b'\t');nul=nul or b'\x00' in piece
            if piece: last_byte=piece[-1]
            if i<len(pieces)-1:
                raw_length+=1
                finish(True)
    if raw_length: finish(False)
    for sample in samples:
        sample['is_final_physical_line']=sample['data_physical_line_1based']==ordinal
    return dict(counts=dict(counts),max_raw_record_bytes=max_bytes,max_payload_bytes=max_payload,
                anomaly_samples=samples,last_line=last,data_bytes_sha256=hashed.hexdigest(),reached_eof=True)


def run(source, output, expected_schema):
    source,output=Path(source),Path(output)
    if not source.is_absolute() or not output.is_absolute() or source.is_symlink() or output.is_symlink():
        raise DiagnosticError('absolute_nonsymlink_paths_required')
    source,output=source.resolve(),output.resolve()
    if output==source.parent or source.parent in output.parents or output in source.parents:
        raise DiagnosticError('output_source_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    start=time.monotonic()
    report=dict(version=1,status='running',restricted_until_reviewed=True,source=str(source),
                interpretation='Byte structure only; no values, patient N, UTF-8/clinical validation, skipped rows or approved parser change.',
                record_limit_bytes=1048576)
    def save():
        temp=output/'summary.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(output/'summary.json')
    save()
    try:
        before=source.stat()
        header=inspect(source.parent,source.name)
        if header.get('status')!='header_candidate' or header.get('delimiter')!='tab' or header['schema_sha256']!=expected_schema:
            raise DiagnosticError('schema_mismatch_or_unavailable')
        with source.open('rb') as stream:
            stream.readline(65537)
            print('Scanning byte structure only; no clinical values will be printed.',flush=True)
            result=scan(stream,header['column_count'])
        after=source.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
            raise DiagnosticError('source_changed')
        report.update(status='diagnostic_complete',source_changed=False,source_bytes=after.st_size,
                      schema_sha256=expected_schema,expected_columns=header['column_count'],**result)
    except Exception as exc:
        report.update(status='failed_diagnostic',reason=str(exc) if isinstance(exc,DiagnosticError) else 'diagnostic_failed_no_raw_error_export')
        raise
    finally:
        report['elapsed_seconds']=round(time.monotonic()-start,3);save()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--expected-schema-sha256',required=True)
    a=p.parse_args()
    try:r=run(a.source,a.output_dir,a.expected_schema_sha256)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,DiagnosticError) else type(exc).__name__),flush=True)
        return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
