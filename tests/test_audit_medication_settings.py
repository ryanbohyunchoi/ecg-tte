import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_medication_settings as A


class MedicationSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        self.out = self.base / 'report'

    def put(self, name='a.parquet'):
        path = self.root / name
        pq.write_table(pa.table({'MRN': ['SECRET_ID'] * 4, 'note': ['SECRET_NOTE'] * 4,
            'setting': ['outpatient', 'inpatient', None, ' '],
            'order_status': ['ordered', 'given', 'given', 'given'],
            'fill_date': ['SECRET_DATE', None, None, None]}), path)
        return path

    def test_privacy_bounds_and_read_only(self):
        p = self.put()
        before = p.read_bytes()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            report = A.run(self.root, self.out, row_limit=3)
        f = report['files'][0]
        self.assertEqual(f['rows_read'], 3)
        self.assertTrue(f['row_limit_reached'])
        self.assertEqual(f['field_counts']['setting']['null'], 1)
        self.assertEqual(f['field_counts']['fill_date']['value'], 1)
        self.assertNotIn('outpatient', json.dumps(report))
        for path in self.out.iterdir():
            self.assertNotIn('SECRET', path.read_text())
        self.assertNotIn('SECRET', stdout.getvalue())
        self.assertEqual(p.read_bytes(), before)
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o700)

    def test_categories_and_cross_counts_cap_explicitly(self):
        self.put()
        report = A.run(self.root, self.out, category_limit=1)
        f = report['files'][0]
        self.assertEqual(f['field_counts']['setting']['uncatalogued_records'], 3)
        self.assertEqual(f['cross_uncatalogued_records'], 3)
        raw = json.loads((self.out / 'restricted_values.json').read_text())
        self.assertEqual(raw['files'][0]['categories']['setting'][0]['value'], 'outpatient')

    def test_refuse_overwrite_and_source_output(self):
        self.put()
        with self.assertRaises(ValueError):
            A.run(self.root, self.root / 'report')
        A.run(self.root, self.out)
        with self.assertRaises(FileExistsError):
            A.run(self.root, self.out)

    def test_symlinks_skipped_and_file_cap_reported(self):
        p = self.put()
        self.put('b.parquet')
        (self.root / 'link.parquet').symlink_to(p)
        r = A.run(self.root, self.out, file_limit=1)
        self.assertEqual(r['files_discovered'], 2)
        self.assertTrue(r['file_limit_reached'])
        self.assertEqual(len(r['files']), 1)

    def test_failed_file_is_not_reported_as_complete(self):
        (self.root / 'bad.parquet').write_text('SECRET')
        r = A.run(self.root, self.out)
        self.assertEqual(r['status'], 'inspection_incomplete')
        self.assertNotIn('SECRET', json.dumps(r))

    def test_blank_and_null_not_conflated(self):
        self.put()
        r = A.run(self.root, self.out)
        counts = r['files'][0]['field_counts']['setting']
        self.assertEqual((counts['null'], counts['blank'], counts['value']), (1, 1, 2))


if __name__ == '__main__':
    unittest.main()
