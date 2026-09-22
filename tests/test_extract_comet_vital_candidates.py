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
    def timed(self,raw,time='10:00',enc='E1'):
        return dict(self.obs(raw),recorded_time='2023-12-01 '+time,encounter_key=enc)
    def test_encounter_average_dedup_and_pairing(self):
        first=self.timed('120/80','09:00');last=self.timed('140/90')
        other=self.timed('200/100','08:00','E2')
        state=dict(day=date(2023,12,1),observations=[first,first,last,other])
        self.assertEqual(E.choose_timed(state,'bp'),('candidate_numeric_units_unverified',(130.,85.)))
        state['observations']=[self.timed('60','09:00'),self.timed('80')]
        self.assertEqual(E.choose_timed(state,'pulse')[1],(70.,))
    def test_bmi_latest_and_exact_timestamp_conflict(self):
        state=dict(day=date(2023,12,1),observations=[self.timed('20','09:00'),self.timed('21')])
        self.assertEqual(E.choose_timed(state,'bmi')[1],(21.,))
        state['observations'].append(self.timed('22'))
        self.assertEqual(E.choose_timed(state,'bmi')[0],'latest_timestamp_disagreement')
    def test_time_and_encounter_ambiguity_block(self):
        state=dict(day=date(2023,12,1),observations=[self.timed('120/80',enc=None)])
        self.assertEqual(E.choose_timed(state,'bp')[0],'latest_encounter_unresolved')
        state['observations']=[self.timed('120/80',enc='E1'),self.timed('130/90',enc='E2')]
        self.assertEqual(E.choose_timed(state,'bp')[0],'latest_encounter_unresolved')
        state['observations']=[dict(self.timed('120/80'),recorded_time='2023-12-01')]
        self.assertEqual(E.choose_timed(state,'bp')[0],'latest_day_time_unresolved')
    def test_integration_schema_statuses_and_no_future(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();src=raw/'v.parquet';snapshot=root/'snapshot'
            t=pa.table({'PAT_MRN_ID':['A','A','A','B'], 'RECORDED_TIME':['2023-12-01 09:00','2024-01-01 09:00','2024-01-02 09:00','2023-12-01 09:00'],
                'PAT_ENC_CSN_ID':['E1','E2','E3','E4'],'FLO_MEAS_ID':['5','5','5','8'],'FLO_MEAS_NAME':['BLOOD PRESSURE']*3+['PULSE'],
                'DISP_NAME':['BP']*3+['Pulse'],'MEAS_VALUE':['120/80','999/999','888/888','70'],'UNIT':['NULL']*4})
            older=t.slice(0,1).to_pylist()[0];older.update(RECORDED_TIME='2023-03-01 09:00',MEAS_VALUE='110/70',PAT_ENC_CSN_ID='OLD')
            t=pa.concat_tables([t,pa.Table.from_pylist([older],schema=t.schema)])
            pq.write_table(t,src)
            spec=dict(id='test_vitals',path=str(src),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=5,key='PAT_MRN_ID',dates=['RECORDED_TIME'],terminal_empty=False)
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
            self.assertEqual(len(lineage['records']),3)
            self.assertEqual(r[0]['bp_older_first_candidate'],110.)
            self.assertEqual(sum(g['patient_keys'] for g in s['older_auxiliary_counts'] if g['feature']=='bp'),2)
            self.assertNotIn('120/80',(root/'out'/'summary.json').read_text())
            with patch.object(E,'IDS',{'test_vitals'}),self.assertRaises(FileExistsError):E.run(report,snapshot,root/'out')

if __name__=='__main__':unittest.main()
