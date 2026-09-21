import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_shared_tables as B
import build_psm_shared_tables as E


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'raw'
        self.root.mkdir()
        self.selected = []
        for year in ('2025', '2026'):
            relative = f'Data-{year}-04-03/CarDS_2435227_Hosp_Enc_Labs_1.txt'
            path = self.root / relative
            path.parent.mkdir()
            path.write_bytes(b'PAT_MRN_ID\tRESULT_TIME\tORD_VALUE\tORD_NUM_VALUE\n'
                             b' 001 \t2024-01-01 12:30\t<5\t9999999\n'
                             b'A001\tNULL\tSECRET_SYNTHETIC\tNULL\n')
            schema = B.inspect(self.root, relative)['schema_sha256']
            self.selected.append((relative, 'labs_' + year, schema))
        self.output = self.base / 'extension'

    def specs(self, terminal=False):
        with patch.object(E, 'sources', return_value=self.selected):
            return E.extension_sources(self.root, terminal)

    def run_build(self, specs, resume=False):
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            result = B.build(specs, self.output, resume=resume, batch_rows=1)
        self.assertNotIn('SECRET', capture.getvalue())
        return result

    def test_preserves_both_values_separate_deliveries_and_eof_accounting(self):
        specs = self.specs()
        result = self.run_build(specs)
        self.assertEqual(len(result['stages']), 2)
        for spec in specs:
            stage = result['stages'][spec['id']]
            self.assertTrue(stage['reached_eof'])
            self.assertEqual(stage['physical_lines'], 2)
            self.assertIsNone(stage['source_spec']['expected_rows'])
            table = B.open_table(self.output, spec['id'], True).to_table().to_pydict()
            self.assertEqual(table['ORD_VALUE'], ['<5', 'SECRET_SYNTHETIC'])
            self.assertEqual(table['ORD_NUM_VALUE'], ['9999999', 'NULL'])
            self.assertEqual(table['__patient_key'], ['001', 'A001'])
            self.assertEqual(table['__source_id'], [spec['id']] * 2)
        self.assertNotIn('SECRET', (self.output / 'summary.json').read_text())
        with patch.object(B, 'build_stage', side_effect=AssertionError('must reuse')):
            self.run_build(specs, resume=True)

    def test_terminal_blank_is_opt_in_and_interior_multiple_whitespace_fail(self):
        spec = self.specs(True)[0]
        path = Path(spec['path'])
        original = path.read_bytes()
        for suffix in (b'\n', b'\r\n'):
            path.write_bytes(original + suffix)
            target = self.base / ('ok' + str(len(suffix)))
            stage = B.build_stage(spec, target, 2)
            self.assertEqual((stage['rows'], stage['physical_lines'], stage['terminal_empty_lines']), (2, 3, 1))
        for i, suffix in enumerate((b'\n\n', b' \n', b'\nBAD\n', b'\xef\xbb\xbf\n')):
            path.write_bytes(original + suffix)
            with self.assertRaises(B.BuildError):
                B.build_stage(spec, self.base / f'bad{i}', 2)
        path.write_bytes(original + b'\n')
        spec['terminal_empty'] = False
        with self.assertRaisesRegex(B.BuildError, 'row_width_mismatch'):
            B.build_stage(spec, self.base / 'strict', 2)

    def test_late_bad_row_fails_without_publishing_and_keeps_first_stage(self):
        specs = self.specs()
        path = Path(specs[1]['path'])
        with path.open('ab') as stream:
            stream.write(b'BROKEN\n')
        with self.assertRaisesRegex(B.BuildError, 'row_width_mismatch'):
            self.run_build(specs)
        self.assertTrue((self.output / specs[0]['id'] / 'manifest.json').exists())
        self.assertFalse((self.output / specs[1]['id']).exists())
        self.assertEqual(json.loads((self.output / 'summary.json').read_text())['status'], 'failed')
        with self.assertRaises(B.BuildError):
            B.open_table(self.output, specs[0]['id'])

    def test_unknown_counts_require_explicit_policy_and_empty_source_fails(self):
        spec = self.specs()[0]
        del spec['row_count_policy']
        with self.assertRaisesRegex(B.BuildError, 'missing_expected_rows_policy'):
            B.build_stage(spec, self.base / 'missingpolicy', 2)
        spec['row_count_policy'] = 'discover_at_eof'
        path = Path(spec['path'])
        path.write_bytes(path.read_bytes().split(b'\n')[0] + b'\n')
        with self.assertRaisesRegex(B.BuildError, 'empty_source'):
            B.build_stage(spec, self.base / 'empty', 2)

    def test_changed_schema_stops_preflight(self):
        path = self.root / self.selected[1][0]
        path.write_bytes(path.read_bytes().replace(b'ORD_NUM_VALUE', b'OTHER_COLUMN'))
        with self.assertRaisesRegex(B.BuildError, 'extension_schema_mismatch'):
            self.specs()
        self.assertFalse(self.output.exists())

    def test_real_selection_has_19_unique_sources_excludes_missing_patients(self):
        from profile_psm_sources import sources
        selected = sources()
        self.assertEqual(len(selected), 19)
        self.assertEqual(len({s[0] for s in selected}), 19)
        self.assertNotIn('Data-2026-04-15/CarDS_2435227_Patients.txt', [s[0] for s in selected])

if __name__ == '__main__':
    unittest.main()
