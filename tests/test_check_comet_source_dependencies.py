import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_comet_source_dependencies as S

class DependencyTests(unittest.TestCase):
    def test_inventory_does_not_promote_failed_snapshot_or_read_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);root=p/'raw';root.mkdir();shared=p/'shared';shared.mkdir();audits=p/'audits';audits.mkdir()
            d=root/S.DELIVERIES[0];d.mkdir()
            (d/'CarDS_2435227_Hosp_Enc_DX.txt').write_text('PAT_MRN_ID\tDX_DATE\nSYNTHETIC\tbad-date\n')
            (d/'CarDS_2435227_Hosp_Enc_Labs_3.txt').write_bytes(b'\x00'*100)
            (d/'data_dictionary.txt').write_text('must not read contents')
            stage=shared/'old'/'snapshot';stage.mkdir(parents=True)
            (stage/'summary.json').write_text(json.dumps({'status':'failed','tables':{'hospital_labs_1':{'rows':10}}}))
            catalog=audits/'old'/'report';catalog.mkdir(parents=True)
            (catalog/'restricted_measurement_catalog.json').write_text('not JSON: no content read')
            out=p/'out';s=S.run(root,shared,audits,out)
            self.assertEqual(s['diagnoses'][0]['status'],'header_candidate')
            self.assertEqual(s['saved_lab_stages'][0]['snapshot_status'],'failed')
            self.assertEqual(len(s['saved_measurement_catalogs']),1)
            self.assertNotIn('SYNTHETIC',(out/'summary.json').read_text())
            self.assertNotIn('must not read',(out/'summary.json').read_text())
            self.assertEqual(len(s['labs']),11)
            with self.assertRaises(FileExistsError):S.run(root,shared,audits,out)
    def test_symlink_file_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);f=p/'target';f.write_text('secret');link=p/'link';link.symlink_to(f)
            self.assertEqual(S.metadata(link)['status'],'symlink_not_followed')
            with self.assertRaises(ValueError):S.bounded_json(link)
