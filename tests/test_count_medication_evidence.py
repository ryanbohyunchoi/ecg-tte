import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import count_medication_evidence as C


class EvidenceCountsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        self.source = self.root / 'meds.txt'
        self.out = self.base / 'report'

    def put(self, text):
        self.source.write_text(text)

    def run_audit(self, **kwargs):
        return C.run(self.root, 'meds.txt', self.out, **kwargs)

    def test_full_counts_duplicate_patients_and_no_verified_fill_inference(self):
        self.put('PAT_MRN_ID\tORDER_STATUS\tFILL_DATE\tDAYS_SUPPLY\n'
                 'SECRET_A\tDispensed\tSECRET_DATE\t30\n'
                 'SECRET_A\tOrdered\t\t\n'
                 'SECRET_B\tDispensed\tinvalid-date\tinvalid-number\n'
                 '\tDispensed\t\t\n')
        before = self.source.read_bytes()
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            r = self.run_audit(max_rows=None)
        self.assertEqual(r['status'], 'complete_file')
        self.assertEqual(r['rows_read'], 4)
        self.assertEqual(r['distinct_nonempty_patient_keys'], 2)
        self.assertEqual(r['rows_missing_patient_key'], 1)
        self.assertEqual(r['patients_with_candidate_fill_date'], 2)
        self.assertIsNone(r['verified_outpatient_fill_patients'])
        groups = json.loads((self.out / 'restricted_categories.json').read_text())['groups']
        self.assertEqual([g['distinct_nonempty_patient_keys'] for g in groups], [2, 1])
        self.assertEqual(self.source.read_bytes(), before)
        for path in self.out.iterdir():
            self.assertTrue(path.is_file())
            self.assertNotIn('SECRET', path.read_text())
        self.assertNotIn('SECRET', captured.getvalue())
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o700)

    def test_refill_authorization_and_missing_fields_do_not_mean_zero_fills(self):
        self.put('PAT_MRN_ID\tREFILLS\tORDER_STATUS\nA\t3\tDispensed\n')
        r = self.run_audit(max_rows=None)
        self.assertIsNone(r['patients_with_candidate_fill_date'])
        self.assertIsNone(r['patients_with_candidate_supply'])
        self.assertIsNone(r['verified_outpatient_fill_patients'])
        self.assertEqual(r['field_presence']['REFILLS']['nonempty'], 1)

    def test_prefix_and_category_cap_are_explicit(self):
        self.put('PAT_MRN_ID\tORDER_STATUS\nA\tone\nB\ttwo\nC\tthree\n')
        r = self.run_audit(max_rows=2, category_limit=1)
        self.assertEqual(r['status'], 'bounded_prefix')
        self.assertFalse(r['reached_eof'])
        self.assertEqual(r['distinct_nonempty_patient_keys'], 2)
        self.assertEqual(r['category_omitted_records'], 1)

    def test_malformed_row_invalidates_counts_and_cleans_identifier_storage(self):
        self.put('PAT_MRN_ID\tORDER_STATUS\nSECRET_A\tone\nSECRET_B\ttwo\textra\n')
        r = self.run_audit(max_rows=None)
        self.assertEqual(r['status'], 'failed_counts_invalid')
        self.assertNotIn('distinct_nonempty_patient_keys', r)
        self.assertEqual([p.name for p in self.out.iterdir()], ['summary.json'])
        self.assertNotIn('SECRET', json.dumps(r))

    def test_refuses_output_reuse_and_source_output(self):
        self.put('PAT_MRN_ID\tREFILLS\nA\t1\n')
        with self.assertRaises(ValueError):
            C.run(self.root, 'meds.txt', self.root / 'report')
        self.run_audit()
        with self.assertRaises(FileExistsError):
            self.run_audit()

    def test_missing_patient_column_and_symlink_fail_closed(self):
        self.put('PAT_ID\tREFILLS\nA\t1\n')
        self.assertEqual(self.run_audit()['status'], 'failed_counts_invalid')
        link = self.root / 'link.txt'
        link.symlink_to(self.source)
        r = C.run(self.root, 'link.txt', self.base / 'report2')
        self.assertEqual(r['status'], 'failed_counts_invalid')


if __name__ == '__main__':
    unittest.main()
