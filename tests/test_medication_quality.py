import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import count_medication_evidence as C
from medication_quality import date_kind, number_kind, missing_kind


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        self.path = self.root / 'meds.txt'
        self.output = self.base / 'report'

    def audit(self, text, **kwargs):
        self.path.write_text(text)
        before = self.path.read_bytes()
        schema = C.inspect(self.root, 'meds.txt')['schema_sha256']
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            r = C.run(self.root, 'meds.txt', self.output, max_rows=None,
                      detail_audit=True, record_format='literal-tabs',
                      expected_schema_sha256=schema, **kwargs)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertNotIn('SECRET', stdout.getvalue())
        self.assertNotIn('SECRET', json.dumps(r))
        return r

    def test_calendar_formats_and_candidate_markers(self):
        self.assertEqual(date_kind(' NULL '), 'candidate_marker_NULL')
        self.assertEqual(date_kind('2024-02-29 12:00:00'), 'parseable_iso')
        self.assertEqual(date_kind('2024-02-29 12:00'), 'parseable_iso')
        self.assertEqual(date_kind('2024-02-29 25:00'), 'invalid_calendar_or_clock')
        self.assertEqual(date_kind('2023-02-29'), 'invalid_calendar_or_clock')
        self.assertEqual(date_kind('02/29/2024 1:30:00 PM'), 'parseable_month_first_hypothesis')
        self.assertEqual(date_kind('31/12/2024'), 'invalid_calendar_or_clock')
        self.assertEqual(date_kind('SECRET_DATE'), 'unrecognized_format')
        self.assertEqual(missing_kind('0'), None)

    def test_numeric_validity_not_dispensing(self):
        for value, expected in [('NULL', 'candidate_marker_NULL'), ('', 'blank'),
            ('0', 'zero'), ('-2', 'negative'), ('30', 'positive'),
            ('30 tablets', 'unrecognized_numeric_format'), ('inf', 'unrecognized_numeric_format')]:
            self.assertEqual(number_kind(value), expected)
        self.assertEqual(number_kind('1.5', integer=True), 'noninteger')
        self.assertEqual(number_kind('1.5'), 'positive')

    def test_duplicate_order_conflicts_and_missingness(self):
        r = self.audit('PAT_MRN_ID\tORDER_MED_ID\tQUANTITY_DISPENSED\tEND_DATE\tMEDICATION_ID\n'
            'SECRET_A\tSECRET_O1\t30\tNULL\tD1\n'
            'SECRET_A\tSECRET_O1\t30\tNULL\tD1\n'
            'SECRET_A\tSECRET_O1\t60\tNULL\tD1\n'
            'SECRET_B\tSECRET_O1\t30\tNULL\tD1\n'
            'SECRET_B\tSECRET_O2\t0\t2024-02-29\tD2\n'
            'SECRET_B\tNULL\tbad\tbad\tD2\n')
        self.assertEqual(r['status'], 'complete_file')
        q = r['quality_audit']
        self.assertEqual(q['field_quality']['END_DATE']['candidate_marker_NULL'], 4)
        self.assertEqual(q['field_quality']['QUANTITY_DISPENSED']['positive'], 4)
        o = q['order_key_audit']
        self.assertEqual(o['distinct_nonmarker_order_keys'], 2)
        self.assertEqual(o['repeated_order_keys'], 1)
        self.assertEqual(o['rows_beyond_first_per_order_key'], 3)
        self.assertEqual(o['order_keys_with_differing_audit_fields'], 1)
        self.assertEqual(o['order_keys_linked_to_multiple_nonmarker_patient_keys'], 1)
        self.assertEqual(o['rows_blank_or_candidate_marker_order_key'], 1)
        self.assertIsNone(q['verified_outpatient_fill_patients'])
        self.assertTrue(all(p.is_file() for p in self.output.iterdir()))

    def test_missing_order_field_is_unassessable_not_zero(self):
        r = self.audit('PAT_MRN_ID\tQUANTITY_DISPENSED\nA\t10\n')
        self.assertIsNone(r['quality_audit']['order_key_audit'])

    def test_mode_cross_counts_are_restricted_and_overlap_not_summed(self):
        r = self.audit('PAT_MRN_ID\tORDERING_MODE\tORDER_CLASS\tORDER_SOURCE\n'
                       'A\tOutpatient\tNormal\tClinic\nA\tInpatient\tNormal\tHospital\n')
        self.assertNotIn('Outpatient', json.dumps(r))
        cats = json.loads((self.output / 'restricted_categories.json').read_text())
        self.assertIn('ORDERING_MODE', cats['category_fields'])
        self.assertEqual([g['distinct_nonempty_patient_keys'] for g in cats['groups']], [1, 1])
        self.assertEqual(r['distinct_nonempty_patient_keys'], 1)

    def test_failure_has_no_partial_quality_or_counts(self):
        r = self.audit('PAT_MRN_ID\tORDER_MED_ID\nSECRET_A\tSECRET_1\nB\t2\textra\n')
        self.assertEqual(r['status'], 'failed_counts_invalid')
        self.assertNotIn('quality_audit', r)
        self.assertEqual([p.name for p in self.output.iterdir()], ['summary.json'])

    def test_missing_patient_then_conflicting_patients(self):
        r = self.audit('PAT_MRN_ID\tORDER_MED_ID\nNULL\t1\nA\t1\nB\t1\n')
        self.assertEqual(r['quality_audit']['order_key_audit']['order_keys_linked_to_multiple_nonmarker_patient_keys'], 1)
