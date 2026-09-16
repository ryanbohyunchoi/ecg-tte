import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import profile_jdat_mapping as P
from inspect_jdat_headers import inspect


class MappingProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        self.output = self.base / 'out'
        self.headers = self.base / 'headers.json'

    def source(self, rows, header='PAT_ID|MEDICATION_ID|ORDER_INST|COMMENTS\n'):
        self.file = self.root / 'table.txt'
        self.file.write_text(header + rows)
        entry = {'relative_path': 'table.txt', **inspect(self.root, 'table.txt')}
        self.headers.write_text(json.dumps({'source_root': str(self.root), 'files': [entry]}))

    def run_audit(self, **kwargs):
        self.console = io.StringIO()
        with contextlib.redirect_stdout(self.console):
            return P.run(self.headers, [1], self.output, **kwargs)

    def test_counts_and_no_values_in_summary_or_console(self):
        self.source('SYNTHETIC_PATIENT|123|SYNTHETIC_DATE|SECRET_NOTE\n'
                    'SYNTHETIC_PATIENT2|123||OTHER_NOTE\n'
                    'SYNTHETIC_PATIENT3|456||OTHER_NOTE\n')
        result = self.run_audit()
        fields = result['files'][0]['fields']
        self.assertEqual(fields['MEDICATION_ID'], {'empty': 0, 'nonempty': 3, 'distinct_raw_cells': 2})
        self.assertEqual(fields['ORDER_INST']['empty'], 2)
        for secret in ['SYNTHETIC_PATIENT', 'SYNTHETIC_DATE', 'SECRET_NOTE']:
            self.assertNotIn(secret, json.dumps(result) + self.console.getvalue())
        with sqlite3.connect(self.output / 'restricted_code_counts.sqlite') as db:
            self.assertEqual(db.execute('SELECT source_value, record_count FROM codes ORDER BY source_value').fetchall(),
                             [('123', 2), ('456', 1)])

    def test_prefix_is_not_claimed_complete_or_random(self):
        self.source('p|123||n\np|456||n\n')
        result = self.run_audit(max_rows=1)
        self.assertEqual(result['files'][0]['status'], 'bounded_prefix')
        self.assertEqual(result['files'][0]['rows_accepted'], 1)

    def test_multiline_quoted_note_and_width_failure(self):
        self.source('p|123||"note\ncontinued"\np|456||n\n')
        result = self.run_audit()
        self.assertEqual(result['files'][0]['rows_accepted'], 2)
        self.assertEqual(result['files'][0]['status'], 'complete_file')

    def test_failed_file_clears_catalog_and_counts(self):
        self.source('p|123||n\np|456|too_few\n')
        result = self.run_audit()
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['files'][0]['counts_valid'])
        self.assertEqual(result['files'][0]['fields'], {})
        with sqlite3.connect(self.output / 'restricted_code_counts.sqlite') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM codes').fetchone()[0], 0)

    def test_oversized_and_unclosed_record_fail_without_leak(self):
        self.source('p|123||"' + 'SENSITIVE' * 100 + '\n')
        result = self.run_audit(max_record_bytes=128)
        self.assertEqual(result['files'][0]['reason'], 'record_exceeds_byte_limit')
        self.assertNotIn('SENSITIVE', json.dumps(result))

    def test_schema_change_rejected(self):
        self.source('p|123||n\n')
        self.file.write_text('PAT_ID|OTHER\np|x\n')
        result = self.run_audit()
        self.assertEqual(result['files'][0]['reason'], 'schema_changed_since_header_report')

    def test_existing_output_and_source_overlap_refused(self):
        self.source('p|123||n\n')
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_audit()
        with self.assertRaises(P.AuditError):
            P.run(self.headers, [1], self.root / 'out')

    def test_symlink_replacement_refused(self):
        self.source('p|123||n\n')
        other = self.base / 'other.txt'
        self.file.rename(other)
        self.file.symlink_to(other)
        result = self.run_audit()
        self.assertEqual(result['files'][0]['reason'], 'symlink_not_followed')

    def test_invalid_selection_and_limits(self):
        self.source('p|123||n\n')
        for indices in [[], [0], [2], [1, 1]]:
            with self.assertRaises(P.AuditError):
                P.run(self.headers, indices, self.output)
        with self.assertRaises(P.AuditError):
            self.run_audit(max_rows=0)


if __name__ == '__main__':
    unittest.main()
