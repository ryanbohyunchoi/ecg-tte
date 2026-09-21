#!/usr/bin/env python3
"""Read 20 KiB of a diagnosed malformed tail; export byte counts, never text."""
import argparse
import json
import os
from pathlib import Path

EXPECTED_SIZE=66081132812
TAIL_BYTES=15529283887
WINDOW=4096


def sample(source, expected_size=EXPECTED_SIZE, tail_bytes=TAIL_BYTES, window=WINDOW):
    before=source.stat()
    if before.st_size!=expected_size or not 0<tail_bytes<=expected_size or not 0<window<=4096:
        raise ValueError('source_size_or_sample_contract_mismatch')
    start=expected_size-tail_bytes
    width=min(window,tail_bytes)
    offsets=sorted({start+(tail_bytes-width)*i//4 for i in range(5)})
    samples=[]
    with source.open('rb') as stream:
        for offset in offsets:
            stream.seek(offset);data=stream.read(width)
            if len(data)!=width:raise ValueError('source_short_read')
            samples.append(dict(file_offset_bytes=offset,bytes_read=len(data),nul_bytes=data.count(b'\x00'),
                tab_bytes=data.count(b'\t'),lf_bytes=data.count(b'\n'),cr_bytes=data.count(b'\r'),
                printable_ascii_bytes=sum(32<=b<=126 for b in data),high_bytes=sum(b>=128 for b in data),
                all_nul=all(b==0 for b in data)))
    after=source.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('source_changed')
    return dict(status='bounded_sample_complete',restricted_until_reviewed=True,source_changed=False,
                interpretation='Five windows only, no raw text. Cannot establish full-tail contents, completeness or permission to discard.',
                malformed_tail_start_offset=start,total_bytes_read=sum(x['bytes_read'] for x in samples),samples=samples)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    try:
        source,output=a.source,a.output_dir
        if not source.is_absolute() or not output.is_absolute() or source.is_symlink() or output.is_symlink():
            raise ValueError('absolute_nonsymlink_paths_required')
        source,output=source.resolve(),output.resolve()
        if source.parent==output or source.parent in output.parents or output in source.parents:
            raise ValueError('output_source_overlap')
        os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
        result=sample(source)
        (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    except Exception as exc:
        print('Stopped: '+type(exc).__name__);return 1
    print('Review '+str(output/'summary.json')+' on H100. No source values exported.')
    return 0

if __name__=='__main__':raise SystemExit(main())
