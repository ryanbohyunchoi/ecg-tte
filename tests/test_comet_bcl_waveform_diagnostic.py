import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_comet_bcl_waveforms import probe
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
    def test_missing_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(probe(Path(tmp)/'absent',{'fileID':{'x'}})['exists'])
if __name__=='__main__':unittest.main()
