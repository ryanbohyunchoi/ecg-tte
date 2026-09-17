import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from relocate_audit_reports import relocate


class RelocateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.home = self.base/'home'; self.home.mkdir()
        self.dest = self.base/'raid'/'audits'

    def folder(self, name, status='complete_file'):
        p=self.home/name; (p/'report').mkdir(parents=True)
        (p/'report'/'summary.json').write_text(json.dumps({'status':status}))
        return p

    def test_moves_only_finished_audits_preserving_bytes(self):
        p=self.folder('medication-dates-finished')
        before=(p/'report'/'summary.json').read_bytes()
        unrelated=self.folder('unrelated-data')
        relocate([self.home],self.dest,True)
        self.assertFalse(p.exists()); self.assertTrue(unrelated.exists())
        self.assertEqual((self.dest/p.name/'report'/'summary.json').read_bytes(),before)

    def test_skips_active_missing_metadata_and_existing_destinations(self):
        active=self.folder('medication-quality-active','running')
        existing=self.folder('jdat-headers-existing')
        self.dest.mkdir(parents=True); (self.dest/existing.name).mkdir()
        unknown=self.home/'medication-format-unknown'; unknown.mkdir()
        r=relocate([self.home],self.dest,True)
        self.assertTrue(all(action.startswith('SKIP') for _,action in r))
        self.assertTrue(all(p.exists() for p in (active,existing,unknown)))

    def test_preview_and_symlink(self):
        p=self.folder('medication-dates-complete')
        (self.home/'medication-dates-link').symlink_to(p)
        r=relocate([self.home],self.dest)
        self.assertEqual(len(r),1); self.assertEqual(r[0][1],'WOULD_MOVE')
        self.assertTrue(p.exists()); self.assertFalse(self.dest.exists())

    def test_overlapping_paths_refused(self):
        with self.assertRaises(ValueError): relocate([self.home],self.home/'audit',True)


if __name__ == '__main__': unittest.main()
