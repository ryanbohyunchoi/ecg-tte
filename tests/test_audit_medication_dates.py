from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_medication_dates as A


class DateAuditTests(unittest.TestCase):
    def test_extended_iso_formats(self):
        for value in ('2024-02-29 12:30', '2024-02-29 12:30:01.1234567', '2024-02-29 1:30 PM'):
            self.assertEqual(A.parse(value)[1], date(2024, 2, 29))
        self.assertEqual(A.parse('2023-02-29 12:30')[0], 'invalid_calendar_or_clock')

    def test_ambiguous_slash_and_timezone_are_not_compared(self):
        self.assertIsNone(A.parse('01/02/2024 1:30 PM')[1])
        self.assertEqual(A.parse('02/29/2024 1:30:01 PM')[1], date(2024, 2, 29))
        self.assertIsNone(A.parse('2024-02-29T12:30:01Z')[1])

    def test_missing_and_masking(self):
        self.assertIsNone(A.parse('NULL')[1])
        self.assertIsNone(A.parse('SECRET_TEXT')[1])
        masked = A.shape('SECRET_TEXT 2024-02-29')
        self.assertNotIn('SECRET', masked)
        self.assertNotIn('2024', masked)

    def test_comparison_boundaries(self):
        self.assertEqual(A.compare(date(2024, 1, 1), date(2024, 1, 1)), 'same_calendar_day')
        self.assertEqual(A.compare(date(2024, 1, 8), date(2024, 1, 1)), 'start_before_order_1_7_days')
        self.assertEqual(A.compare(date(2024, 1, 1), date(2024, 1, 9)), 'start_after_order_8_30_days')
        self.assertEqual(A.compare(None, date(2024, 1, 1)), 'not_comparable')

    def test_counts_privacy_and_no_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'source'; root.mkdir()
            source = root / 'a.txt'
            source.write_text('PAT_MRN_ID\tORDER_INST\tSTART_DATE\tORDER_CLASS\n'
                'SECRET_ID\t2024-02-29 12:30\t2024-02-29\tNormal\n'
                'SECRET_ID\tNULL\t2024-03-01\tNormal\n')
            before = source.read_bytes()
            schema = A.inspect(root, 'a.txt')['schema_sha256']
            r = A.run(root, 'a.txt', base / 'out', schema)
            self.assertEqual(r['comparison_counts'], {'same_calendar_day': 1, 'not_comparable': 1})
            self.assertEqual(r['status'], 'complete_file')
            self.assertEqual(before, source.read_bytes())
            for p in (base / 'out').iterdir():
                for secret in ('SECRET', '2024-02-29', '2024-03-01'):
                    self.assertNotIn(secret, p.read_text())
            r2 = A.run(root, 'a.txt', base / 'prefix', schema, 1)
            self.assertEqual(r2['status'], 'bounded_prefix')
            with self.assertRaises(FileExistsError):
                A.run(root, 'a.txt', base / 'out', schema)

    def test_bad_width_and_schema_invalidate_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'source'; root.mkdir()
            source = root / 'a.txt'
            source.write_text('PAT_MRN_ID\tORDER_INST\tSTART_DATE\nA\tNULL\tNULL\nB\textra\n')
            schema = A.inspect(root, 'a.txt')['schema_sha256']
            r = A.run(root, 'a.txt', base / 'out', schema)
            self.assertEqual(r['reason'], 'row_width_mismatch')
            self.assertNotIn('comparison_counts', r)
            self.assertEqual(A.run(root, 'a.txt', base / 'bad_schema', 'wrong')['reason'], 'schema_hash_mismatch')


if __name__ == '__main__':
    unittest.main()
