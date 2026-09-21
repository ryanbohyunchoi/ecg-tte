from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_lab_tail_bytes import sample

class TailSampleTests(unittest.TestCase):
    def test_samples_zero_tail_without_text_export(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'synthetic';p.write_bytes(b'SECRET_SYNTHETIC'+b'\x00'*10000)
            r=sample(p,p.stat().st_size,10000,100)
            self.assertEqual(r['total_bytes_read'],500)
            self.assertTrue(all(s['all_nul'] for s in r['samples']))
            self.assertNotIn('SECRET',str(r))
    def test_size_change_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'synthetic';p.write_bytes(b'ABC')
            with self.assertRaises(ValueError):sample(p,4,2,1)
    def test_mixed_bytes_and_tiny_tail_not_oversampled(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'synthetic';p.write_bytes(b'A\x00\t\n\r\xff')
            r=sample(p,6,6,100)
            self.assertEqual(r['total_bytes_read'],6)
            s=r['samples'][0]
            for key in ('nul_bytes','tab_bytes','lf_bytes','cr_bytes','high_bytes','printable_ascii_bytes'):
                self.assertEqual(s[key],1)

if __name__=='__main__':unittest.main()
