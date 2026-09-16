import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_existing_omop as A


class ExistingOmopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'existing'
        self.root.mkdir()
        self.output = self.base / 'report'

    def test_manifest_allowlist_and_source_unchanged(self):
        folder = self.root / 'audit/runs/run1'
        folder.mkdir(parents=True)
        p = folder / 'manifest.json'
        p.write_text(json.dumps({'run_id': 'run1', 'errors': {'4': 'SECRET_ERROR'}, 'steps': {
            '4': {'silver': {'source_files': ['synthetic/Meds.txt'], 'kept': 10},
                  'gold': {'output_counts': {'drug_exposure': 8}, 'top_unmapped': 'SECRET_VALUES'}}}}))
        before = p.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            result = A.run(self.root, self.output)
        text = json.dumps(result)
        self.assertNotIn('SECRET', text)
        self.assertIn('synthetic/Meds.txt', text)
        self.assertEqual(p.read_bytes(), before)
        self.assertEqual(result['manifests'][0]['error_step_ids'], ['4'])
        self.assertFalse(result['data_rows_read'])

    def test_schema_bound_and_symlink_not_read(self):
        folder = self.root / 'gold/measurement'
        folder.mkdir(parents=True)
        for i in range(5):
            (folder / f'{i}.parquet').write_bytes(b'synthetic')
        (folder / 'link.parquet').symlink_to(folder / '0.parquet')
        with patch.object(A, 'schema', return_value={'status': 'available'}) as read, contextlib.redirect_stdout(io.StringIO()):
            result = A.run(self.root, self.output, schema_limit=2)
        self.assertEqual(read.call_count, 2)
        self.assertEqual(result['gold_tables']['measurement']['parquet_files'], 5)

    def test_output_overlap_and_overwrite_refused(self):
        with self.assertRaises(ValueError):
            A.run(self.root, self.root / 'report')
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            A.run(self.root, self.output)

    def test_invalid_manifest_does_not_echo_contents(self):
        p = self.base / 'bad.json'
        p.write_text('SECRET_INVALID_JSON')
        result = A.manifest_summary(p)
        self.assertEqual(result['status'], 'unavailable')
        self.assertNotIn('SECRET', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
