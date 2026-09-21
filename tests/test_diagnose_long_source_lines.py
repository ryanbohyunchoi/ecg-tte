import hashlib
import io
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_long_source_lines import scan


class LongLineTests(unittest.TestCase):
    def test_long_record_across_chunks_no_payload_export(self):
        content=b'A\t'+b'SECRET_SYNTHETIC'*100+b'\tZ\n'
        r=scan(io.BytesIO(content),3,record_limit=100,chunk_bytes=17)
        self.assertEqual(r['counts']['physical_lines'],1)
        self.assertEqual(r['counts']['over_record_limit'],1)
        self.assertEqual(r['counts']['matching_width'],1)
        self.assertEqual(r['max_raw_record_bytes'],len(content))
        self.assertEqual(r['max_payload_bytes'],len(content)-1)
        self.assertEqual(r['data_bytes_sha256'],hashlib.sha256(content).hexdigest())
        self.assertNotIn('SECRET',str(r))

    def test_crlf_boundary_empty_terminal_and_exact_limit(self):
        raw=b'A\tB\r\n\r\n'
        r=scan(io.BytesIO(raw),2,record_limit=5,chunk_bytes=4)
        self.assertEqual(r['counts']['physical_lines'],2)
        self.assertEqual(r['counts']['over_record_limit'],0)
        self.assertEqual(r['counts']['exact_empty_lines'],1)
        self.assertEqual(r['last_line']['payload_bytes'],0)
        self.assertTrue(r['anomaly_samples'][0]['is_final_physical_line'])

    def test_unterminated_last_record_and_width_errors(self):
        r=scan(io.BytesIO(b'A\tB\nX\nA\tB\tC'),2,chunk_bytes=2)
        self.assertEqual(r['counts']['physical_lines'],3)
        self.assertEqual(r['counts']['matching_width'],1)
        self.assertEqual(r['counts']['too_few_columns'],1)
        self.assertEqual(r['counts']['too_many_columns'],1)
        self.assertEqual(r['counts']['unterminated_lines'],1)
        self.assertEqual(r['last_line']['payload_bytes'],5)

    def test_empty_file_nul_and_capped_samples(self):
        self.assertEqual(scan(io.BytesIO(b''),2)['last_line'],None)
        r=scan(io.BytesIO(b'\x00\n'*25),2,chunk_bytes=1)
        self.assertEqual(r['counts']['lines_with_nul'],25)
        self.assertEqual(len(r['anomaly_samples']),20)
        self.assertEqual(r['counts']['anomaly_samples_omitted'],5)
        self.assertTrue(all(not s['is_final_physical_line'] for s in r['anomaly_samples']))

    def test_chunk_size_invariance_including_crlf_and_blank_lines(self):
        raw=b'\nA\tB\r\nC\t'+b'X'*77+b'\nD\tE'
        expected=scan(io.BytesIO(raw),2,record_limit=50,chunk_bytes=10000)
        for size in (1,2,3,4,7,17):
            self.assertEqual(scan(io.BytesIO(raw),2,record_limit=50,chunk_bytes=size),expected)

if __name__=='__main__':unittest.main()
