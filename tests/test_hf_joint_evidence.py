import json
from pathlib import Path
import sqlite3
import sys
import unittest
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import hf_joint_evidence as J
import audit_hf_sources as A

class JointTests(unittest.TestCase):
    def test_cached_code_evidence_preserves_results(self):
        J.clear_cache()
        for value in ['I50.22','I50.4,I10','NULL','I50.22,garbage','x'*129]:
            for _ in range(2): self.assertEqual(J.evidence(value),J._evidence(value))
        self.assertEqual(J._cached_evidence.cache_info().currsize,4)
        self.assertEqual(J._cached_evidence.cache_info().maxsize,16384)
        J.clear_cache()

    def test_codes_no_free_text_or_partial_cell_acceptance(self):
        for cell,result in [('I50.22',(True,True)),('I5043; I10',(True,True)),
            ('I50.32',(True,False)),('I50.9',(True,False)),('I50.999',(False,False)),
            ('428.0',(False,False)),('history I50.22',(False,False)),
            ('I50.22,garbage',(False,False)),('I50.22,',(False,False))]:
            self.assertEqual(J.evidence(cell),result)

    def test_latest_day_window_missingness_and_disagreement(self):
        self.assertEqual(J.echo_state([], '2024-01-02',365),'no_prior_echo')
        self.assertEqual(J.echo_state([('2024-01-01','null')],'2024-01-02',1),'recent_null')
        self.assertEqual(J.echo_state([('2023-12-31','gt_1_le_35')],'2024-01-02',1),'prior_echo_outside_window')
        self.assertEqual(J.echo_state([('2024-01-01','null'),('2024-01-01','gt_1_le_35')],'2024-01-02',1),'recent_latest_day_band_disagreement')
        with self.assertRaises(ValueError): J.echo_state([('2024-01-02','null')],'2024-01-02',365)

    def test_joint_counts_dedup_date_views_and_no_postindex_leakage(self):
        db=sqlite3.connect(':memory:');self.addCleanup(db.close);A.init_db(db);J.init(db)
        db.executemany('INSERT INTO meds VALUES (?,?,?)',[('arm','SECRET_A','2024-01-02'),('arm','SECRET_B','2024-01-02')])
        db.execute('INSERT INTO latest_echo VALUES (?,?,?,?)',('arm','SECRET_A','2024-01-01','gt_1_le_35'))
        for _ in range(2): J.add(db,'SECRET_A','I50.22',{'DX_DATE':None,'CALC_DX_DATE':date(2024,1,1)})
        J.add(db,'SECRET_B','I50.22',{'DX_DATE':date(2024,1,2),'CALC_DX_DATE':date(2024,1,3)})
        r=J.report(db,['arm'],365); arm=r['by_arm']['arm']
        self.assertEqual(sum(x['patient_keys'] for x in arm['DX_DATE']),2)
        self.assertTrue(all(x['diagnosis_evidence']=='no_preindex_code_found' for x in arm['DX_DATE']))
        self.assertEqual(sum(x['patient_keys'] for x in arm['CALC_DX_DATE'] if x['diagnosis_evidence']=='systolic_code_before'),1)
        self.assertEqual(arm['diagnosis_timing_flags']['CALC_DX_DATE']['systolic_before'],1)
        self.assertNotIn('SECRET',json.dumps(r));self.assertNotIn('2024-01',json.dumps(r))
        self.assertIsNone(r['eligible_patients'])

if __name__=='__main__':unittest.main()
