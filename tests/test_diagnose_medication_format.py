import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import diagnose_medication_format as D


class FormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        self.path = self.root / 'meds.txt'

    def audit(self, body, limit=500000):
        self.path.write_text('PAT_MRN_ID\tSIG\n' + body)
        before = self.path.read_bytes()
        previous = csv.field_size_limit()
        r = D.run(self.root, 'meds.txt', self.base / 'report', limit)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(csv.field_size_limit(), previous)
        self.assertNotIn('SECRET', json.dumps(r))
        return r

    def test_quote_conflict_without_tab_width_mismatch(self):
        r = self.audit('SECRET_A\tok\nSECRET_B\t"SECRET_TEXT"suffix\n')
        self.assertEqual(r['strict_csv']['reason'], 'csv_unexpected_character_after_closing_quote')
        self.assertEqual(r['strict_csv']['records_parsed'], 1)
        self.assertEqual(r['literal_delimiter_physical_lines']['matching_width'], 2)

    def test_valid_quoted_multiline_is_not_labeled_as_correct_literal_format(self):
        r = self.audit('SECRET_A\t"line1\nline2"\n')
        self.assertEqual(r['strict_csv']['status'], 'reached_eof')
        self.assertEqual(r['strict_csv']['records_parsed'], 1)
        self.assertEqual(r['literal_delimiter_physical_lines']['too_few_columns'], 1)

    def test_extra_tab_and_bounded_scope(self):
        r = self.audit('SECRET_A\ttext\textra\nSECRET_B\ttext\n', limit=1)
        self.assertEqual(r['strict_csv']['reason'], 'row_width_mismatch')
        self.assertEqual(r['literal_delimiter_physical_lines']['too_many_columns'], 1)
        self.assertEqual(r['literal_delimiter_physical_lines']['status'], 'bounded_prefix')

    def test_unterminated_quote(self):
        r = self.audit('SECRET_A\t"unfinished\n')
        self.assertEqual(r['strict_csv']['reason'], 'csv_unterminated_quoted_record')

    def test_record_byte_bound_is_preserved_in_both_passes(self):
        r = self.audit('SECRET_A\t' + 'x' * 1048576 + '\n')
        self.assertEqual(r['strict_csv']['reason'], 'record_exceeds_byte_limit')
        self.assertEqual(r['literal_delimiter_physical_lines']['reason'], 'record_exceeds_byte_limit')

    def test_reject_symlink_and_output_reuse(self):
        self.path.write_text('PAT_MRN_ID\tSIG\nA\tb\n')
        (self.root / 'link.txt').symlink_to(self.path)
        r = D.run(self.root, 'link.txt', self.base / 'report')
        self.assertEqual(r['status'], 'diagnostic_failed')
        with self.assertRaises(FileExistsError):
            D.run(self.root, 'meds.txt', self.base / 'report')


if __name__ == '__main__':
    unittest.main()
