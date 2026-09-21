import contextlib
from datetime import date
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
import build_shared_tables as B
import build_comet_candidates as C


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.raw=self.base/'raw'; self.raw.mkdir()
        self.snapshot=self.base/'shared'/'core'/'snapshot'; self.out=self.base/'audit'
        meds=[]
        def med(patient,day,name,cls='Normal'):
            meds.append(dict(PAT_MRN_ID=patient,ORDER_INST=day,MEDICATION_NAME=name,
                GENERIC_NAME='',SIMPLE_GENERIC='',ORDERING_MODE='Outpatient',ORDER_CLASS=cls))
        med('A','2024-02-01','carvedilol')
        med('A','2024-03-01','metoprolol tartrate') # later switch does not exclude A
        med('A','2024-01-01','metoprolol succinate','Historical')
        med('B','2024-02-01','carvedilol')
        med('B','2024-02-01','metoprolol tartrate') # tied arms retained unresolved
        med('C','2024-02-01','metoprolol tartrate')
        med('C','NULL','metoprolol','Historical')
        med('D','2024-02-01','carvedilol')
        med('E','2024-02-01','metoprolol succinate') # never tartrate candidate
        echo=pa.table({'MRN':['A','A','C','C','D','D'],
            'EchoDate':['2023-12-01','2024-01-01','2024-02-01','2024-03-01','2023-12-01','2024-01-01'],
            'EF':pa.array([30.,40.,30.,20.,30.,None],type=pa.float64())})
        dx=pa.table({'PAT_MRN_ID':['A','B','D'], 'DX_DATE':['2024-03-01','2024-01-01','2024-02-01'],
            'CALC_DX_DATE':['2024-01-01','2024-01-01','2024-02-01'], 'CURRENT_ICD10_LIST':['I50.22','I50.9','I50.22']})
        specs=[]
        for name,table,key,dates in [
            ('medication_orders',pa.Table.from_pylist(meds),'PAT_MRN_ID',['ORDER_INST']),
            ('hospital_diagnoses',dx,'PAT_MRN_ID',['DX_DATE','CALC_DX_DATE']),
            ('outpatient_diagnoses',dx.slice(0,0),'PAT_MRN_ID',['DX_DATE','CALC_DX_DATE']),
            ('echo_studies',echo,'MRN',['EchoDate'])]:
            path=self.raw/(name+'.parquet'); pq.write_table(table,path)
            specs.append(dict(id=name,path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in table.schema],
                expected_rows=table.num_rows,key=key,terminal_empty=False,dates=dates))
        # Use one irrelevant outpatient row: the standard dataset reader rejects zero-part tables.
        t=pa.table({'PAT_MRN_ID':['UNRELATED'],'DX_DATE':['2024-01-01'],'CALC_DX_DATE':['2024-01-01'],'CURRENT_ICD10_LIST':['Z00.0']})
        pq.write_table(t,Path(specs[2]['path'])); specs[2]['expected_rows']=1
        with contextlib.redirect_stdout(io.StringIO()): B.build(specs,self.snapshot,batch_rows=2)

    def run_candidate(self):
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture): result=C.run(self.snapshot,self.out)
        self.assertNotIn('UNRELATED',capture.getvalue())
        return result

    def test_joint_anchor_history_echo_no_fallback_and_diagnosis_views(self):
        result=self.run_candidate()
        self.assertTrue(result['counts_valid']); self.assertIsNone(result['clinically_eligible_patients'])
        self.assertEqual(result['candidate_patient_keys'],4)
        self.assertEqual(sum(result['by_arm'].values()),4)
        for view in ('DX_DATE','CALC_DX_DATE'):
            self.assertEqual(sum(g['patient_keys'] for g in result['evidence_groups'] if g['date_view']==view),4)
        rows={r['patient_key']:r for r in pq.read_table(self.out/'restricted_candidates.parquet').to_pylist()}
        self.assertEqual(rows['A']['candidate_arm'],'carvedilol_candidate')
        self.assertEqual(rows['B']['candidate_arm'],'competing_arms_same_day')
        self.assertEqual(rows['A']['prior_365d_family_order_records'],1)
        self.assertEqual(rows['C']['undated_family_order_records'],1)
        self.assertEqual(rows['A']['latest_prior_echo_state'],'gt35_le100')
        self.assertEqual(rows['D']['latest_prior_echo_state'],'missing')
        self.assertEqual(rows['C']['latest_prior_echo_state'],'no_prior_echo')
        self.assertFalse(rows['A']['DX_DATE_prior_hf_evidence'])
        self.assertTrue(rows['A']['CALC_DX_DATE_prior_hf_evidence'])
        self.assertFalse(rows['D']['DX_DATE_prior_hf_evidence'])
        self.assertEqual(rows['A']['candidate_order_source_rows'],[1])
        self.assertNotIn('patient_key"',(self.out/'summary.json').read_text())
        with self.assertRaises(FileExistsError): self.run_candidate()

    def test_discovery_ignores_building_extension_and_rejects_ambiguity(self):
        ext=self.base/'shared'/'extension'/'snapshot'; ext.mkdir(parents=True)
        (ext/'manifest.json').write_text(json.dumps(dict(status='building',stages={})))
        self.assertEqual(C.discover(self.base/'shared'),self.snapshot)
        (ext/'manifest.json').write_text((self.snapshot/'manifest.json').read_text())
        with self.assertRaises(B.BuildError): C.discover(self.base/'shared')

    def test_incomplete_core_is_rejected_without_output(self):
        path=self.snapshot/'manifest.json'; m=json.loads(path.read_text()); m['status']='building'; path.write_text(json.dumps(m))
        with self.assertRaises(B.BuildError): self.run_candidate()
        self.assertFalse(self.out.exists())

    def test_midrun_manifest_change_invalidates_and_no_final_table(self):
        original=C.records
        changed=False
        def mutate(table,columns):
            nonlocal changed
            for row in original(table,columns): yield row
            if not changed:
                with (self.snapshot/'manifest.json').open('a') as f:f.write(' ')
                changed=True
        with patch.object(C,'records',side_effect=mutate):
            with self.assertRaisesRegex(B.BuildError,'core_snapshot_changed'): self.run_candidate()
        report=json.loads((self.out/'summary.json').read_text())
        self.assertFalse(report['counts_valid']); self.assertFalse((self.out/'restricted_candidates.parquet').exists())

    def test_no_overwrite_or_snapshot_overlap(self):
        with self.assertRaises(B.BuildError): C.run(self.snapshot,self.snapshot/'audit')
        self.assertFalse((self.snapshot/'audit').exists())

    def test_ef_boundary_is_separate(self):
        self.assertEqual(C.ef_state(34.9),'gt1_lt35')
        self.assertEqual(C.ef_state(35),'eq35')
        self.assertEqual(C.ef_state(35.1),'gt35_le100')
        self.assertEqual(C.ef_state(.35),'scale_or_range_unresolved')
        self.assertEqual(C.ef_state(float('nan')),'invalid')

if __name__=='__main__':unittest.main()
