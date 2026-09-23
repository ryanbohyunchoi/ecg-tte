import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_comet_bcl_waveforms import probe, probe_nested
class ProbeTests(unittest.TestCase):
    def test_suffix_symlink_and_private_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'synthetic.npy').write_bytes(b'test')
            (root/'link.npy').symlink_to(root/'synthetic.npy')
            (root/'broken.npy').symlink_to(root/'absent')
            result=probe(root,{'fileID':{'synthetic.npy','link','broken'}})
            c=result['candidate_path_counts']
            self.assertEqual(c['fileID:as_given:nonempty_nonsymlink_file'],1)
            self.assertEqual(c['fileID:append_npy:nonempty_file'],1)
            self.assertNotIn('fileID:append_npy:nonempty_nonsymlink_file',c)
            self.assertEqual(c['fileID:append_npy:broken_or_nonfile_symlink'],1)
            self.assertNotIn('synthetic',str(result));self.assertNotIn('broken.npy',str(result))
    def test_nested_duplicates_limits_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for folder in ('2020_01','2020_02'):
                (root/folder).mkdir();(root/folder/'synthetic.npy').write_bytes(b'x')
            (root/'alias').symlink_to(root/'2020_01',target_is_directory=True)
            r=probe_nested(root,{'fileID':{'synthetic'}})
            self.assertEqual(r['candidate_counts']['fileID:append_npy']['multiple_paths'],1)
            self.assertTrue(r['scan_complete_within_nonsymlink_tree'])
            self.assertEqual(r['qc']['symlinks_not_followed'],1)
            self.assertNotIn('synthetic',str(r))
            self.assertFalse(probe_nested(root,{'fileID':{'synthetic'}},max_entries=1)['scan_complete_within_nonsymlink_tree'])
            self.assertFalse(probe_nested(root,{'fileID':{'synthetic'}},max_depth=0)['scan_complete_within_nonsymlink_tree'])

    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(probe(Path(tmp)/'absent',{'fileID':{'x'}})['exists'])
if __name__=='__main__':unittest.main()
