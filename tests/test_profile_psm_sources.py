import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import profile_psm_sources as P

class PSMProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'source';self.root.mkdir();self.path=self.root/'labs.txt'
    def source(self,body):
        self.path.write_text('PAT_MRN_ID\tRESULT_DATE\tORD_VALUE\tORD_NUM_VALUE\tCOMPONENT_ID\tCOMPONENT_NAME\n'+body)
        return P.inspect(self.root,'labs.txt')['schema_sha256']
    def test_bounded_qc_and_private_catalog(self):
        schema=self.source('SECRET_PAT\t2024-01-01\t<5\tNULL\tX\tSECRET_CATALOG\nOTHER\tbad\t2\t2\tY\tOther\n')
        before=self.path.read_bytes()
        r,c=P.profile(self.root,'labs.txt','labs_2026',schema,1)
        self.assertEqual(r['status'],'bounded_prefix');self.assertFalse(r['reached_eof'])
        self.assertEqual(r['numeric_formats']['ORD_VALUE'],{'qualified_number_no_conversion':1})
        self.assertEqual(r['unit_fields_present'],[])
        self.assertNotIn('SECRET',json.dumps(r));self.assertNotIn('SECRET_PAT',json.dumps(c))
        self.assertIn('SECRET_CATALOG',json.dumps(c));self.assertEqual(self.path.read_bytes(),before)
    def test_width_failure_no_partial_catalog(self):
        schema=self.source('SECRET_BAD\n')
        r,c=P.profile(self.root,'labs.txt','labs_2026',schema,10)
        self.assertFalse(r['counts_valid']);self.assertIsNone(c)
        self.assertEqual(r['reason'],'row_width_mismatch');self.assertNotIn('SECRET',json.dumps(r))
    def test_schema_pin_and_catalog_omissions(self):
        schema=self.source('A\t2024-01-01\t1\t1\tX\tx\nB\t2024-01-01\t1\t1\tY\ty\n')
        r,c=P.profile(self.root,'labs.txt','labs_2026','wrong',10)
        self.assertEqual(r['reason'],'schema_hash_mismatch')
        r,c=P.profile(self.root,'labs.txt','labs_2026',schema,10,catalog_limit=1)
        self.assertEqual(r['status'],'complete_file');self.assertEqual(r['rows_read'],2)
        self.assertEqual(r['catalog_records_omitted'],1)
    def test_selection_and_output_reuse(self):
        self.assertEqual(len(P.sources()),19)
        self.assertTrue(all('Data-2026-04-15/CarDS_2435227_Patients.txt'!=x[0] for x in P.sources()))
        schema=self.source('A\t2024-01-01\t1\t1\tX\tx\n')
        out=self.root.parent/'report'
        r=P.run(self.root,out,1,[('labs.txt','labs_2026',schema)])
        self.assertEqual(r['status'],'complete_requested_scope')
        with self.assertRaises(FileExistsError):P.run(self.root,out,1,[])
        with self.assertRaises(ValueError):P.run(self.root,self.root/'bad',1,[])

if __name__=='__main__':unittest.main()
