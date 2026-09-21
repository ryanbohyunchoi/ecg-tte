#!/usr/bin/env python3
"""Build separate raw-preserving RBC PSM source extensions on H100."""
import argparse
from pathlib import Path

from build_shared_tables import BuildError, build
from inspect_jdat_headers import inspect
from profile_psm_sources import DATES, sources


def extension_sources(root, allow_terminal_empty=False):
    """Preflight every selected schema before starting the large conversion."""
    root = Path(root)
    if not root.is_absolute():
        raise BuildError('absolute_source_root_required')
    specs = []
    for relative, domain, schema in sources():
        path = root / relative
        header = inspect(root, relative)
        if header.get('status') != 'header_candidate' or header.get('delimiter') != 'tab':
            raise BuildError('extension_header_unavailable')
        if header['schema_sha256'] != schema:
            raise BuildError('extension_schema_mismatch')
        delivery, filename = relative.split('/')
        source_id = delivery.replace('-', '_') + '_' + filename.removeprefix('CarDS_2435227_').removesuffix('.txt').lower()
        specs.append(dict(
            id=source_id, path=str(path), format='literal_tabs', schema_hash=schema,
            expected_rows=None, row_count_policy='discover_at_eof', key='PAT_MRN_ID',
            terminal_empty=allow_terminal_empty,
            dates=[c for c in header['columns'] if c in DATES],
            delivery=delivery, domain=domain, relative_path=relative,
            extension_contract='psm_raw_sources_v1',
            interpretation='Raw source values; no unit conversion, numeric-value selection, delivery union or clinical normalization.'
        ))
    return specs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--allow-terminal-empty-line', action='store_true',
                   help='Explicitly allow at most one exact empty LF/CRLF line at verified EOF per source; count it separately.')
    args = p.parse_args()
    try:
        specs = extension_sources(args.root, args.allow_terminal_empty_line)
        result = build(specs, args.output_dir, resume=args.resume)
    except Exception as exc:
        print('Extension stopped: ' + (str(exc) if isinstance(exc, BuildError) else type(exc).__name__), flush=True)
        return 1
    print('PSM source extension complete. Keep tables and manifests on H100.', flush=True)
    for name, stage in result['stages'].items():
        print(name + ': ' + str(stage['rows']) + ' rows', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
