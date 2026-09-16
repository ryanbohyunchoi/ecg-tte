import contextlib
import csv
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

    def test_long_unused_field_passes_without_changing_global_csv_limit(self):
        previous = csv.field_size_limit(131072)
        self.addCleanup(csv.field_size_limit, previous)
        self.put('PAT_MRN_ID\tREFILLS\tSIG\nSECRET_A\t3\t' + 'x' * 200000 + '\n')
        r = self.run_audit(max_rows=None)
        self.assertEqual(r['status'], 'complete_file')
        self.assertEqual(r['distinct_nonempty_patient_keys'], 1)
        self.assertEqual(csv.field_size_limit(), 131072)
        self.assertNotIn('SECRET', json.dumps(r))

    def test_explicit_field_limit_reports_safe_reason(self):
        self.put('PAT_MRN_ID\tSIG\nSECRET_A\t' + 'x' * 200 + '\n')
        r = self.run_audit(max_rows=None, max_field_chars=128)
        self.assertEqual(r['reason'], 'csv_field_exceeds_character_limit')
        self.assertEqual(r['failure_stage'], 'record_parse')
        self.assertFalse(r['counts_valid'])
        self.assertNotIn('distinct_nonempty_patient_keys', r)

    def test_unterminated_quote_is_not_skipped_or_reinterpreted(self):
        self.put('PAT_MRN_ID\tSIG\nA\tok\nSECRET_B\t"SECRET_TEXT\n')
        r = self.run_audit(max_rows=None)
        self.assertEqual(r['reason'], 'csv_unterminated_quoted_record')
        self.assertEqual(r['diagnostic_records_processed'], 1)
        self.assertNotIn('SECRET', json.dumps(r))
        self.assertNotIn('distinct_nonempty_patient_keys', r)

    def test_multiline_record_and_record_byte_limit(self):
        self.put('PAT_MRN_ID\tSIG\nA\t"line one\nline two"\n')
        r = self.run_audit(max_rows=None)
        self.assertEqual(r['rows_read'], 1)
        self.put('PAT_MRN_ID\tSIG\nA\t' + 'x' * 256 + '\n')
        r = C.run(self.root, 'meds.txt', self.base / 'report2', max_rows=None,
                  max_record_bytes=128, max_field_chars=128)
        self.assertEqual(r['reason'], 'record_exceeds_byte_limit')

    def test_arbitrary_exception_messages_are_never_returned(self):
        for exc in (csv.Error('SECRET_TEXT'), ValueError('SECRET_TEXT'),
                    C.CountError('SECRET_TEXT'), C.AuditError('SECRET_TEXT')):
            self.assertNotIn('SECRET', C.failure_reason(exc))

    def literal(self, **kwargs):
        schema = C.inspect(self.root, 'meds.txt')['schema_sha256']
        return self.run_audit(max_rows=None, record_format='literal-tabs',
                              expected_schema_sha256=schema, **kwargs)

    def test_literal_quotes_are_preserved_without_merging_lines(self):
        self.put('PAT_MRN_ID\tREFILLS\tSIG\nA\t3\t"text"suffix\nA\t2\tplain\nB\t1\t\n')
        r = self.literal()
        self.assertEqual(r['status'], 'complete_file')
        self.assertEqual(r['rows_read'], 3)
        self.assertEqual(r['distinct_nonempty_patient_keys'], 2)
        self.assertIsNone(r['verified_outpatient_fill_patients'])
        self.assertEqual(r['parser']['format_semantics'], 'provisional_literal_tab_hypothesis')

    def test_literal_requires_matching_schema_and_tab_delimiter(self):
        self.put('PAT_MRN_ID\tREFILLS\nA\t2\n')
        with self.assertRaises(ValueError):
            self.run_audit(record_format='literal-tabs')
        r = self.run_audit(record_format='literal-tabs', expected_schema_sha256='wrong')
        self.assertEqual(r['reason'], 'schema_hash_mismatch')
        self.put('PAT_MRN_ID,REFILLS\nA,2\n')
        schema = C.inspect(self.root, 'meds.txt')['schema_sha256']
        r = C.run(self.root, 'meds.txt', self.base / 'report2', record_format='literal-tabs',
                  expected_schema_sha256=schema)
        self.assertEqual(r['reason'], 'literal_tabs_requires_tab_header')

    def test_literal_multiline_and_extra_tabs_still_fail(self):
        self.put('PAT_MRN_ID\tSIG\nA\t"line1\nline2"\n')
        r = self.literal()
        self.assertEqual(r['reason'], 'row_width_mismatch')
        self.assertNotIn('distinct_nonempty_patient_keys', r)

    def test_literal_field_limit_and_quoted_keys(self):
        self.put('PAT_MRN_ID\tSIG\n"A"\ttext\nA\ttext\n')
        r = self.literal()
        self.assertEqual(r['distinct_nonempty_patient_keys'], 2)
        self.assertEqual(r['rows_with_quotes_in_patient_key'], 1)
        self.put('PAT_MRN_ID\tSIG\nA\t' + 'x' * 200 + '\n')
        schema = C.inspect(self.root, 'meds.txt')['schema_sha256']
        r = C.run(self.root, 'meds.txt', self.base / 'report2', record_format='literal-tabs',
                  expected_schema_sha256=schema, max_field_chars=128)
        self.assertEqual(r['reason'], 'literal_field_exceeds_character_limit')


if __name__ == '__main__':
    unittest.main()
