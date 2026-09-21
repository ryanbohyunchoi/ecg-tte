import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_psm_source_headers as P

class PSMHeadersTests(unittest.TestCase):
    def test_explicit_selection_no_duplicate_or_medication_rescan(self):
        self.assertEqual(len(P.FILES),20)
        self.assertEqual(len(set(P.FILES)),20)
        self.assertTrue(all('Meds' not in p and 'Enc_DX' not in p for p in P.FILES))
        self.assertIn('Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_4.txt',P.FILES)
        self.assertIn('Data-2025-04-03/CarDS_2435227_Patients.txt',P.FILES)

    def test_group_schemas_preserve_missing_candidates(self):
        a=dict(status='header_candidate',schema_sha256='hash',delimiter='tab',columns=['PAT_MRN_ID','VALUE'],file_bytes=10)
        r=P.compact(dict(status='incomplete',root_check='available',files=[
            dict(a,relative_path='a.txt'),dict(a,relative_path='b.txt'),
            dict(relative_path='missing.txt',status='unavailable',reason='file_missing')]))
        self.assertEqual(len(r['schema_groups']),1)
        self.assertEqual(len(r['schema_groups'][0]['files']),2)
        self.assertEqual(r['unavailable'][0]['relative_path'],'missing.txt')
        self.assertFalse(r['data_rows_parsed'])

if __name__=='__main__':unittest.main()
