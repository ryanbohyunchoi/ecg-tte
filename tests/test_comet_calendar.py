from datetime import date
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from restrict_comet_calendar import partition
from build_shared_tables import BuildError


class CalendarTests(unittest.TestCase):
    def test_boundary_and_missingness(self):
        rows = [dict(patient_key=str(i), index_date=d, index_year=d.year, lvef=None)
                for i, d in enumerate([date(2014, 12, 31), date(2015, 1, 1), date(2025, 1, 1)])]
        kept, excluded = partition(rows)
        self.assertEqual(kept, rows[1:])
        self.assertEqual(excluded, rows[:1])
        self.assertTrue(all(r['lvef'] is None for r in kept))

    def test_invalid_dates_and_duplicates(self):
        row = dict(patient_key='synthetic', index_date=date(2015, 1, 1), index_year=2015)
        with self.assertRaisesRegex(BuildError, 'duplicate'):
            partition([row, row])
        with self.assertRaisesRegex(BuildError, 'inconsistent'):
            partition([{**row, 'index_year': 2014}])

    def test_artifact_filtering_and_parent_integrity(self):
        import tempfile
        import pyarrow as pa
        import pyarrow.parquet as pq
        from restrict_comet_calendar import run, FIELDS
        from build_shared_tables import atomic_json, digest
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            source.mkdir()
            rows = [dict(patient_key=str(i), treatment_arm='synthetic_arm',
                         index_date=d, index_year=d.year, **{f: None for f in FIELDS})
                    for i, d in enumerate([date(2014, 12, 31), date(2015, 1, 1)])]
            pq.write_table(pa.Table.from_pylist(rows), source / 'restricted_baseline_resolution.parquet')
            for name in ['restricted_feature_status.parquet', 'restricted_lab_selected_lineage.parquet']:
                pq.write_table(pa.table({'patient_key': ['0', '1']}), source / name)
            atomic_json(source / 'lab_mapping_report.json', {})
            version = 'comet_baseline_resolution_v2_mapped_labs'
            atomic_json(source / 'manifest.json', dict(version=version, outputs={p.name: digest(p) for p in source.iterdir()}))
            atomic_json(source / 'summary.json', dict(version=version, status='complete_resolution_candidate',
                        counts_valid=True, rows=2, denominators={'synthetic_arm': 2}))
            before = {p.name: digest(p) for p in source.iterdir()}
            output = Path(tmp) / 'output'
            result = run(source, output)
            self.assertEqual(result['rows'], 1)
            self.assertFalse(result['ready_for_mice'])
            for name in ['restricted_baseline_resolution.parquet', 'restricted_feature_status.parquet', 'restricted_lab_selected_lineage.parquet']:
                self.assertEqual(pq.read_table(output / name)['patient_key'].to_pylist(), ['1'])
            self.assertEqual(before, {p.name: digest(p) for p in source.iterdir()})
            with self.assertRaises(FileExistsError):
                run(source, output)
            atomic_json(source / 'lab_mapping_report.json', {'changed': True})
            with self.assertRaisesRegex(BuildError, 'artifact_changed'):
                run(source, Path(tmp) / 'other')
