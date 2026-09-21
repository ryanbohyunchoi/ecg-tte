from datetime import date
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_comet_clinical_baseline as A
import build_shared_tables as B

class ClinicalAuditTests(unittest.TestCase):
    def test_dob_conflict_and_age_boundary(self):
        self.assertEqual(A.age_state({date(2006,2,1)},date(2024,1,31)),('under18',17))
        self.assertEqual(A.age_state({date(2006,2,1)},date(2024,2,1)),('adult_numeric',18))
        self.assertEqual(A.age_state({None,date(1980,1,1)},date(2024,1,1)),('dob_conflict',None))
        self.assertEqual(A.age_state(set(),date(2024,1,1)),('no_demographic_match',None))
    def test_shapes_not_values_or_units(self):
        self.assertEqual(A.value_shape('120/80'),'slash_pair_unvalidated')
        self.assertEqual(A.value_shape('70'),'numeric_unvalidated')
        self.assertEqual(A.value_shape('NULL'),'missing_marker')
        self.assertEqual(A.value_shape('text'),'other_unparsed')
    def fixture(self,root):
        raw=root/'raw';raw.mkdir();snapshot=root/'clinical-sources-v1-test'/'snapshot';specs=[]
        tables={
          'test_patients':(pa.table({'PAT_MRN_ID':['A','B','B'],'BIRTH_DATE':['1980-01-01','1981-01-01','1982-01-01'],'SEX_C':['1','2','2'],'SEX':['synthetic1','synthetic2','synthetic2']}),['BIRTH_DATE']),
          'test_hosp_enc':(pa.table({'PAT_MRN_ID':['A','A','A'],'PAT_ENC_CSN_ID':['X','X','F'],'HOSP_ADMSN_DATE':['2023-12-01','2023-12-01','2024-01-01'],'ED_YN':['Y']*3,'INP_YN':['N']*3}),['HOSP_ADMSN_DATE']),
          'test_outpatient_enc':(pa.table({'PAT_MRN_ID':['A','B'],'PAT_ENC_CSN_ID':['X','X'],'CONTACT_DATE':['2023-12-02','2023-12-02']}),['CONTACT_DATE']),
          'test_vitals':(pa.table({'PAT_MRN_ID':['A','A','A'],'RECORDED_TIME':['2023-12-01','2024-01-01','2024-01-02'],'FLO_MEAS_ID':['1']*3,'FLO_MEAS_NAME':['syntheticbp']*3,'DISP_NAME':['syntheticbp']*3,'MEAS_VALUE':['120/80']*3,'UNIT':['NULL']*3}),['RECORDED_TIME'])}
        for name,(t,dates) in tables.items():
            path=raw/(name+'.parquet');pq.write_table(t,path)
            specs.append(dict(id=name,path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=t.num_rows,key='PAT_MRN_ID',dates=dates,terminal_empty=False))
        with contextlib.redirect_stdout(io.StringIO()):B.build(specs,snapshot)
        report=root/'report';report.mkdir();p=report/'restricted_broad_candidates.parquet'
        pq.write_table(pa.table({'patient_key':['A','B'],'candidate_arm':['carvedilol_candidate','metoprolol_tartrate_candidate'],'candidate_order_day':[date(2024,1,1)]*2}),p)
        (report/'summary.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=2,core_snapshot=str(snapshot))))
        (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',rows=2,core_manifest_sha256=B.digest(snapshot/'manifest.json'),output_sha256=B.digest(p))))
        return report,snapshot,set(tables)
    def test_integration_temporal_overlap_conflicts_and_preserved_roster(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report,snapshot,ids=self.fixture(root);before=B.digest(report/'restricted_broad_candidates.parquet')
            with patch.object(A,'IDS',ids),contextlib.redirect_stdout(io.StringIO()) as logs:
                self.assertEqual(A.discover(root),snapshot)
                r=A.run(report,snapshot,root/'out')
            self.assertTrue(r['counts_valid']);self.assertEqual(before,B.digest(report/'restricted_broad_candidates.parquet'))
            self.assertEqual(sum(g['patient_keys'] for g in r['demographic_groups']),2)
            self.assertEqual(r['encounter_key_overlap'],dict(patient_csn_in_multiple_sources=1,patient_csn_with_multiple_dates=1,csn_with_multiple_patient_keys=1))
            c=json.loads((root/'out'/'restricted_mapping_catalog.json').read_text())
            self.assertEqual(len(c['vitals']),1);self.assertEqual(c['vitals'][0]['rows'],1)
            self.assertNotIn('120/80',(root/'out'/'restricted_mapping_catalog.json').read_text())
            self.assertNotIn('synthetic',logs.getvalue())
            private=pq.read_table(root/'out'/'restricted_demographic_qc.parquet').to_pylist()
            self.assertEqual(private[0]['age_candidate'],44);self.assertEqual(private[1]['age_status'],'dob_conflict')
            with patch.object(A,'IDS',ids),self.assertRaises(FileExistsError):A.run(report,snapshot,root/'out')
    def test_failed_or_wrong_snapshot_not_discovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report,snapshot,ids=self.fixture(root)
            with self.assertRaises(B.BuildError):A.discover(root)
            p=snapshot/'manifest.json';m=json.loads(p.read_text());m['status']='failed';p.write_text(json.dumps(m))
            with patch.object(A,'IDS',ids),self.assertRaises(B.BuildError):A.discover(root)

if __name__=='__main__':unittest.main()
