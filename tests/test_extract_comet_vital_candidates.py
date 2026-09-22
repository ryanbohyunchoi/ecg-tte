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
import extract_comet_vital_candidates as E
import build_shared_tables as B

class VitalTests(unittest.TestCase):
    def obs(self,raw='120/80',unit='NULL',labels=True):
        return dict(raw=raw,unit=unit,labels_match=labels,source='test',source_row=1,component='5')
    def test_pair_preserved_not_reversed_or_normalized(self):
        self.assertEqual(E.parse_candidate('120 / 80',True),('numeric_raw_scale',(120.,80.)))
        self.assertEqual(E.parse_candidate('0',False),('numeric_raw_scale',(0.,)))
        self.assertEqual(E.parse_candidate('<70',False),('unparsed_value',None))
    def test_latest_unusable_does_not_fallback(self):
        s={};E.add_latest(s,date(2024,1,1),self.obs());E.add_latest(s,date(2024,1,2),self.obs('NULL'))
        self.assertEqual(E.choose(s,True),('latest_value_unusable',None))
    def test_tie_disagreement_and_signature_changes(self):
        s={};E.add_latest(s,date(2024,1,1),self.obs());E.add_latest(s,date(2024,1,1),self.obs('130/80'))
        self.assertEqual(E.choose(s,True)[0],'latest_day_disagreement')
        for obs in [self.obs(unit='mmHg'),self.obs(labels=False)]:
            self.assertEqual(E.choose(dict(observations=[obs]),True)[0],'mapping_signature_changed')
        s={};E.add_latest(s,None,self.obs());self.assertEqual(E.choose(s,True)[0],'unresolved_undated_record')
    def test_integration_schema_statuses_and_no_future(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();src=raw/'v.parquet';snapshot=root/'snapshot'
            t=pa.table({'PAT_MRN_ID':['A','A','A','B'], 'RECORDED_TIME':['2023-12-01','2024-01-01','2024-01-02','2023-12-01'],
                'FLO_MEAS_ID':['5','5','5','8'],'FLO_MEAS_NAME':['BLOOD PRESSURE']*3+['PULSE'],
                'DISP_NAME':['BP']*3+['Pulse'],'MEAS_VALUE':['120/80','999/999','888/888','70'],'UNIT':['NULL']*4})
            pq.write_table(t,src)
            spec=dict(id='test_vitals',path=str(src),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=4,key='PAT_MRN_ID',dates=['RECORDED_TIME'],terminal_empty=False)
            with contextlib.redirect_stdout(io.StringIO()):B.build([spec],snapshot)
            report=root/'report';report.mkdir();cp=report/'restricted_broad_candidates.parquet'
            pq.write_table(pa.table({'patient_key':['A','B'],'candidate_arm':['carvedilol_candidate','metoprolol_tartrate_candidate'],'candidate_order_day':[date(2024,1,1)]*2}),cp)
            (report/'summary.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=2,core_snapshot=str(snapshot))))
            (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_broad_exploratory_v2',rows=2,core_manifest_sha256=B.digest(snapshot/'manifest.json'),output_sha256=B.digest(cp))))
            before=B.digest(cp)
            with patch.object(E,'IDS',{'test_vitals'}),contextlib.redirect_stdout(io.StringIO()):s=E.run(report,snapshot,root/'out')
            self.assertTrue(s['counts_valid']);self.assertFalse(s['ready_for_mice']);self.assertEqual(before,B.digest(cp))
            r=pq.read_table(root/'out'/'restricted_vital_candidates.parquet').to_pylist()
            self.assertEqual(r[0]['bp_first_candidate'],120.);self.assertEqual(r[1]['pulse_candidate'],70.)
            self.assertIsNone(r[0]['bmi_candidate'])
            self.assertEqual(sum(g['patient_keys'] for g in s['joint_status_counts']),2)
            for feature in ('bp','pulse','bmi'):self.assertEqual(sum(g['patient_keys'] for g in s['feature_status_counts'] if g['feature']==feature),2)
            lineage=json.loads((root/'out'/'restricted_lineage.json').read_text())
            self.assertEqual(len(lineage['records']),2)
            self.assertNotIn('120/80',(root/'out'/'summary.json').read_text())
            with patch.object(E,'IDS',{'test_vitals'}),self.assertRaises(FileExistsError):E.run(report,snapshot,root/'out')

if __name__=='__main__':unittest.main()
