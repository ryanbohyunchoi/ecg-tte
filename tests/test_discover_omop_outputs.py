import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import discover_omop_outputs as D


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()

    def test_nested_table_and_separate_measurement_families(self):
        folder = self.root / 'nested/gold_rbc/measurement/year=2020'
        folder.mkdir(parents=True)
        for name in ['labs_a', 'labs_b', 'vitals_a']:
            (folder / (name + '.parquet')).write_bytes(b'SYNTHETIC_SECRET')
        with patch.object(D, 'schema', return_value={'status': 'available', 'columns': {'measurement_concept_id': 'int64'}}) as read:
            r = D.inspect_root(self.root, 5, 100, 10)
        self.assertEqual(read.call_count, 2)
        self.assertEqual(r['parquet_files_seen'], 3)
        self.assertEqual(len(r['table_directories']), 1)
        self.assertNotIn('SYNTHETIC_SECRET', str(r))

    def test_limits_and_symlink(self):
        for i in range(5):
            (self.root / f'{i}.parquet').touch()
        with patch.object(D, 'schema', return_value={'status': 'available'}) as read:
            r = D.inspect_root(self.root, 2, 3, 1)
        self.assertEqual(r['entries_seen'], 3)
        self.assertEqual(r['status'], 'entry_limit_reached')
        self.assertEqual(read.call_count, 1)
        link = self.base / 'link'
        link.symlink_to(self.root)
        self.assertEqual(D.inspect_root(link, 2, 3, 1)['status'], 'root_symlink_not_followed')

    def test_depth_missing_and_existing_output(self):
        (self.root / 'a/b/c').mkdir(parents=True)
        r = D.inspect_root(self.root, 1, 100, 2)
        self.assertEqual(r['depth_limited_directories'], 1)
        self.assertEqual(D.inspect_root(self.base / 'missing', 1, 10, 1)['status'], 'root_missing_or_not_directory')
        with self.assertRaises(ValueError):
            D.run([self.root], self.root / 'out')
        out = self.base / 'out'
        out.mkdir()
        with self.assertRaises(FileExistsError):
            D.run([self.root], out)


if __name__ == '__main__':
    unittest.main()
